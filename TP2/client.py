#!/usr/bin/env python3
import asyncio
import aiohttp
import argparse
import json
import sys

# Valores por defecto del cliente
DEFAULT_URL = "https://www.example.com"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8080
DEFAULT_TIMEOUT = 150 # Timeout alto para esperar al Servidor B


def build_endpoint(host: str, port: int) -> str:
    """
    Construye el endpoint HTTP para /scrape.
    Si el host es una dirección IPv6 literal, se envuelve entre corchetes.
    """
    if ":" in host and not host.startswith("["):
        return f"http://[{host}]:{port}/scrape"
    return f"http://{host}:{port}/scrape"


async def solicitar_scrape(url: str, host: str, port: int, timeout: int):

    endpoint = build_endpoint(host, port)
    params = {"url": url} # Petición GET con query params

    print("\n=== Cliente de Prueba - Scraping Distribuido ===")
    print(f"- Destino a scrapear : {url}")
    print(f"- Servidor A objetivo: {host}:{port}")
    print(f"- Endpoint           : {endpoint}")
    print(f"- Timeout máximo     : {timeout} s\n")

    timeout_cfg = aiohttp.ClientTimeout(total=timeout)

    try:
        async with aiohttp.ClientSession(timeout=timeout_cfg) as session:
            print("[INFO] Solicitando al Servidor A...")
            async with session.get(endpoint, params=params) as resp:
                print(f"[INFO] HTTP recibido: {resp.status} {resp.reason}")

                # Intentar interpretar como JSON
                try:
                    data = await resp.json()
                except Exception:
                    text = await resp.text()
                    print("\n[ERROR] La respuesta no es JSON válido.")
                    print("Contenido recibido (parcial):")
                    print(text[:1000])
                    return

                # Análisis básico del contenido
                status_global = data.get("status", "desconocido")
                scraping = data.get("scraping_data", {})
                processing = data.get("processing_data", {})
                titulo = scraping.get("title", "N/D")

                print("\n--- Resumen de la respuesta ---")
                print(f"Estado reportado : {status_global}")
                print(f"Título detectado : {titulo}")

                # Verificación de datos de procesamiento
                if processing.get("error"):
                    print(f"Error Procesamiento: {processing['error']}")
                elif processing.get("screenshot"):
                    print(f"Screenshot       : Recibido ({len(processing['screenshot'])} bytes)")
                else:
                    print("Screenshot       : No recibido")

                print("\n--- JSON completo ---")
                print(json.dumps(data, indent=4, ensure_ascii=False))

    except aiohttp.ClientConnectorError:
        print(f"\n[ERROR] No se pudo conectar con {host}:{port}. ¿El servidor A está en ejecución?")
    except asyncio.TimeoutError:
        print(f"\n[ERROR] Se alcanzó el timeout de {timeout} segundos esperando la respuesta del Servidor A.")
    except KeyboardInterrupt:
        print("\n[INFO] Cliente interrumpido.")
    except Exception as e:
        print(f"\n[ERROR] Error inesperado en el cliente: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Cliente de prueba para el sistema de Scraping Distribuido."
    )
    parser.add_argument(
        "url",
        nargs="?",
        default=DEFAULT_URL,
        help=f"URL a scrapear (default: {DEFAULT_URL})",
    )
    parser.add_argument(
        "--host",
        default=DEFAULT_HOST,
        help=f"Host del Servidor A (IPv4 o IPv6, default: {DEFAULT_HOST})",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"Puerto del Servidor A (default: {DEFAULT_PORT})",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help=f"Timeout total en segundos (default: {DEFAULT_TIMEOUT})",
    )

    args = parser.parse_args()
    try:
        asyncio.run(solicitar_scrape(args.url, args.host, args.port, args.timeout))
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()