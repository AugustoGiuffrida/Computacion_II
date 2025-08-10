from hashlib import sha256
from json import dumps

def crear_bloque(datos:list, alerta:bool, prev_hash:str) -> dict:
    '''
    Crea un bloque con los datos procesados, el estado de alerta, el hash previo y calcula el nuevo hash.

    Parameters
    ----------
    datos : list
        Lista con tres dicts, uno por cada tipo (frecuencia, presion, oxigeno).
    alerta : bool
        Indica si hay una alerta médica en los datos.
    prev_hash : str
        Hash del bloque anterior.

    Returns
    -------
    dict
        Estructura del bloque.
    '''
    timestamp = datos[0].get('timestamp')  # Todos los datos comparten el mismo timestamp

    cuerpo = {
        'frecuencia': {'media': None, 'desv': None},
        'presion': {'media': None, 'desv': None},
        'oxigeno': {'media': None, 'desv': None},
    }

    for dato in datos:
        tipo = dato.get('tipo')
        cuerpo[tipo] = {
            'media': dato.get('media'),
            'desv': dato.get('desv')
        }

    bloque = {
        'timestamp': timestamp,
        'datos': cuerpo,
        'alerta': alerta,
        'prev_hash': prev_hash,
    }

    # Calcular el hash del bloque
    hash_input = prev_hash + dumps(cuerpo, sort_keys=True) + timestamp
    bloque['hash'] = sha256(hash_input.encode()).hexdigest()

    return bloque
