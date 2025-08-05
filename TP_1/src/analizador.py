import json
from time import sleep
from src.utils import media, desviacion
from random import randint
from os import getpid
    
def leer_datos(canal_entrada:any=None, ventana:list=[], ventana_size:int=30):
    '''
    Lee un dato del canal de entrada y lo agrega a la ventana.
    El tamaño de la ventana está dado por `ventana_size`. Si se supera este tamaño se elimina el elemento más antiguo.

    Parameters
    ----------
    canal_de_entrada : any
        Debe ser algún canal que permita IPC, como el extremo de lectura de un Pipe.
    ventana : list
        Lista por referencia, donde se agregan los datos leidos del generador.
    ventana_size : int
        Número entero que determina el tamaño de la ventana.
    '''

    # Formato del dato string: {"timestamp": "2025-06-11T15:32:09", "frecuencia": 122, "presion": [166, 99], "oxigeno": 100}
    ventana.append(json.loads(canal_entrada.recv())) # Validar que la string sea un json válido
    if len(ventana) > ventana_size:
        ventana.pop(0)

def procesar(tipo:str='none',ventana:list=[],verbose:bool=False):
    '''
    Procesa los datos de la ventana según el tipo de dato y devuelve un objeto con la media, desviación estándar y timestamp.
    
    Parameters
    ----------
    tipo : str
        Tipo de dato. Puede ser 'frecuencia', 'presion' o 'oxigeno'.
    ventana : list
        Lista por referencia, con los datos leidos del generador.

    Returns
    -------
    resultado : dict 
        Un diccionario con la media y la desviación estándar del tipo especificado respetando el siguiente formato:
        ```
        {
        'tipo': tipo,
        'timestamp': timestamp,
        'media': med,
        'desv': desv
        }
        ```
    '''
    timestamp = ventana[-1].get('timestamp')

    # Obtiene los datos según el self.__tipo__ entonces:
    # Frecuen: datos = [55,59,65,70,90,...] todas las frecuencias cardiacas que hay en ventana 
    # Presión: datos = [[110,80], [112,90], ...] todas las listas de presion que hay en ventana
    # Oxigeno: datos = [92,95,96,95,96,...] todos los oxigenos que hay en ventana
    datos = [dato.get(tipo) for dato in ventana]

    med = media(tipo, datos)
    desv = desviacion(tipo, datos)
    # Simula un calculo costoso (1 a 5 segundos float)
    sleep(randint(1,300)/100)

    resultado = {
        'tipo': tipo,
        'timestamp': timestamp,
        'media': med,
        'desv': desv
    }
    if verbose:
        print(f'[{getpid()} - {tipo}] Procesado:\n\t{resultado}')
    return resultado

def analizar(
        tipo:str='none',
        pipe_to_read:any=None, 
        queue:any=None, n:int=0, 
        done_count:any=None,
        cond:any=None, 
        total_procs:int=3, 
        verbose:bool=False
    ):
    '''
    Analiza los datos del pipe_to_read y envía los resultados a la queue.
    
    Parameters
    ----------
    tipo : str
        Tipo de dato. Puede ser 'frecuencia', 'presion' o 'oxigeno'.
    pipe_to_read : any
        Debe ser el extremo de lectura de un Pipe.
    queue : any
        Debe ser una Queue.
    n : int
        Número entero que determina cuántas veces se lee del pipe y se envía a la queue.
    '''
    print(f'[{getpid()} - {tipo}] Proceso analizador iniciado.')
    ventana = []
    for _ in range(n):
        if verbose:
            print(f'[{getpid()} - {tipo}] Leyendo datos de la tubería...')
        leer_datos(canal_entrada=pipe_to_read, ventana=ventana)
        if verbose:
            print(f'[{getpid()} - {tipo}] Tamaño de la ventana: {len(ventana)} | Escribiendo datos en la cola...')
        queue.put(json.dumps(procesar(tipo=tipo, ventana=ventana,verbose=verbose)))
        # Incrementar contador
        with cond:
            done_count.value += 1
            if done_count.value == total_procs:
                done_count.value = 0
                cond.notify_all()  # Avisar a los demas que todos terminaron
            else:
                cond.wait() # Sino esperar a que todos terminen
