import ctypes
import ctypes.util
import os
import time

# Cargar la libc
libc = ctypes.CDLL(ctypes.util.find_library("c"))

# Constantes
SIGUSR1 = 10

# Estructura siginfo_t simplificada (solo el campo si_value.int)
class SigInfo(ctypes.Structure):
    _fields_ = [
        ("si_signo", ctypes.c_int),
        ("si_errno", ctypes.c_int),
        ("si_code", ctypes.c_int),
        ("si_pid", ctypes.c_int),
        ("si_uid", ctypes.c_uint),
        ("si_status", ctypes.c_int),
        ("si_value", ctypes.c_int),  # parte del union sigval
    ]

# Estructura de sigaction
class SigAction(ctypes.Structure):
    _fields_ = [
        ("sa_sigaction", ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.POINTER(SigInfo), ctypes.c_void_p)),
        ("sa_flags", ctypes.c_int),
        ("sa_restorer", ctypes.c_void_p),
        ("sa_mask", ctypes.c_ulong * 16),  # sigset_t simplificado
    ]

# Manejador en Python
@ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.POINTER(SigInfo), ctypes.c_void_p)
def handler(signum, info, context):
    print(f"Recibido SIGUSR1 con valor: {info.contents.si_value}")

# Configurar sigaction
action = SigAction()
action.sa_sigaction = handler
action.sa_flags = 4  # SA_SIGINFO

# Registrar el handler
libc.sigaction(SIGUSR1, ctypes.byref(action), None)

print(f"Receptor listo. PID = {os.getpid()}")
while True:
    time.sleep(1)
