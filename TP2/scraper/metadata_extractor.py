from bs4 import BeautifulSoup
from typing import Dict

# Tags Open Graph y otros que buscamos
META_TAGS_TO_EXTRACT = [
    'description', 
    'keywords', 
    'og:title', 
    'og:description', 
    'og:image',
    'twitter:card',
    'twitter:title'
]

def extract_meta_tags(html_content: str) -> Dict:
    """
    Extrae meta tags relevantes (description, keywords, Open Graph tags).
    """
    soup = BeautifulSoup(html_content, 'html')
    meta_tags = {}
    
    # 1. Extraer tags 'name' y 'property'
    for tag in soup.find_all('meta'):
        
        # Buscar por atributo 'name' (description, keywords)
        key = tag.get('name') or tag.get('property')
        
        if key in META_TAGS_TO_EXTRACT:
            content = tag.get('content')
            if content:
                 meta_tags[key] = content
            
    return meta_tags