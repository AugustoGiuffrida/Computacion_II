from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from typing import Dict
import time
import logging

log = logging.getLogger(__name__)

def analyze_performance(url: str, driver: webdriver.Chrome) -> Dict[str, float]:
    """
    Calcula métricas de rendimiento (tiempo de carga) usando la API de 
    Performance Timing del navegador a través de Selenium.
    
    Reutiliza un driver si se pasa uno, o crea uno nuevo si no.
    """
    
    # Ejecutar JavaScript para obtener el objeto performance.timing
    # Esto proporciona métricas precisas del navegador.
    log.info(f"[Processor] Analizando rendimiento para {url}...")
    
    try:
        timing_js = "return window.performance.timing.toJSON()"
        timing = driver.execute_script(timing_js)
        
        resources_js = "return window.performance.getEntriesByType('resource')"
        resources = driver.execute_script(resources_js)

        # Calcular el tiempo de carga final (LoadEventEnd - NavigationStart)
        # Los valores son timestamps en milisegundos Unix.
        navigation_start = timing.get('navigationStart', 0)
        load_event_end = timing.get('loadEventEnd', 0)
        
        load_time_ms = 0
        if navigation_start and load_event_end and load_event_end > navigation_start:
            load_time_ms = load_event_end - navigation_start
        
        # Calcular tamaño total (aproximado desde 'transferSize')
        total_size_bytes = 0
        for res in resources:
            total_size_bytes += res.get('transferSize', 0)
            
        # Contar requests
        num_requests = len(resources)
        
        log.info(f"[Processor] Análisis de rendimiento completado para {url}.")
        
        return {
            "load_time_ms": load_time_ms,
            "total_size_kb": round(total_size_bytes / 1024, 2),
            "num_requests": num_requests
        }
        
    except Exception as e:
        log.error(f"Error analizando rendimiento para {url}: {e}")
        return {
            "load_time_ms": 0,
            "total_size_kb": 0,
            "num_requests": 0
        }