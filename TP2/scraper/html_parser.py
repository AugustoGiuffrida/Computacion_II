from bs4 import BeautifulSoup
import logging

log = logging.getLogger(__name__)

def parse_html_content(html_content):
    """
    Analiza el contenido HTML de una página y devuelve información relevante.
    
    El contenido HTML se analiza utilizando BeautifulSoup y se extraen los siguientes datos:
    - Título de la página
    - Todos los enlaces (links) encontrados
    - Meta tags relevantes (description, keywords, Open Graph tags)
    - Estructura básica (cantidad de headers H1-H6)
    - Cantidad de imágenes en la página
    
    La función devuelve un diccionario con la siguiente estructura:
    {
        "title": str,
        "links": List[str],
        "meta_tags": Dict[str, str],
        "structure": Dict[str, int],
        "images_count": int
    }
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Título
    title = soup.title.string if soup.title else "Sin Título"
    
    links = []
    for a in soup.find_all('a', href=True):
        links.append(a['href'])
        
    # Metadatos 
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
        "links": links[:50], # Limite de 50 (para no llenar la salida)
        "meta_tags": meta_tags,
        "structure": structure,
        "images_count": images_count
    }

async def scrape_page_data(content):
    """
    Analiza el contenido HTML de una página y devuelve información relevante.
    
    Esta función utiliza `parse_html_content` para analizar el contenido HTML y devuelve un diccionario con la siguiente estructura:
    {
        "title": str,
        "links": List[str],
        "meta_tags": Dict[str, str],
        "structure": Dict[str, int],
        "images_count": int
    }
    """
    data = parse_html_content(content)
    return data
