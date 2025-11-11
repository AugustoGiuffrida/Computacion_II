import json
import struct
import logging

# Usamos 'Big-Endian' (network byte order) para el unsigned int de 4 bytes
_HEADER = struct.Struct('!I')
HEADER_SIZE = _HEADER.size

log = logging.getLogger(__name__)

def pack_message(data: dict) -> bytes:
    """Serializa un dict a JSON y le prefija 4 bytes de longitud."""
    try:
        payload = json.dumps(data).encode('utf-8')
        header = _HEADER.pack(len(payload))
        return header + payload
    except Exception as e:
        log.error(f"Error al empaquetar mensaje: {e}")
        return b""

def read_exact(sock, n: int) -> bytes:
    """
    Función de ayuda bloqueante para leer exactamente 'n' bytes de un socket.
    Usado por el Servidor B (socketserver síncrono).
    """
    buf = bytearray()
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("Socket cerrado inesperadamente al leer")
        buf.extend(chunk)
    return bytes(buf)

def recv_message(sock) -> dict:
    """
    Recibe un mensaje completo (header + payload) de un socket bloqueante.
    """
    try:
        # 1. Leer Header
        header_bytes = read_exact(sock, HEADER_SIZE)
        (msg_len,) = _HEADER.unpack(header_bytes)
        
        # 2. Leer Payload
        payload_bytes = read_exact(sock, msg_len)
        
        # 3. Deserializar
        return json.loads(payload_bytes.decode('utf-8'))
        
    except (struct.error, json.JSONDecodeError, ConnectionError) as e:
        log.error(f"Error al recibir/decodificar mensaje: {e}")
        raise ConnectionError("Fallo en el protocolo de recepción") from e
    except Exception as e:
        log.error(f"Error inesperado en recv_message: {e}")
        raise e