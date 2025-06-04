import signal
import time

# Defino un contador global para contar la cantidad de señales
signal_count=0

# Definimos el manejador
def manejar_ctrl_c(signum, frame):
    global signal_count
    print(f"Interrupción detectada (señal {signum}). No terminaré aún.")
    signal_count+=1
    
# Asociamos la señal SIGINT al manejador
signal.signal(signal.SIGINT, manejar_ctrl_c)

print("Programa en ejecución. Presioná Ctrl+C para probar...")
try:
    while signal_count<3:
        time.sleep(1)
        print("Esperando señal...")
    print("\nFinalizando...")
except KeyboardInterrupt:
    print(f"Señal SIGINT recibida un total de {signal_count} veces.")