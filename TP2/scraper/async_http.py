import aiohttp
import asyncio
from aiohttp import ClientTimeout

# Timeout de 30 segundos
SCRAPING_TIMEOUT = 30 

async def fetch_url(session: aiohttp.ClientSession, url: str) -> str:
    """
    Realiza una petición GET asíncrona a la URL y devuelve el contenido HTML.
    Maneja el timeout y errores básicos.
    """
    timeout_config = ClientTimeout(total=SCRAPING_TIMEOUT)
    
    try:
        async with session.get(url, allow_redirects=True, timeout=timeout_config) as response:
            
            # Manejo de códigos de estado HTTP (4xx, 5xx)
            if response.status >= 400:
                response.raise_for_status()
            
            # Leemos el contenido como texto (HTML)
            html_content = await response.text()
            return html_content
            
    except asyncio.TimeoutError:
        # Captura específica del timeout asíncrono
        raise asyncio.TimeoutError(f"Scraping timeout ({SCRAPING_TIMEOUT}s) for {url}")
    except aiohttp.ClientError as e:
        # Captura otros errores de red o HTTP (conexión rechazada, DNS, etc.)
        raise ConnectionError(f"Network or HTTP error for {url}: {e}")
    except Exception as e:
        raise Exception(f"Unexpected error during fetch: {e}")