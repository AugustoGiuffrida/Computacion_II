from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import base64
import logging

log = logging.getLogger(__name__)

def generate_screenshot(url: str) -> str:
    """
    Genera un screenshot de la URL usando Selenium Headless.
    Devuelve la imagen como una cadena Base64.
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1280,720")
    
    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        # Timeout de carga de página de 30 segundos
        driver.set_page_load_timeout(30) 
        
        log.info(f"[Processor] Navegando a {url} para screenshot...")
        driver.get(url)
        
        # Captura la imagen como bytes PNG
        png_bytes = driver.get_screenshot_as_png()
        
        # Codifica a Base64 para el JSON de respuesta
        log.info(f"[Processor] Screenshot generado para {url}.")
        return base64.b64encode(png_bytes).decode('utf-8')
        
    except Exception as e:
        # Manejo de errores de Selenium/Carga de página
        log.error(f"Error generando screenshot para {url}: {e}")
        return "" # Devuelve cadena vacía si falla la captura
    finally:
        if driver:
            driver.quit()