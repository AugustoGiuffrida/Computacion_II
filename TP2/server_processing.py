#!/usr/bin/env python3
import argparse
import base64
import socketserver
import json
import logging
import os
import struct
from concurrent.futures import ProcessPoolExecutor, TimeoutError
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Importaciones de módulos locales
from common.protocol import recv_message, pack_message, HEADER_SIZE
from processor.screenshot import generate_screenshot
from processor.performance import analyze_performance
from processor.image_processor import process_images

# Configuración de Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [Servidor B] [%(levelname)s] %(message)s')
log = logging.getLogger(__name__)

# Timeout para el trabajo completo en el pool
JOB_TIMEOUT_SECONDS = 120

# --- Función de Tarea (CPU-Bound) ---
# Esta función se ejecutará en el ProcessPoolExecutor
def worker_process(job_data: dict) -> dict:
    """
    Ejecuta todas las tareas CPU-Bound para una solicitud.
    """
    url = job_data.get('url')
    image_urls = job_data.get('image_urls', [])
    
    pid = os.getpid()
    log.info(f"[PID {pid}] Iniciando análisis para: {url}")
    
    # 1. Generar Screenshot y 2. Análisis de Rendimiento (con Selenium)
    # Optimizamos reutilizando el driver para screenshot y performance
    
    screenshot_b64 = ""
    performance_data = {}
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1280,720")
    driver = None
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(30)
        
        log.info(f"[PID {pid}] Navegando a {url} (Selenium)...")
        driver.get(url)
        
        # Tarea 1: Screenshot
        log.info(f"[PID {pid}] Generando screenshot...")
        png_bytes = driver.get_screenshot_as_png()
        screenshot_b64 = base64.b64encode(png_bytes).decode('utf-8')
        
        # Tarea 2: Performance
        log.info(f"[PID {pid}] Analizando rendimiento...")
        performance_data = analyze_performance(url, driver)
        
    except Exception as e:
        log.error(f"[PID {pid}] Error en tareas de Selenium para {url}: {e}")
        performance_data = {"error": f"Selenium failed: {e}"}
    finally:
        if driver:
            driver.quit()
            
    # Tarea 3: Análisis de Imágenes (Thumbnails)
    log.info(f"[PID {pid}] Generando thumbnails...")
    try:
        thumbnails = process_images(image_urls)
    except Exception as e:
        log.error(f"[PID {pid}] Error en procesamiento de imágenes: {e}")
        thumbnails = []

    log.info(f"[PID {pid}] Análisis completado para: {url}")
    
    return {
        "screenshot": screenshot_b64,
        "performance": performance_data,
        "thumbnails": thumbnails
    }

# ----------------------------------------

class TaskHandler(socketserver.BaseRequestHandler):
    """
    Manejador para cada conexión TCP del Servidor A.
    """
    
    def handle(self):
        try:
            # --- 1. Recibir datos (usando el protocolo) ---
            log.info(f"Conexión recibida de: {self.client_address}")
            job_data = recv_message(self.request)
            log.info(f"Recibida tarea para: {job_data.get('url')}")

            start = datetime.now()
            
            # --- 2. Enviar tarea al Pool de Procesos ---
            pool = self.server.process_pool
            future = pool.submit(worker_process, job_data)
            
            # Obtenemos el resultado (esto bloquea ESTE HILO, 
            # pero no el servidor principal)
            result_data = future.result(timeout=JOB_TIMEOUT_SECONDS) 

            end = datetime.now()
            log.info(f"Trabajo completado para {job_data.get('url')} en {end-start}")

            # --- 3. Enviar respuesta ---
            response_msg = pack_message(result_data)
            self.request.sendall(response_msg)
            
        except (ConnectionError, struct.error):
            log.warning(f"Error de protocolo/conexión con {self.client_address}. Cliente desconectado.")
        except TimeoutError:
            log.error(f"Timeout en job para {job_data.get('url')} (límite: {JOB_TIMEOUT_SECONDS}s)")
            self.send_error(f"Processing job timed out after {JOB_TIMEOUT_SECONDS}s")
        except Exception as e:
            log.error(f"Error en TaskHandler: {e}", exc_info=True)
            self.send_error(f"Error interno del Servidor B: {e}")

    def send_error(self, error_msg: str):
        """Intenta enviar un error de vuelta al Servidor A."""
        try:
            error_response = {"status": "error", "error": error_msg}
            self.request.sendall(pack_message(error_response))
        except Exception:
            pass # La conexión ya puede estar cerrada

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """Servidor TCP que usa hilos para manejar cada conexión."""
    allow_reuse_address = True
    
    def __init__(self, server_address, RequestHandlerClass, pool):
        super().__init__(server_address, RequestHandlerClass)
        self.process_pool = pool

def main():
    default_procs = os.cpu_count() or 4
    parser = argparse.ArgumentParser(
        description="Servidor de Procesamiento Distribuido (Parte B)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('-i', '--ip', required=True, help="Dirección de escucha (IPv4)")
    parser.add_argument('-p', '--port', required=True, type=int, help="Puerto de escucha")
    parser.add_argument('-n', '--processes', type=int, default=default_procs, 
                        help="Número de procesos en el pool (default: CPU count)")
    
    args = parser.parse_args()

    log.info(f"Iniciando ProcessPoolExecutor con {args.processes} workers...")

    # Usamos un context manager para asegurar que el pool se cierre
    with ProcessPoolExecutor(max_workers=args.processes) as pool:
        server_address = (args.ip, args.port)
        
        server = ThreadedTCPServer(
            server_address, 
            TaskHandler,
            pool=pool
        )
        
        log.info(f"Servidor B (Procesamiento) escuchando en {args.ip}:{args.port}")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            log.info("Servidor B detenido.")
        finally:
            log.info("Cerrando servidor B...")
            server.shutdown()
            server.server_close()

if __name__ == "__main__":
    main()