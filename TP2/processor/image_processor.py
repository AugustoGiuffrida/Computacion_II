import io
import base64
import logging
import asyncio
import aiohttp
from PIL import Image
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By

log = logging.getLogger(__name__)

# --- Parte Asíncrona (Green Threads) ---

async def fetch_image(session: aiohttp.ClientSession, url: str) -> bytes | None:
    """
    Descarga una imagen en forma asíncrona
    
    Args:
        session (aiohttp.ClientSession): Sesión de aiohttp
        url (str): URL de la imagen a descargar
    
    Returns:
        bytes | None: Bytes de la imagen descargada o None si falló
    """
    try:
        async with session.get(url, timeout=5) as response:
            response.raise_for_status()
            return await response.read()  # Devuelve los bytes crudos
    except Exception as e:
        log.warning(f"No se pudo descargar la imagen {url}: {e}")
        return None

async def download_all_images_async(image_urls: list[str]) -> list[bytes]:
    """
    Descarga todas las imágenes en forma asíncrona y devuelve una lista de bytes

    Args:
        image_urls (list[str]): lista de URLs de las imágenes a descargar

    Returns:
        list[bytes]: lista de bytes de las imágenes descargadas
    """
    async with aiohttp.ClientSession() as session:
        # Crea una lista de tareas (coroutines)
        tasks = [fetch_image(session, url) for url in image_urls]
        
        # Ejecuta todas las tareas en paralelo y espera a que terminen
        results = await asyncio.gather(*tasks)
        
        # Filtra los resultados que fallaron (None)
        return [data for data in results if data]

# --- Parte Síncrona (CPU-Bound) ---

def process_image_data_sync(img_data: bytes, size: tuple) -> str | None:
    """
    Procesa una imagen en formato bytes y devuelve su thumbnail en formato
    base64.

    Args:
        img_data (bytes): Bytes de la imagen a procesar
        size (tuple): Tamaño de la thumbnail (ancho, alto)

    Returns:
        str | None: Base64 de la thumbnail procesada o None si falló
    """
    try:
        with Image.open(io.BytesIO(img_data)) as img:
            img.thumbnail(size)
            thumb_io = io.BytesIO()
            img.save(thumb_io, format="PNG")
            return base64.b64encode(thumb_io.getvalue()).decode('utf-8')
    except Exception as e:
        log.warning(f"No se pudo procesar la imagen (¿formato inválido?): {e}")
        return None

# --- Función Principal (Puerta de enlace) ---

def generate_thumbnail(driver: WebDriver, max_thumbnails=5, size=(100, 100)) -> list[str]:
    """
    Genera thumbnails de imágenes en una página web.

    Args:
        driver (WebDriver): Instancia de WebDriver para acceder a la página
        max_thumbnails (int): Número máximo de thumbnails a generar (default: 5)
        size (tuple): Tamaño de la thumbnail (ancho, alto) (default: (100, 100))

    Returns:
        list[str]: Lista de thumbnails en formato base64
    """
    log.info(f"Iniciando procesamiento de imágenes...")
    
    try:
        # --- 1. Obtener URLs (Síncrono, con Selenium) ---
        image_elements = driver.find_elements(By.TAG_NAME, "img")
        image_urls = []
        for img in image_elements:
            src = img.get_attribute('src')
            if src and src.startswith('http'):
                image_urls.append(src)
        
        urls_to_fetch = image_urls[:max_thumbnails]
        log.info(f"Se encontraron {len(image_urls)} imágenes. Procesando {len(urls_to_fetch)}...")

        if not urls_to_fetch:
            return []

        # --- 2. Descargar Imágenes (Asíncrono / Concurrente) ---
        # Esta es la "puerta": usamos asyncio.run() para ejecutar
        # nuestra tarea de descarga asíncrona.
        log.info("Iniciando descarga concurrente de imágenes...")
        all_image_data = asyncio.run(download_all_images_async(urls_to_fetch))
        log.info(f"Descarga completada. {len(all_image_data)} imágenes obtenidas.")

        # --- 3. Procesar Imágenes (Síncrono / CPU-Bound) ---
        # Ahora que tenemos todos los datos, procesamos (CPU-bound)
        # secuencialmente. Esto está bien, ya no hay esperas de red.
        thumbnails = []
        for data in all_image_data:
            thumb_b64 = process_image_data_sync(data, size)
            if thumb_b64:
                thumbnails.append(thumb_b64)

        log.info(f"Se generaron {len(thumbnails)} thumbnails.")
        return thumbnails

    except Exception as e:
        log.error(f"Error al procesar imágenes: {e}")
        raise # Dejamos que el orquestador maneje el error
