Este es un excelente y completo trabajo práctico. Combina dos de los conceptos más importantes y potentes de la programación concurrente en Python: **asyncio** para operaciones de I/O (red) y **multiprocessing** para tareas que consumen CPU.

Como me indicaste, no voy a resolver el trabajo práctico por completo, pero sí puedo actuar como tu asistente y proporcionarte una guía detallada, los esqueletos de código y los patrones de diseño clave que necesitas para construirlo paso a paso.

Vamos a empezar por lo más importante: la arquitectura de los dos servidores y cómo se comunican entre ellos.

-----

## 🚀 Paso 1: Esqueleto del Servidor A (Asyncio)

Este servidor es tu "puerta de entrada". Usará `aiohttp` para manejar las peticiones HTTP del cliente de forma asíncrona. También usará `argparse` para la configuración.

Aquí tienes un esqueleto robusto para `server_scraping.py`.

```python
# TP2/server_scraping.py

import argparse
import asyncio
import aiohttp
from aiohttp import web
import json
import logging

# (Más adelante importaremos los módulos de scraping y comunicación)
# from common.protocol import request_processing_from_server_b
# from scraper.html_parser import scrape_page_data

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

async def handle_scrape(request):
    """
    Manejador principal para la ruta /scrape.
    """
    url = request.query.get('url')
    if not url:
        return web.json_response(
            {"status": "error", "message": "Falta el parámetro 'url'"},
            status=400
        )

    log.info(f"Recibida solicitud de scraping para: {url}")

    try:
        # --- 1. SCRAPING (PARTE A) ---
        # (Aquí llamaremos a nuestra función de scraping asíncrona)
        # scraping_data = await scrape_page_data(request.app['http_session'], url)
        
        # --- Mockup temporal ---
        await asyncio.sleep(0.5) # Simula I/O no bloqueante
        scraping_data = {
            "title": "Título de la página (Mockup)",
            "links": ["link1", "link2"],
            "meta_tags": {"description": "Mockup data"},
            "structure": {"h1": 1, "h2": 3},
            "images_count": 5
        }
        log.info(f"Scraping para {url} completado.")

        # --- 2. COMUNICACIÓN (PARTE B) ---
        # (Aquí nos comunicaremos con el Servidor B)
        # processing_data = await request_processing_from_server_b(
        #     request.app['server_b_config'], 
        #     {"url": url, "task": "full_analysis"}
        # )
        
        # --- Mockup temporal ---
        await asyncio.sleep(1.0) # Simula I/O de red con Servidor B
        processing_data = {
            "screenshot": "base64_mockup",
            "performance": {"load_time_ms": 100},
            "thumbnails": ["thumb1_mockup"]
        }
        log.info(f"Procesamiento de {url} completado.")


        # --- 3. CONSOLIDACIÓN (PARTE C) ---
        final_response = {
            "url": url,
            "timestamp": "2025-10-25T10:00:00Z", # Usar datetime.now().isoformat()
            "scraping_data": scraping_data,
            "processing_data": processing_data,
            "status": "success"
        }
        
        return web.json_response(final_response, status=200)

    except asyncio.TimeoutError:
        log.warning(f"Timeout al procesar {url}")
        return web.json_response(
            {"status": "error", "message": "Timeout durante el procesamiento"},
            status=504
        )
    except Exception as e:
        log.error(f"Error procesando {url}: {e}", exc_info=True)
        return web.json_response(
            {"status": "error", "message": str(e)},
            status=500
        )

async def setup_app(server_b_ip, server_b_port):
    """Configura e inicializa la aplicación aiohttp."""
    app = web.Application()
    
    # Cliente HTTP asíncrono para el scraping
    app['http_session'] = aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=30)
    )
    
    # Configuración del servidor B para los handlers
    app['server_b_config'] = (server_b_ip, server_b_port)
    
    app.router.add_get('/scrape', handle_scrape)
    
    async def cleanup_session(app_instance):
        log.info("Cerrando ClientSession HTTP...")
        await app_instance['http_session'].close()
        
    app.on_cleanup.append(cleanup_session)
    return app

def main():
    parser = argparse.ArgumentParser(description="Servidor de Scraping Web Asíncrono")
    parser.add_argument('-i', '--ip', required=True, help="Dirección de escucha (soporta IPv4/IPv6)")
    parser.add_argument('-p', '--port', required=True, type=int, help="Puerto de escucha")
    # Este argumento es para saber dónde está el Servidor B
    parser.add_argument('--b-ip', required=True, help="IP del servidor de procesamiento")
    parser.add_argument('--b-port', required=True, type=int, help="Puerto del servidor de procesamiento")
    # aiohttp maneja los workers internamente, este arg no es necesario para aiohttp
    
    args = parser.parse_args()

    try:
        app = setup_app(args.b_ip, args.b_port)
        log.info(f"Iniciando Servidor A en http://{args.ip}:{args.port}")
        # web.run_app escucha en todas las IPs (IPv4 e IPv6) si host es 0.0.0.0 o ::
        # Si especificas una IP, usa esa.
        web.run_app(app, host=args.ip, port=args.port)
        
    except KeyboardInterrupt:
        log.info("Servidor A detenido manualmente.")
    finally:
        log.info("Servidor A finalizado.")

if __name__ == "__main__":
    main()
```

