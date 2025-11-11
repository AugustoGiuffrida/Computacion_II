import json

def serialize_data(data: dict) -> bytes:
    """Serializa un diccionario a bytes usando JSON."""
    return json.dumps(data).encode('utf-8')

def deserialize_data(data_bytes: bytes) -> dict:
    """Deserializa bytes a un diccionario Python."""
    return json.loads(data_bytes.decode('utf-8'))