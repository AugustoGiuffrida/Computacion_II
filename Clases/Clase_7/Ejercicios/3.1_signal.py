import signal
import time
import os

def handler(signum, frame):
    print(f"Señal recibida: {signum}")

# Asociamos la señal SIGUSR1 al handler
signal.signal(signal.SIGUSR1, handler)

print(f"PID del proceso: {os.getpid()}")
print("Esperando señales. Usá `kill -s SIGUSR1 <PID>` desde otra terminal.")

# Bucle infinito para mantener el programa corriendo
while True:
    time.sleep(1)
