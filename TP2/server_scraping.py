#!/usr/bin/env python3
import argparse
import asyncio
import logging
import datetime
import struct
import json
import aiohttp
from aiohttp import web, ClientSession

# Importaciones de módulos locales
from common.protocol import pack_message, HEADER_SIZE
from common.serialization import deserialize_data
from scraper.async_http import fetch_url
from scraper.html_parser import scrape_html_content
from scraper.metadata_extractor import extract_meta_tags

# Configuración de Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [Servidor A] [%(levelname)s] %(message)s')
log = logging.getLogger(__name__)

# Timeout para la comunicación con Servidor B
PROCESSOR_TIMEOUT = 130 # Debe ser mayor que el JOB_TIMEOUT_SECONDS de B

# --- 3. Comunicación Asíncrona con Servidor B ---

async def talk_with_processor(job: dict, host: str, port: int) -> dict:
    """
    Envía un trabajo al Servidor B (procesamiento) y espera su respuesta.
    Utiliza sockets asíncronos (asyncio streams).
    """
    reader = writer = None
    try:
        # 1. Conectar asíncronamente
        log.info(f"Conectando al Servidor B en {host}:{port}...")
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=10 # Timeout de conexión
        )

        # 2. Enviar mensaje (Header + Payload)
        msg = pack_message(job)
        writer.write(msg)
        await writer.drain()
        log.info(f"Trabajo enviado a Servidor B para: {job.get('url')}")

        # 3. Leer respuesta (Header)
        header_bytes = await asyncio.wait_for(
            reader.readexactly(HEADER_SIZE), 
            timeout=PROCESSOR_TIMEOUT
        )
        (length,) = struct.unpack('!I', header_bytes) # Big-Endian

        # 4. Leer respuesta (Payload)
        body_bytes = await asyncio.wait_for(
            reader.readexactly(length), 
            timeout=PROCESSOR_TIMEOUT
        )
        
        resp = deserialize_data(body_bytes)
        log.info(f"Respuesta recibida de Servidor B para: {job.get('url')}")
        return resp

    except asyncio.TimeoutError:
        msg = f"Timeout ({PROCESSOR_TIMEOUT}s) esperando respuesta del Servidor B"
        log.error(msg)
        return {"status": "error", "error": msg}
    except ConnectionRefusedError:
        msg = f"Conexión rechazada por Servidor B en {host}:{port}"
        log.error(msg)
        return {"status": "error", "error": msg}
    except Exception as e:
        msg = f"Error hablando con Servidor B: {e}"
        log.error(msg, exc_info=True)
        return {"status": "error", "error": msg}
    finally:
        if writer:
            writer.close()
            await writer.wait_closed()

# --- 4. Handler HTTP /scrape ---

async def handle_scrape(request: web.Request):
    url = request.query.get("url")
    if not url:
        return web.json_response(
            {"status": "error", "message": 'Missing "url" query parameter'},
            status=400,
        )

    # Añadir esquema si falta
    if not url.startswith(('http://', 'https://')):
        url = f"http://{url}"

    proc_host = request.app["processor_ip"]
    proc_port = request.app["processor_port"]
    session = request.app["client_session"]

    log.info(f"Procesando URL: {url}")
    
    scraping_data = {}
    content_data = {}
    
    # --- A. Scraping Asíncrono (I/O-Bound) ---
    try:
        html_content = await fetch_url(session, url)
        
        # Parseo (CPU-light, se hace en el event loop)
        content_data = scrape_html_content(html_content, base_url=url)
        meta_data = extract_meta_tags(html_content)

        # Preparamos la parte 'scraping_data' de la respuesta
        scraping_data = {
            "title": content_data["title"],
            "links": content_data["links"],
            "meta_tags": meta_data,
            "structure": content_data["structure"],
            "images_count": content_data["images_count"],
        }
        
    except asyncio.TimeoutError:
        log.warning(f"Scraping timed out para: {url}")
        return web.json_response(
            {"status": "error", "message": "Scraping timed out (30s)"},
            status=504, # Gateway Timeout
        )
    except ConnectionError as e:
        log.error(f"Error de conexión en scraping: {e}")
        return web.json_response(
            {"status": "error", "message": str(e)},
            status=502, # Bad Gateway
        )
    except Exception as e:
        log.exception("Error no manejado en scraping")
        return web.json_response(
            {"status": "error", "message": f"Scraping failed: {e}"},
            status=500,
        )

    # --- B. Envío a Servidor B (I/O-Bound socket) ---
    job = {
        "url": url,
        "image_urls": content_data.get("image_urls", []),
    }

    # Esta llamada es asíncrona (await)
    proc_resp = await talk_with_processor(job, proc_host, proc_port)

    # Interpretar respuesta del Servidor B
    if not isinstance(proc_resp, dict):
        processing_data = {"error": "Invalid response from processing server"}
        final_status = "partial_success"
    elif proc_resp.get("status") == "error" or proc_resp.get("error"):
        log.warning(f"Error recibido del Servidor B: {proc_resp.get('error')}")
        processing_data = proc_resp
        final_status = "partial_success"
    else: 
        processing_data = proc_resp
        final_status = "success"

    # --- C. Consolidación de Respuesta (Transparencia) ---
    response = {
        "url": url,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "scraping_data": scraping_data,
        "processing_data": processing_data,
        "status": final_status,
    }

    log.info(f"Finalizado {url} con estado: {final_status}")
    return web.json_response(response, dumps=lambda x: json.dumps(x, indent=4))

# --- 5. Inicialización y CLI ---

async def on_startup(app):
    """Crea la sesión de aiohttp."""
    app['client_session'] = aiohttp.ClientSession()
    log.info("Sesión de cliente aiohttp creada.")

async def on_cleanup(app):
    """Cierra la sesión de aiohttp."""
    await app['client_session'].close()
    log.info("Sesión de cliente aiohttp cerrada.")

def main():
    parser = argparse.ArgumentParser(
        description="Servidor de Scraping Web Asíncrono (Parte A)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("-i", "--ip", required=True, help="Dirección de escucha (soporta IPv4/IPv6)")
    parser.add_argument("-p", "--port", required=True, type=int, help="Puerto de escucha")
    parser.add_argument("-w", "--workers", type=int, default=4, help="Número de workers (default: 4)")
    
    # Argumentos para conectar con Servidor B
    parser.add_argument("--processor-ip", default="127.0.0.1", help="IP del Servidor B")
    parser.add_argument("--processor-port", type=int, default=8001, help="Puerto del Servidor B")

    args = parser.parse_args()

    app = web.Application()
    
    # Guardamos la config de B en la app para el handler
    app["processor_ip"] = args.processor_ip
    app["processor_port"] = args.processor_port
    
    # Rutas y ciclo de vida
    app.router.add_get("/scrape", handle_scrape)
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)

    log.info(f"Servidor A (Scraping) escuchando en {args.ip}:{args.port} (workers: {args.workers})")
    log.info(f"Usando Servidor B (Procesamiento) en {args.processor_ip}:{args.processor_port}")

    # web.run_app maneja el event loop y soporta IPv4/v6 en 'host'
    web.run_app(
        app, 
        host=args.ip, 
        port=args.port,
        # 'workers' solo funciona en producción, no con auto-reload
        # workers=args.workers 
    )

if __name__ == "__main__":
    main()