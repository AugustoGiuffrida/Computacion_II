import argparse
import socketserver
import json
import logging
from concurrent.futures import ProcessPoolExecutor
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from datetime import datetime

from processor.screenshot import take_screenshot
from processor.image_processor import generate_thumbnail
from processor.performance import analyze_performance

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

def setup_driver():
    """Configurar los parametros del driver (selenium)"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-deb-shm-usage")
    chrome_options.add_argument("--window-size=1280,720")
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(20)
    return driver


# --- Funciones de Tarea (CPU-Bound) ---
# Estas funciones se ejecutarán en el ProcessPoolExecutor
def run_full_analysis(url: str) -> dict:
    """
    Realiza un análisis completo de una página web.

    Este análisis comprende tres partes:
    1. Generar un screenshot de la página.
    2. Analizar el rendimiento de la página (window.performance).
    3. Generar thumbnails de las imágenes de la página.

    Parámetros:
    url (str): La URL de la página a analizar.

    Devuelve un diccionario con los siguientes campos:
    status (str): El estado del análisis ("success" o "error").
    screenshot (str): El screenshot de la página en formato base64.
    performance (dict): Los datos de rendimiento de la página (ver analyze_performance).
    thumbnails (list): Las thumbnails generadas (ver generate_thumbnail).
    """
    log.info(f"[PID {os.getpid()}] Iniciando análisis para: {url}")
    driver = None
    try:
        driver = setup_driver()
        driver.get(url)
        # 1. Generar Screenshot
        screenshot_b64 = take_screenshot(url=url, driver=driver)
        
        # 2. Análisis de Rendimiento
        performance_data = analyze_performance(url=url, driver=driver)
        
        # 3. Análisis de Imágenes
        thumbnails = generate_thumbnail(driver=driver)
        
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

    finally:
        if driver:
            driver.quit()

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

            start = datetime.now()
            # --- 2. Enviar tarea al Pool de Procesos ---
            # self.server.process_pool es el ProcessPoolExecutor
            future = self.server.process_pool.submit(
                run_full_analysis, 
                task_data['url']
            )
            
            # Obtenemos el resultado (esto bloquea ESTE HILO, 
            # pero no el servidor principal ni otros hilos)
            result = future.result() 

            end = datetime.now()
            log.info(f'Tiempo transcurrido para el analisis: {end-start}')

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
    DEFAULT_NUM_PROCESS = 4

    parser = argparse.ArgumentParser(description="Servidor de Procesamiento Distribuido")
    parser.add_argument('-i', '--ip', required=True, help="Dirección de escucha")
    parser.add_argument('-p', '--port', required=True, type=int, help="Puerto de escucha")
    parser.add_argument('-n', '--processes', type=int, default=DEFAULT_NUM_PROCESS, 
                        help="Número de procesos en el pool (default: 4)")
    
    args = parser.parse_args()
    
    num_processes = args.processes if args.processes else DEFAULT_NUM_PROCESS
    log.info(f"Iniciando ProcessPoolExecutor con {num_processes} workers...")

    # Creamos un pool (por defecto de 4 procesos). Estos procesos
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
