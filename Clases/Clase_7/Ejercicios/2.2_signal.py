import signal
import time
import os

# Definimos el manejador
def manejar_ctrl_c(signum, frame):
    print(f"Interrupción detectada (señal {signum}). No terminaré aún.")

def manejar_sigusr1(signum, frame):
    print(f"Interrupción detectada (señal {signum}). Esta es una señal kill, no moriré.")
    
# Asociamos la señal SIGINT al manejador
signal.signal(signal.SIGINT, manejar_ctrl_c)
signal.signal(signal.SIGUSR1, manejar_sigusr1)

print(f"Programa en ejecución. Presioná Ctrl+C o envía una señal con `kill -SIGUSR1 {os.getpid()}` para probar...")
while True:
    exit=input("Esperando señal...\nEscriba q para salir\n")
    if exit=='q':
        break