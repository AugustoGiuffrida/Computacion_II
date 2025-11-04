import base64
import logging
from selenium.webdriver.remote.webdriver import WebDriver

log = logging.getLogger(__name__)

def take_screenshot(url:str,driver:WebDriver):
    """
    Toma un screenshot de una página web.

    Parámetros:
    url (str): La URL de la página a tomar el screenshot.
    driver (WebDriver): El objeto WebDriver que se usará para tomar el screenshot.

    Devuelve un string con el screenshot codificado en base64.
    """
    log.info(f"Tomando screenshot de {url}...")

    try:
        # Espera un poco (no es ideal, pero simple)
        driver.implicitly_wait(2) 
        
        png_data = driver.get_screenshot_as_png()
        b64_data = base64.b64encode(png_data).decode('utf-8')
        log.info(f"Screenshot de {url} completado.")
        return b64_data
        
    except Exception as e:
        log.error(f"Error al tomar screenshot de {url}: {e}")
        raise
