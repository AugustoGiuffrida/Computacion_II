import asyncio
import json
import logging

log = logging.getLogger(__name__)

async def request_processing_from_server_b(server_b_config, task_data):
    """
    Realiza una petición asincrona al Servidor B y devuelve una respuesta.

    Args:
        server_b_config (tuple): Tuple con la IP y el puerto del Servidor B.
        task_data (dict): Diccionario con los datos de la tarea.

    Returns:
        dict: Diccionario con los datos de procesamiento.

    Raises:
        asyncio.TimeoutError: Si el Servidor B no responde en el timeout especificado.
        Exception: Si ocurre un error de comunicación con el Servidor B.
    """
    host, port = server_b_config
    try:
        log.debug(f"Conectando al Servidor B en {host}:{port}")
        # 1. Conectar de forma asíncrona
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=5.0 # Timeout de conexión
        )

        # 2. Serializar y enviar datos (con protocolo de longitud)
        data = json.dumps(task_data).encode('utf-8')
        header = len(data).to_bytes(4, 'big')
        
        writer.write(header + data)
        await writer.drain()
        log.debug(f"Datos enviados al Servidor B: {task_data}")

        # 3. Recibir respuesta (con protocolo de longitud)
        response_header = await asyncio.wait_for(reader.readexactly(4), timeout=30.0)
        if not response_header:
            raise ConnectionError("Servidor B cerró la conexión inesperadamente (header)")
            
        response_len = int.from_bytes(response_header, 'big')
        
        response_data = await asyncio.wait_for(reader.readexactly(response_len), timeout=30.0)
        if not response_data:
            raise ConnectionError("Servidor B cerró la conexión inesperadamente (data)")

        log.debug("Respuesta recibida del Servidor B")
        
        # 4. Cerrar y deserializar
        writer.close()
        await writer.wait_closed()
        
        return json.loads(response_data.decode('utf-8'))

    except asyncio.TimeoutError:
        log.error(f"Timeout en la comunicación con el Servidor B ({host}:{port})")
        raise
    except Exception as e:
        log.error(f"Error de comunicación con Servidor B: {e}")
        raise
