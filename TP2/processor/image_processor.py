from PIL import Image
import requests
import io
import base64
from typing import List, Dict
import logging

log = logging.getLogger(__name__)

# Definición del tamaño del thumbnail requerido
THUMBNAIL_SIZE = (150, 150)
MAX_IMAGES_TO_PROCESS = 5 # Límite para evitar sobrecarga

def generate_thumbnail_b64(image_data: bytes) -> str:
    """
    Toma los bytes de una imagen, genera un thumbnail (PNG)
    y lo devuelve codificado en Base64.
    """
    try:
        img = Image.open(io.BytesIO(image_data))
        img.thumbnail(THUMBNAIL_SIZE)
        output = io.BytesIO()
        img.save(output, format="PNG") # Usamos PNG para thumbnails
        return base64.b64encode(output.getvalue()).decode('utf-8')
        
    except Exception as e:
        log.error(f"Error procesando imagen con Pillow: {e}")
        return ""

def process_images(image_urls: List[str]) -> List[str]:
    """
    Descarga un número limitado de imágenes y genera sus thumbnails.
    """
    thumbnail_b64_list = []
    log.info(f"[Processor] Procesando {len(image_urls)} URLs de imágenes (límite {MAX_IMAGES_TO_PROCESS})...")
    
    processed_count = 0
    for url in image_urls: 
        if processed_count >= MAX_IMAGES_TO_PROCESS:
            break
            
        if not url.startswith(('http://', 'https://')):
            continue 
            
        try:
            response = requests.get(url, timeout=10) 
            
            if response.status_code == 200 and 'image' in response.headers.get('Content-Type', ''):
                
                thumb = generate_thumbnail_b64(response.content)
                if thumb:
                    thumbnail_b64_list.append(thumb)
                    processed_count += 1
            
        except requests.exceptions.Timeout:
            log.warning(f"Timeout al descargar imagen: {url}")
        except Exception as e:
            log.warning(f"Fallo al descargar/procesar {url}: {e}")
            
    log.info(f"[Processor] {len(thumbnail_b64_list)} thumbnails generados.")
    return thumbnail_b64_list