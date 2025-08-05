from datetime import datetime
import random, json, time
from os import getpid

def generar_dato():
    '''
    Genera un diccionario por segundo:
    {
       "timestamp": "YYYY-MM-DDTHH:MM:SS",
       "frecuencia": int(60-180),
       "presion": [int(110-180), int(70-110)],
       "oxigeno": int(90-100)
    }
    '''
    # Devuelve un diccionario con los campos frecuencia, presión y oxígeno
    # {"timestamp": "2025-06-11T15:32:09", "frecuencia": 122, "presion": [166, 99], "oxigeno": 100}
    return json.dumps({
        "timestamp": datetime.now().isoformat(timespec='seconds'),
        "frecuencia": random.randint(40, 220),
        "presion": [random.randint(110, 220), random.randint(40, 110)], # [sistolica, diastolica]
        "oxigeno": random.randint(89, 100)
    })

def generar(n:int=60,pipes:list=[],verbose:bool=False):
    '''
    Genera n datos y los escribe en los pipes pipe_frec, pipe_press y pipe_ox.
    
    Parameters
    ----------
    n : int
        Número de datos a generar.
    pipe_frec : any
        Extremo de escritura del pipe para la frecuencia.
    pipe_press : any
        Extremo de escritura del pipe para la presión.
    pipe_ox : any
        Extremo de escritura del pipe para el oxígeno.
    verbose : bool
        Imprime en stdout los datos generados si es True.
    '''
    print(f'[{getpid()}] Proceso generador iniciado.')
    for i in range(n):
        dato = generar_dato()
        for pipe in pipes:
            pipe.send(dato)
        if verbose:
            print(f'[{getpid()}] Proceso generador: dato {i+1} generado; escribiendo en pipes: \n\t{dato}')
        time.sleep(1)