import aiohttp
from aiohttp import request, web
import logging
import argparse 
import json

from scraper.async_http import fetch_url

# --- Configuración de Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger(__name__)


async def handle_scrape_request(request):
    """
    Manejador de peticiónes de scraping

    Recibe una petición HTTP y devuelve una respuesta JSON con el contenido
    scrapeado de la URL especificada en el cuerpo de la petición.

    Lógica de ejecución:
    1. Espera input del cliente (json)
    2. Obtiene la sesión compartida (ver init_app)
    3. Obtiene los datos del servidor B (ver init_app)
    4. Ejecuta la lógica de scraping con la sesión y datos del servidor B
    5. Devuelve la respuesta con el contenido scrapeado
    6. Mejora la salida del json con ensure_ascii=False, indent=2

    En caso de error, devuelve una respuesta JSON con el estado de error
    y el mensaje de error correspondiente.
    """
    try:
        # 1. Esperar input del cliente 
        data = await request.json()
        url = data.get("url")

        if not url:
            return web.json_response(
                {"status": "error", "message": "Missing parameter: 'url'"},
                status=400
            )
        
        log.info(f"Petición recibida de {request.remote} para: {url}")

        # 2. Obtener la sesión compartida (ver init_app)
        session = request.app['client_session']

        # 3. Obtener datos del servidor B 
        B_IP = request.app['B_IP']
        B_PORT = request.app['B_PORT']

        # 4. Ejecutar la lógica de scraping
        scraped_content = await fetch_url(session, url, (B_IP,B_PORT))

        # 5. Devolver la respuesta
        status_code = 500 if scraped_content.get("status") == "error" else 200

        # 6. Mejorar la salida del json 
        body = json.dumps(scraped_content, ensure_ascii=False, indent=2)
        return web.Response(text=body, status=status_code)

    except Exception as e:
        log.error(f"Error en el manejador principal: {e}", exc_info=True)
        return web.json_response(
            {"status": "error", "message": f"Error interno del servidor: {str(e)}"},
            status=500
        )

# --- Funciones de Arranque y Limpieza ---

async def on_startup(app):
    """Se ejecuta una vez, cuando el servidor arranca."""
    # Crea una sesión de cliente para que la use toda la aplicación
    app['client_session'] = aiohttp.ClientSession()
    log.info("Servidor arrancado, sesión de cliente creada.")

async def on_cleanup(app):
    """Se ejecuta una vez, cuando el servidor se apaga."""
    await app['client_session'].close()
    log.info("Cerrando sesión de cliente...")


def init_app(b_ip, b_port):
    """Inicializa la aplicación web aiohttp."""
    # https://docs.aiohttp.org/en/stable/web_quickstart.html
    app = web.Application()

    # 0. Definir constantes para que puedan ser accedidas desde el handler
    app['B_IP'] = b_ip
    app['B_PORT'] = b_port
    
    # 1. Definir rutas
    # Cualquier petición POST a http://.../scrape será manejada
    # por la función handle_scrape_request
    app.router.add_post("/scrape", handle_scrape_request)
    
    # 2. Registrar funciones de arranque/limpieza
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
    
    return app

def main():
    parser = argparse.ArgumentParser(description="Servidor de Scraping Web Asíncrono")
    parser.add_argument('-i', '--ip', required=True, help="Dirección de escucha (soporta IPv4/IPv6)")
    parser.add_argument('-p', '--port', type=int, required=True, help="Puerto de escucha")
    parser.add_argument('-b', '--b_ip', required=False, default='127.0.0.2', help='Ruta (IPv4) al servidor B - (procesamiento) | Predeterminado: "127.0.0.2"')
    parser.add_argument('-d', '--b_port', required=False, default='8000', help='Puerto del servidor B - (procesamiento) | Predeterminado: "8000"')
    parser.add_argument('-s', '--start_b', type=bool, required=False, default=True , help='Iniciar automaticamente el servidor B | Predeterminado: True')

    args = parser.parse_args()

    app = init_app(args.b_ip, args.b_port)

    log.info(f"Iniciando servidor en http://{args.ip}:{args.port}")
    
    # Esto inicia el servidor y el event loop
    # y se queda corriendo para siempre (hasta Ctrl+C)
    web.run_app(app, host=args.ip, port=args.port)

if __name__ == '__main__':
    main()