-----

## 📦 Paso 2: Esqueleto del Servidor B (Multiprocessing)

Este servidor es tu "trabajador pesado". Recibe tareas por sockets y usa un `ProcessPoolExecutor` para ejecutar trabajo intensivo de CPU (como `selenium`) en procesos separados, sin bloquear la recepción de nuevas tareas.

Usaremos `socketserver` para manejar las conexiones TCP y `concurrent.futures.ProcessPoolExecutor` para el pool de procesos.

```python
# TP2/server_processing.py

import argparse
import socketserver
import json
import logging
from concurrent.futures import ProcessPoolExecutor
import os

# (Más adelante importaremos los módulos de procesamiento)
# from processor.screenshot import take_screenshot
# from processor.performance import analyze_performance

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# --- Funciones de Tarea (CPU-Bound) ---
# Estas funciones se ejecutarán en el ProcessPoolExecutor

def run_full_analysis(url):
    """
    Función que se ejecuta en un proceso separado.
    Debe ser una función simple, no un método de clase,
    para que sea fácilmente "picklable".
    """
    log.info(f"[PID {os.getpid()}] Iniciando análisis para: {url}")
    try:
        # 1. Generar Screenshot
        # screenshot_b64 = take_screenshot(url)
        screenshot_b64 = f"base64_screenshot_for_{url}" # Mockup
        
        # 2. Análisis de Rendimiento
        # performance_data = analyze_performance(url)
        performance_data = {"load_time_ms": 1234, "total_size_kb": 567} # Mockup
        
        # 3. Análisis de Imágenes
        thumbnails = ["thumb1_b64", "thumb2_b64"] # Mockup
        
        log.info(f"[PID {os.getpid()}] Análisis completado para: {url}")
        
        return {
            "status": "success",
            "screenshot": screenshot_b64,
            "performance": performance_data,
            "thumbnails": thumbnails
        }
    except Exception as e:
        log.error(f"[PID {os.getpid()}] Error en análisis de {url}: {e}")
        return {"status": "error", "message": str(e)}

# ----------------------------------------

class TaskHandler(socketserver.BaseRequestHandler):
    """
    Manejador para cada conexión TCP al Servidor B.
    """
    
    def handle(self):
        try:
            # --- 1. Recibir datos ---
            # Usaremos un protocolo simple: 4 bytes (longitud) + JSON
            header = self.request.recv(4)
            if not header:
                return
            
            msg_len = int.from_bytes(header, 'big')
            data = self.request.recv(msg_len)
            
            task_data = json.loads(data.decode('utf-8'))
            log.info(f"Recibida tarea: {task_data}")

            # --- 2. Enviar tarea al Pool de Procesos ---
            # self.server.process_pool es el ProcessPoolExecutor
            future = self.server.process_pool.submit(
                run_full_analysis, 
                task_data['url']
            )
            
            # Obtenemos el resultado (esto bloquea ESTE HILO, 
            # pero no el servidor principal ni otros hilos)
            result = future.result() 

            # --- 3. Enviar respuesta ---
            response_data = json.dumps(result).encode('utf-8')
            response_header = len(response_data).to_bytes(4, 'big')
            
            self.request.sendall(response_header + response_data)
            
        except Exception as e:
            log.error(f"Error en TaskHandler: {e}", exc_info=True)
            try:
                # Intentar enviar un error de vuelta
                err_msg = json.dumps({"status": "error", "message": "Error interno del servidor B"}).encode('utf-8')
                err_header = len(err_msg).to_bytes(4, 'big')
                self.request.sendall(err_header + err_msg)
            except:
                pass # La conexión ya puede estar cerrada

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """Servidor TCP que usa hilos para manejar cada conexión."""
    allow_reuse_address = True
    
    def __init__(self, server_address, RequestHandlerClass, process_pool):
        super().__init__(server_address, RequestHandlerClass)
        self.process_pool = process_pool

def main():
    parser = argparse.ArgumentParser(description="Servidor de Procesamiento Distribuido")
    parser.add_argument('-i', '--ip', required=True, help="Dirección de escucha")
    parser.add_argument('-p', '--port', required=True, type=int, help="Puerto de escucha")
    parser.add_argument('-n', '--processes', type=int, default=None, 
                        help="Número de procesos en el pool (default: CPU count)")
    
    args = parser.parse_args()
    
    num_processes = args.processes if args.processes else os.cpu_count()
    log.info(f"Iniciando ProcessPoolExecutor con {num_processes} workers...")

    # Usamos un context manager para asegurar que el pool se cierre
    with ProcessPoolExecutor(max_workers=num_processes) as pool:
        server_address = (args.ip, args.port)
        
        # Pasamos el pool al constructor de nuestro servidor
        server = ThreadedTCPServer(
            server_address, 
            TaskHandler,
            process_pool=pool
        )
        
        log.info(f"Iniciando Servidor B en {args.ip}:{args.port}")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            log.info("Servidor B detenido manualmente.")
        finally:
            log.info("Cerrando servidor B...")
            server.shutdown()
            server.server_close()

if __name__ == "__main__":
    main()
```

