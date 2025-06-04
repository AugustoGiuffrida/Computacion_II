import os
import signal
import time

NUM_HIJOS = 3
pipes = []
pids = []

# Manejador en los hijos
def iniciar_trabajo(signum, frame):
    print(f"Hijo (PID {os.getpid()}): Recibí la orden, empezando tarea...")
    time.sleep(1)  # Simula una tarea
    os.write(pipe_w, f"Hijo {os.getpid()} finalizado\n".encode())
    os._exit(0)

# Código principal (proceso maestro)
for i in range(NUM_HIJOS):
    pipe_r, pipe_w = os.pipe()  # Crear un pipe
    pid = os.fork()

    if pid == 0:
        # Código del hijo
        for fd in pipes:  # Cerramos pipes heredados innecesarios
            os.close(fd[0])
            os.close(fd[1])
        os.close(pipe_r)  # El hijo no necesita leer del pipe
        signal.signal(signal.SIGUSR1, iniciar_trabajo)
        print(f"Hijo {i+1} (PID {os.getpid()}): Esperando señal...")
        globals()['pipe_w'] = pipe_w  # Guardar para usar en el handler
        signal.pause()
    else:
        pipes.append((pipe_r, pipe_w))
        pids.append(pid)

# Código del padre
for i, (pid, (r, w)) in enumerate(zip(pids, pipes)):
    os.close(w)  # El padre no necesita escribir en el pipe
    print(f"Maestro: Enviando SIGUSR1 a Hijo {i+1} (PID {pid})...")
    time.sleep(1)
    os.kill(pid, signal.SIGUSR1)

# Leer mensajes de los hijos
for i, (r, _) in enumerate(pipes):
    msg = os.read(r, 1024).decode()
    print(f"Maestro: Recibido -> {msg.strip()}")
    os.close(r)

# Esperar a que todos los hijos terminen
for pid in pids:
    os.waitpid(pid, 0)

print("Maestro: Todos los hijos han completado su tarea.")
