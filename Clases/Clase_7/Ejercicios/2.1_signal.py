import signal
import time

# Definimos el manejador
def manejar_ctrl_c(signum, frame):
    print(f"Interrupción detectada (señal {signum}). No terminaré aún.")
    
# Asociamos la señal SIGINT al manejador
signal.signal(signal.SIGINT, manejar_ctrl_c)

print("Programa en ejecución. Presioná Ctrl+C para probar...")
while True:
    exit=input("Esperando señal...\nEscriba q para salir\n")
    if exit=='q':
        break
