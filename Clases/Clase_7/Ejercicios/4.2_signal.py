import os
import signal
import time
import sys

# Estado compartido en el hijo
orden_recibida = False

def manejar_usr1(signum, frame):
    global orden_recibida
    orden_recibida = True
    print(f"Hijo (PID {os.getpid()}): Recibida SIGUSR1. Iniciando tarea...")

def manejar_term(signum, frame):
    print(f"Hijo (PID {os.getpid()}): Recibida SIGTERM. Cancelando ejecución.")
    sys.exit(1)

# Asignar manejadores
signal.signal(signal.SIGUSR1, manejar_usr1)
signal.signal(signal.SIGTERM, manejar_term)

pid = os.fork()

if pid == 0:
    # Código del hijo
    print(f"Hijo: Esperando orden. PID: {os.getpid()}")
    while not orden_recibida:
        signal.pause()
    print("Hijo: Ejecutando tarea principal...")
    time.sleep(2)
    print("Hijo: Tarea completada.")
    sys.exit(0)
else:
    print(f"Padre: Esperando 2 segundos para decidir qué hacer con el hijo (PID {pid})...")
    time.sleep(2)

    # Aquí podés alternar entre estas dos líneas para ver los dos comportamientos:
    os.kill(pid, signal.SIGUSR1)  # para iniciar la tarea
    # os.kill(pid, signal.SIGTERM)  # para cancelarla

    os.waitpid(pid, 0)
    print("Padre: Hijo finalizado.")
