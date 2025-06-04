import os
import signal
import time

# Manejador común para los hijos
def recibir_orden(signum, frame):
    print(f"Hijo (PID {os.getpid()}): Señal {signum} recibida. Comenzando ejecución...")

# Configuramos el manejador
signal.signal(signal.SIGUSR1, recibir_orden)

# Creamos dos hijos
hijos = []
for i in range(2):
    pid = os.fork()
    if pid == 0:
        # Código del hijo
        print(f"Hijo {i+1}: Esperando señal del padre. PID: {os.getpid()}")
        signal.pause()
        print(f"Hijo {i+1}: Terminando.")
        os._exit(0)
    else:
        hijos.append(pid)

# Código del padre
for i, pid in enumerate(hijos):
    print(f"Padre: Enviando SIGUSR1 a Hijo {i+1} (PID {pid}) en {3 * (i+1)} segundos...")
    time.sleep(3 * (i + 1))
    os.kill(pid, signal.SIGUSR1)

# Esperar que terminen los hijos
for pid in hijos:
    os.waitpid(pid, 0)

print("Padre: Todos los hijos han finalizado.")