-----

## 🔌 Paso 3: Comunicación A \<-\> B (Asyncio \<-\> Sockets)

Esta es la parte más desafiante. El Servidor A (asyncio) **no puede** usar `socket` estándar porque es bloqueante. Debe usar `asyncio.open_connection` para hablar con el Servidor B.

Crearemos un módulo `common/protocol.py` para manejar esta comunicación.

```python
# TP2/common/protocol.py

import asyncio
import json
import logging

log = logging.getLogger(__name__)

async def request_processing_from_server_b(server_b_config, task_data):
    """
    Se conecta al Servidor B, envía una tarea y recibe una respuesta.
    Todo de forma asíncrona.
    """
    host, port = server_b_config
    try:
        log.debug(f"Conectando al Servidor B en {host}:{port}")
        # 1. Conectar de forma asíncrona
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=5.0 # Timeout de conexión
        )

        # 2. Serializar y enviar datos (con protocolo de longitud)
        data = json.dumps(task_data).encode('utf-8')
        header = len(data).to_bytes(4, 'big')
        
        writer.write(header + data)
        await writer.drain()
        log.debug(f"Datos enviados al Servidor B: {task_data}")

        # 3. Recibir respuesta (con protocolo de longitud)
        response_header = await asyncio.wait_for(reader.readexactly(4), timeout=30.0)
        if not response_header:
            raise ConnectionError("Servidor B cerró la conexión inesperadamente (header)")
            
        response_len = int.from_bytes(response_header, 'big')
        
        response_data = await asyncio.wait_for(reader.readexactly(response_len), timeout=30.0)
        if not response_data:
            raise ConnectionError("Servidor B cerró la conexión inesperadamente (data)")

        log.debug("Respuesta recibida del Servidor B")
        
        # 4. Cerrar y deserializar
        writer.close()
        await writer.wait_closed()
        
        return json.loads(response_data.decode('utf-8'))

    except asyncio.TimeoutError:
        log.error(f"Timeout en la comunicación con el Servidor B ({host}:{port})")
        raise
    except Exception as e:
        log.error(f"Error de comunicación con Servidor B: {e}")
        raise
```

**Para conectar esto:**

1.  Guarda este archivo como `TP2/common/protocol.py`.
2.  En `server_scraping.py`, descomenta la línea:
    `from common.protocol import request_processing_from_server_b`
3.  Reemplaza el "Mockup temporal" de la **COMUNICACIÓN (PARTE B)** con la llamada real:
    ```python
    processing_data = await request_processing_from_server_b(
        request.app['server_b_config'], 
        {"url": url, "task": "full_analysis"} # Enviamos la URL y la tarea
    )
    # Aquí puedes chequear processing_data['status']
    if processing_data.get('status') == 'error':
        raise Exception(f"Error en Servidor B: {processing_data.get('message')}")
    ```

