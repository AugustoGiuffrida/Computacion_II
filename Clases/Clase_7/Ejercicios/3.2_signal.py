import signal
import time
import os
import sys

def term_handler(signum, frame):
    print("Se recibió SIGTERM. Finalizando el programa de forma limpia...")
    sys.exit(0)

# Asignamos el manejador para SIGTERM
signal.signal(signal.SIGTERM, term_handler)

print(f"PID del proceso: {os.getpid()}")
print("Esperando SIGTERM. Usá `kill -s SIGTERM <PID>` para terminar el programa.")

while True:
    time.sleep(1)
