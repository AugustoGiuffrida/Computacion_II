import json
import logging
from selenium.webdriver.remote.webdriver import WebDriver

log = logging.getLogger(__name__)

def analyze_performance(url:str,driver: WebDriver):
    """
    Analiza el rendimiento de una página web utilizando el objeto window.performance.

    Parámetros:
    url (str): La URL de la página a analizar.
    driver (WebDriver): El driver de Selenium para acceder a la página.

    Devuelve un diccionario con los siguientes campos:
    load_time_ms (int): El tiempo de carga de la página en milisegundos.
    total_size_kb (float): El tamaño total de los recursos cargados en kilobytes.
    num_requests (int): El número de solicitudes realizadas para cargar la página.
    """
    log.info(f"Analizando rendimiento de {url}...")
    
    try:
        performance = json.loads(
            driver.execute_script("return JSON.stringify(window.performance.timing)")
        )
        resources = json.loads(
            driver.execute_script("return JSON.stringify(window.performance.getEntriesByType('resource'))")
        )

        load_time_ms = performance['loadEventEnd'] - performance['navigationStart']
        num_requests = len(resources)
        total_size_kb = sum(r.get('transferSize', 0) for r in resources) / 1024

        return {
            "load_time_ms": load_time_ms,
            "total_size_kb": round(total_size_kb, 2),
            "num_requests": num_requests
        }
    except Exception as e:
        log.error(f'Error al analizar rendimiento: {e}')
        raise
