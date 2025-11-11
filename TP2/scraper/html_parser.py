from bs4 import BeautifulSoup
from typing import Dict, List
from urllib.parse import urljoin # Para resolver URLs relativas

def scrape_html_content(html_content: str, base_url: str) -> Dict:
    """
    Extrae el título, enlaces, conteo y URLs de imágenes, y estructura de encabezados.
    """
    soup = BeautifulSoup(html_content, 'lxml')
    
    # 1. Título
    title = soup.title.string.strip() if soup.title and soup.title.string else "No Title Found"
    
    # 2. Enlaces (Links)
    links = []
    for a in soup.find_all('a', href=True):
        href = a['href'].strip()
        if href:
            # Convierte enlaces relativos (ej: /about) a absolutos
            full_url = urljoin(base_url, href)
            links.append(full_url)
    
    # 3. Imágenes
    images = soup.find_all('img', src=True)
    images_count = len(images)
    image_urls = []
    for img in images:
        src = img.get('src', '').strip()
        if src:
            # Convierte URLs relativas a absolutas
            full_url = urljoin(base_url, src)
            image_urls.append(full_url)
            
    # 4. Estructura de encabezados
    structure = {f'h{i}': len(soup.find_all(f'h{i}')) for i in range(1, 7)}
        
    return {
        "title": title,
        "links": links,
        "structure": structure,
        "images_count": images_count,
        "image_urls": image_urls # Importante para Servidor B
    }