-----

## 🗺️ Próximos Pasos (Tu Tarea)

Ahora tienes los cimientos de la arquitectura distribuida. Lo que sigue es "rellenar" las funciones de trabajo:

### 1\. Rellenar el Scraping (Servidor A)

Crea `TP2/scraper/html_parser.py` y `TP2/scraper/metadata_extractor.py`.

```python
# TP2/scraper/html_parser.py
from bs4 import BeautifulSoup
import logging

log = logging.getLogger(__name__)

async def fetch_html(http_session, url):
    """Usa aiohttp para descargar el HTML."""
    try:
        async with http_session.get(url) as response:
            response.raise_for_status() # Lanza error si es 4xx/5xx
            return await response.text()
    except Exception as e:
        log.error(f"Error al descargar {url}: {e}")
        raise

def parse_html_content(html_content, url):
    """Usa BeautifulSoup para extraer datos."""
    soup = BeautifulSoup(html_content, 'lxml')
    
    # Título
    title = soup.title.string if soup.title else "Sin Título"
    
    # Enlaces (usa urllib.parse.urljoin para hacerlos absolutos)
    links = []
    for a in soup.find_all('a', href=True):
        links.append(a['href']) # Aquí deberías normalizarlos
        
    # Metadatos (puedes mover esto a metadata_extractor.py)
    meta_tags = {}
    for meta in soup.find_all('meta'):
        if 'name' in meta.attrs and meta.attrs.get('content'):
            meta_tags[meta.attrs['name']] = meta.attrs['content']
        if 'property' in meta.attrs and meta.attrs.get('content'):
            meta_tags[meta.attrs['property']] = meta.attrs['content']
            
    # Estructura
    structure = {
        "h1": len(soup.find_all('h1')),
        "h2": len(soup.find_all('h2')),
        "h3": len(soup.find_all('h3')),
        "h4": len(soup.find_all('h4')),
        "h5": len(soup.find_all('h5')),
        "h6": len(soup.find_all('h6')),
    }
    
    # Imágenes
    images_count = len(soup.find_all('img'))
    
    return {
        "title": title,
        "links": links[:50], # Limita la cantidad
        "meta_tags": meta_tags,
        "structure": structure,
        "images_count": images_count
    }

async def scrape_page_data(http_session, url):
    """Función principal de scraping que llamas desde el handler."""
    html = await fetch_html(http_session, url)
    data = parse_html_content(html, url)
    return data
```

**Para conectar:** En `server_scraping.py`, importa `scrape_page_data` y reemplaza el mockup de *SCRAPING (PARTE A)*.

### 2\. Rellenar el Procesamiento (Servidor B)

Crea `TP2/processor/screenshot.py`.

```python
# TP2/processor/screenshot.py
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import base64
import logging

log = logging.getLogger(__name__)

def take_screenshot(url):
    """
    Toma un screenshot usando Selenium (¡operación CPU/I/O intensiva!)
    Esta función se ejecuta en un proceso separado.
    """
    log.info(f"Tomando screenshot de {url}...")
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1280,720")
    
    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(20) # Timeout para la carga
        driver.get(url)
        
        # Espera un poco (no es ideal, pero simple)
        driver.implicitly_wait(2) 
        
        png_data = driver.get_screenshot_as_png()
        b64_data = base64.b64encode(png_data).decode('utf-8')
        log.info(f"Screenshot de {url} completado.")
        return b64_data
        
    except Exception as e:
        log.error(f"Error al tomar screenshot de {url}: {e}")
        raise
    finally:
        if driver:
            driver.quit()
```

**Para conectar:** En `server_processing.py`, importa `take_screenshot` y reemplaza el mockup dentro de `run_full_analysis`. Haz lo mismo para `analyze_performance` (puedes usar `selenium` para obtener datos de `window.performance`) y `image_processor` (usando `Pillow`).

-----

Empieza implementando estos esqueletos. Ejecuta ambos servidores en terminales separadas y prueba a llamar al Servidor A con un cliente como `curl` o Postman:

```bash
# Terminal 1
$ python3 TP2/server_processing.py -i 127.0.0.1 -p 9000 -n 4

# Terminal 2
$ python3 TP2/server_scraping.py -i 127.0.0.1 -p 8080 --b-ip 127.0.0.1 --b-port 9000

# Terminal 3
$ curl "http://127.0.0.1:8080/scrape?url=https://www.python.org"
```
