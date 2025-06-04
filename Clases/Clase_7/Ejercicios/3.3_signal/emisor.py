import ctypes
import ctypes.util
import os
import sys

libc = ctypes.CDLL(ctypes.util.find_library("c"))

# union sigval (simplificado para enviar int)
class SigVal(ctypes.Union):
    _fields_ = [("sival_int", ctypes.c_int), ("sival_ptr", ctypes.c_void_p)]

# Comprobar argumentos
if len(sys.argv) != 3:
    print("Uso: python emisor.py <PID> <valor>")
    sys.exit(1)

pid = int(sys.argv[1])
valor = int(sys.argv[2])

sigval = SigVal()
sigval.sival_int = valor

# Enviar la señal con sigqueue
res = libc.sigqueue(pid, 10, sigval)  # 10 = SIGUSR1
if res != 0:
    print("Error al enviar señal")
else:
    print(f"Señal SIGUSR1 enviada a {pid} con valor {valor}")
