from json import dumps, loads
from time import sleep
from random import randint
from os import getpid
from src.utils import media, desviacion

# Imports para mejorar el tipado (para hacer un poco más verborrágico a python jaja)
from multiprocessing.connection import Connection
from multiprocessing.queues import Queue
from typing import Any, List

def leer_datos(canal_entrada:Connection, ventana:List=[], ventana_size:int=30):
    '''
    Consume (o lee) un dato del canal de entrada y lo agrega a la ventana.
    El tamaño de la ventana está dado por `ventana_size`. Si se supera este tamaño se elimina el elemento más antiguo.

    Parameters
    ----------
    canal_de_entrada : Connection
        Debe ser algún canal que permita IPC, como el extremo de lectura de un Pipe (consumidor).
    ventana : List
        Lista por referencia, donde se agregan los datos leidos del generador.
    ventana_size : int
        Número entero que determina el tamaño de la ventana.
    '''

    # Formato del dato string: {"timestamp": "2025-06-11T15:32:09", "frecuencia": 122, "presion": [166, 99], "oxigeno": 100}
    ventana.append(loads(canal_entrada.recv())) # Validar que la string sea un json válido
    if len(ventana) > ventana_size:
        ventana.pop(0)

def procesar(tipo:str='none',ventana:List=[],verbose:bool=False):
    '''
    Procesa los datos de la ventana según el tipo de dato y devuelve un objeto con la media, desviación estándar y timestamp.
    
    Parameters
    ----------
    tipo : str
        Tipo de dato. Puede ser 'frecuencia', 'presion' o 'oxigeno'.
    ventana : List
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
    if tipo != 'frecuencia' and tipo != 'presion' and tipo != 'oxigeno' or len(ventana) == 0:
        raise ValueError
    timestamp = ventana[-1].get('timestamp')

    # Obtiene los datos según el self.__tipo__ entonces:
    # Frecuen: datos = [55,59,65,70,90,...] todas las frecuencias cardiacas que hay en ventana 
    # Presión: datos = [[110,80], [112,90], ...] todas las Listas de presion que hay en ventana
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
        pipe_to_read:Connection, 
        queue:Queue,
        tipo:str='none',
        n:int=0, 
        done_count:Any=None,
        cond:Any=None, 
        total_procs:int=3, 
        verbose:bool=False
    ):
    '''
    Analiza los datos del pipe_to_read y envía los resultados a la queue.
    
    Parameters
    ----------
    pipe_to_read : Connection
        Debe ser el extremo de lectura de un Pipe.
    queue : Queue
        Debe ser una Queue (se usará como productor).
    tipo : str
        Tipo de dato. Puede ser 'frecuencia', 'presion' o 'oxigeno'.
    n : int
        Número entero que determina cuántas veces se lee del pipe y se envía a la queue.
    done_count: Any
        Se espera un valor (Value) compartido, que se utiliza como "semaforo", para esperar 
        a que todos los procesos analizadores terminen y los datos se escriban en orden en 
        la cola. 
    cond: Any 
        Es la condición que me permite escribir el Value recibido (done_count) y esperar
        al resto de procesos.
    total_procs: int
        Cantidad de procesos analizadores que se crearán.
    verbose: bool
        Mostrar información adicional en la salida estándar.
    '''
    if tipo != 'frecuencia' and tipo != 'presion' and tipo != 'oxigeno':
        raise ValueError
    print(f'[{getpid()} - {tipo}] Proceso analizador iniciado.')
    ventana = []
    for _ in range(n):
        if verbose:
            print(f'[{getpid()} - {tipo}] Leyendo datos de la tubería...')
        leer_datos(canal_entrada=pipe_to_read, ventana=ventana)
        if verbose:
            print(f'[{getpid()} - {tipo}] Tamaño de la ventana: {len(ventana)} | Escribiendo datos en la cola...')
        queue.put(dumps(procesar(tipo=tipo, ventana=ventana, verbose=verbose)))
        # Incrementar contador
        with cond:
            done_count.value += 1
            if done_count.value == total_procs:
                done_count.value = 0
                cond.notify_all()  # Avisar a los demas que todos terminaron
            else:
                cond.wait() # Sino esperar a que todos terminen
