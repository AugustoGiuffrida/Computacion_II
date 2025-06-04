## 1. ¿Qué son las señales y por qué son importantes?

### 1.1 Explicación teórica

En los sistemas operativos tipo UNIX y POSIX, **las señales** son un mecanismo fundamental de comunicación entre procesos (IPC, *Inter-Process Communication*). Representan **interrupciones asíncronas** que permiten a un proceso o al sistema notificar a otro sobre un evento. Son conceptualmente similares a las interrupciones en el hardware, pero ocurren en el espacio de usuario y son gestionadas por el kernel.

Las señales pueden ser **generadas por el sistema**, por ejemplo:
- Cuando un proceso comete una infracción (división por cero, acceso inválido a memoria, etc.)
- Cuando un usuario interrumpe manualmente un proceso (`Ctrl+C` → `SIGINT`)

También pueden ser **enviadas por otros procesos** mediante funciones del sistema (`kill`, `sigqueue`, etc.), para indicar eventos o coordinar actividades.

### 1.2 Características clave
- Son **asíncronas**: pueden ocurrir en cualquier momento.
- El proceso **no elige cuándo** recibe la señal, pero sí puede definir **cómo reaccionar** mediante manejadores (*signal handlers*).
- Algunas señales pueden ser **ignoradas o bloqueadas**, mientras que otras (como `SIGKILL` o `SIGSTOP`) no pueden ser interceptadas.

### 1.3 Clasificación de señales

**Síncronas**: están relacionadas con errores que ocurren dentro del propio proceso.
- Ej.: `SIGFPE` (error aritmético), `SIGSEGV` (violación de segmento)

**Asíncronas**: provienen del exterior del proceso.
- Ej.: `SIGINT` (interrupción de teclado), `SIGTERM` (terminación solicitada)

**Tiempo real (Real-time signals)**: ampliación de POSIX. Son numeradas secuencialmente a partir de `SIGRTMIN`, con entrega en orden garantizada y posibilidad de colas (a diferencia de señales clásicas que pueden perderse si llegan múltiples veces antes de ser manejadas).

---

### 1.4 Relevancia en sistemas concurrentes

En sistemas concurrentes, las señales son útiles para:
- Coordinar múltiples procesos.
- Interrumpir procesos bloqueados.
- Gestionar eventos externos sin *polling constante*.
- Implementar comunicación básica sin recursos compartidos complejos.

Sin embargo, requieren un diseño cuidadoso: **los manejadores deben ser rápidos y seguros**, ya que interrumpen el flujo normal del programa, incluso en secciones críticas.

---

## 2. `signal.signal()` y funciones relacionadas en Python

### 2.1 Explicación teórica

Python expone una interfaz al sistema de señales POSIX a través del módulo estándar `signal`. Este módulo permite:

- Definir funciones personalizadas que se ejecutan al recibir una señal.
- Enviar señales a procesos.
- Bloquear, ignorar o manejar señales específicas.

La función central es `signal.signal(sig, handler)`, donde:

- `sig` es la constante que identifica la señal (por ejemplo, `signal.SIGINT`, `signal.SIGTERM`, etc.).
- `handler` puede ser:
  - Una función definida por el usuario.
  - `signal.SIG_IGN` para ignorar la señal.
  - `signal.SIG_DFL` para usar el comportamiento por defecto.

**Importante:** los manejadores de señal deben ser **lo más simples posible**, ya que son ejecutados en contexto asíncrono (es decir, pueden interrumpir cualquier parte del código en ejecución).

Otras funciones útiles del módulo `signal` incluyen:
- `signal.raise_signal(sig)`: envía una señal al proceso actual.
- `signal.getsignal(sig)`: devuelve el manejador actual de la señal.
- `signal.pause()`: bloquea la ejecución hasta recibir una señal.

---

### 2.2 Instrucciones prácticas paso a paso

1. Importar el módulo:
   ```python
   import signal
   import os
   import time
   ```

2. Definir un manejador para una señal:
   ```python
   def manejador_sigint(signum, frame):
       print(f"Señal recibida: {signum} (SIGINT)")
   ```

3. Registrar el manejador con `signal.signal()`:
   ```python
   signal.signal(signal.SIGINT, manejador_sigint)
   ```

4. Mantener el proceso vivo para permitir la señal:
   ```python
   print("Presioná Ctrl+C para enviar SIGINT...")
   while True:
       time.sleep(1)
   ```

---

### 2.3 Ejemplo de código comentado

```python
import signal
import time

# Definimos el manejador
def manejar_ctrl_c(signum, frame):
    print(f"Interrupción detectada (señal {signum}). No terminaré aún.")
    
# Asociamos la señal SIGINT al manejador
signal.signal(signal.SIGINT, manejar_ctrl_c)

print("Programa en ejecución. Presioná Ctrl+C para probar...")
while True:
    time.sleep(2)
    print("Esperando señal...")
```

Este programa ignora el comportamiento habitual de `Ctrl+C` (SIGINT) y ejecuta el manejador en su lugar.

### 2.4 Ejercicios prácticos

**Nivel básico**: Modificá el ejemplo anterior para que también maneje `SIGTERM` e imprima un mensaje diferente.

**Nivel medio**: Escribí un programa que registre dos señales (`SIGINT` y `SIGUSR1`) con manejadores distintos, y que permita enviar `SIGUSR1` desde otro proceso usando `kill`.

**Nivel avanzado**: Creá un programa que registre señales, y que luego de recibir 3 `SIGINT`, termine el proceso de forma segura (como una especie de protección contra cierre accidental).

---

## 3. `kill`, `sigqueue` y `sigaction` (referencia cruzada con C si es útil)

### 3.1 Explicación teórica

En sistemas UNIX y POSIX, las señales pueden enviarse entre procesos mediante llamadas al sistema. Las más utilizadas son:

- **`kill(pid, sig)`**: envía una señal `sig` al proceso con ID `pid`. Es importante notar que *no necesariamente termina* el proceso, a menos que la señal tenga ese efecto por defecto y no sea manejada.

- **`sigqueue(pid, sig, value)`**: permite enviar señales con información adicional (estructura `sigval`). Se usa solo con señales en el rango de *tiempo real* (`SIGRTMIN` a `SIGRTMAX`). No está disponible directamente en Python, pero puede usarse desde C o a través de bindings como `ctypes`.

- **`sigaction()`** (en C): permite un control más detallado sobre el manejo de señales que `signal()`, incluyendo opciones como:
  - Recibir información detallada (`siginfo_t`) sobre la señal.
  - Controlar máscaras de bloqueo.
  - Configurar flags como `SA_RESTART` o `SA_SIGINFO`.

En Python, `signal.signal()` es un envoltorio simplificado que oculta estos detalles.

---

### 3.2 Instrucciones prácticas paso a paso: usar `kill` desde la terminal

1. Abrí una terminal con el programa en ejecución (por ejemplo, el del ejercicio 2).
2. Obtené su PID con `ps` o `pgrep`, o directamente desde el programa (`os.getpid()`).
3. Enviá la señal con:

   ```bash
   kill -SIGUSR1 <PID>
   ```

4. Observá cómo el programa maneja la señal sin finalizar.

**Nota**: El comando `kill` también puede enviar `SIGINT`, `SIGTERM`, `SIGKILL`, etc., lo cual es útil para simular distintos eventos en un entorno controlado.

---

### 3.3 Comparación con C (breve)

En C, enviar y manejar señales es más explícito y requiere definir estructuras específicas. Ejemplo mínimo:

```c
#include <signal.h>
#include <stdio.h>
#include <unistd.h>

void manejador(int sig) {
    printf("Señal %d recibida\n", sig);
}

int main() {
    signal(SIGINT, manejador);
    while (1) {
        pause(); // Espera señal
    }
}
```

Para usar `sigaction` en C:

```c
struct sigaction sa;
sa.sa_handler = manejador;
sigemptyset(&sa.sa_mask);
sa.sa_flags = 0;
sigaction(SIGINT, &sa, NULL);
```

Esto permite, por ejemplo, bloquear otras señales mientras se maneja una.

---

### 3.4 Ejercicios prácticos

**Nivel básico**: Enviá señales manualmente a tu programa desde otra terminal usando `kill`.

**Nivel medio**: Modificá tu código para que muestre el PID al inicio y espere una señal de terminación (`SIGTERM`), donde se despida antes de cerrar.

**Nivel avanzado**: Si te interesa trabajar con `sigqueue` o `sigaction` desde Python, podríamos usar `ctypes`, pero esto requiere comprender estructuras C y acceso a funciones de la libc. Si querés, lo dejamos para un módulo posterior.

---

### Reflexioná:

1. ¿Qué diferencia clave hay entre `kill` y `sigqueue`?
2. ¿Por qué en Python usamos `signal.signal()` en lugar de `sigaction()`?
3. ¿Qué ventajas te da `sigaction()` en C respecto a `signal()`?

---

## 4. Uso de señales para sincronizar procesos

### 4.1 Explicación teórica

La **sincronización entre procesos** es crucial cuando múltiples procesos deben coordinar acciones, como esperar una señal antes de continuar, responder a un evento externo, o terminar de manera ordenada.

Las señales proporcionan un mecanismo **ligero, asíncrono y unidireccional** para lograr esto. Algunos escenarios típicos:

- Un proceso padre notifica a un hijo que puede continuar (`SIGUSR1`).
- Un proceso hijo notifica al padre que ha terminado (`SIGCHLD`).
- Dos procesos cooperativos se sincronizan mediante señales personalizadas (`SIGUSR1`, `SIGUSR2`).

**Ventaja principal**: no requieren recursos compartidos explícitos (memoria compartida, semáforos).

**Desventaja principal**: solo permiten comunicación básica (notificación), no el intercambio de datos complejos, y pueden ser interrumpidas o perdidas (salvo las de tiempo real).

---

### 4.2 Instrucciones prácticas paso a paso

1. Crear un **proceso padre** que cree un hijo con `os.fork()`.
2. El proceso hijo se queda esperando una señal con `signal.pause()`.
3. El proceso padre duerme unos segundos, luego envía una señal al hijo con `os.kill(pid_hijo, signal.SIGUSR1)`.
4. El hijo, al recibir la señal, imprime un mensaje y termina.

---

### 4.3 Ejemplo de código comentado

```python
import os
import signal
import time

# Manejador en el hijo
def recibir_orden(signum, frame):
    print(f"Hijo: Señal {signum} recibida. Comenzando ejecución...")

# Configuramos el manejador
signal.signal(signal.SIGUSR1, recibir_orden)

# Creamos proceso hijo
pid = os.fork()

if pid == 0:
    # Código del hijo
    print(f"Hijo: Esperando señal del padre. PID: {os.getpid()}")
    signal.pause()
    print("Hijo: Terminando.")
else:
    # Código del padre
    print(f"Padre: Enviando señal a hijo ({pid}) en 3 segundos...")
    time.sleep(3)
    os.kill(pid, signal.SIGUSR1)
    os.wait()  # Esperamos a que termine el hijo
    print("Padre: Hijo finalizado.")
```

---

### 4.4 Ejercicios prácticos

**Nivel básico**: Reescribí este ejemplo para que el padre espere dos hijos y les envíe señales por separado.

**Nivel medio**: Agregá una lógica en el hijo que solo comience su trabajo si recibe `SIGUSR1`, pero que termine prematuramente si recibe `SIGTERM`.

**Nivel avanzado**: Creá un programa maestro que maneje múltiples procesos hijos y los coordine con señales y estado compartido (por ejemplo, mediante pipes o archivos temporales).

---

### Preguntas para reflexionar:

1. ¿Cuál es la ventaja de usar `signal.pause()` en el hijo?
2. ¿Qué ocurre si el padre envía la señal antes de que el hijo registre el manejador?
3. ¿Cómo podrías evitar una pérdida de señal en una aplicación real?

---

## 5. Manejo seguro de señales y async-signal-safe

### 5.1 Explicación teórica

En sistemas operativos POSIX, **no todas las funciones son seguras para ser llamadas desde un manejador de señales**. Esto se debe a que, al recibir una señal, se interrumpe el flujo de ejecución normal del proceso, lo que puede llevar a estados inconsistentes si el manejador llama funciones que no están preparadas para operar en ese contexto asíncrono.

Estas funciones seguras se denominan **async-signal-safe functions**, y están definidas por el estándar POSIX como funciones que pueden ser invocadas con seguridad dentro de un manejador de señal. Entre las funciones **seguras** están:

- `write()`, `read()`
- `exit()`, `_exit()`
- `kill()`, `sigaction()`
- `signal()`
- Algunas manipulaciones simples de memoria como `memset()`, `memcmp()`

Funciones **no seguras** incluyen:

- `printf()`, `malloc()`, `free()`
- `open()`, `fopen()`
- Cualquier función que modifique estructuras internas del sistema de librerías (como buffers o heap)

**¿Por qué importa esto en Python?**  
Aunque Python gestiona internamente señales con mecanismos más seguros que en C, el interprete sigue estando expuesto a los mismos riesgos subyacentes del sistema. Por eso, se recomienda que el manejador solo haga tareas **mínimas**, y delegue el trabajo real a otra parte del programa.

---

### 5.2 Instrucciones prácticas paso a paso

1. Dentro del manejador, **evitá funciones complejas o que impliquen I/O**.
2. Si necesitás reaccionar con lógica más avanzada, usá una **variable global como bandera** y evaluála en el cuerpo principal del programa.
3. Si necesitás I/O desde un manejador (por ejemplo, salida a consola), usá `os.write()` en lugar de `print()`.

---

### 5.3 Ejemplo de código con práctica segura

```py
import signal
import os
import time

bandera_senal = False

def manejador_seguro(signum, frame):
    global bandera_senal
    bandera_senal = True
    # Evitar print() aquí — usamos write()
    os.write(1, b"[Manejador]: Señal capturada de forma segura.\n")

# Asociar señal
signal.signal(signal.SIGUSR1, manejador_seguro)

print(f"PID del proceso: {os.getpid()}. Enviá SIGUSR1 para probar.")

while True:
    time.sleep(1)
    if bandera_senal:
        print("[Principal]: Se detectó la señal, ejecutando tarea.")
        bandera_senal = False
```

---

### 5.4 Ejercicios prácticos

**Nivel básico**: Modificá este ejemplo para manejar `SIGINT` y que el programa termine de forma controlada al recibirla 3 veces.

**Nivel medio**: Implementá un sistema donde el manejador no haga más que escribir en un pipe anónimo, y el cuerpo principal lea desde el pipe para ejecutar acciones.

**Nivel avanzado**: Investigá y usá la función `sigaction()` desde C (o vía `ctypes` en Python) para definir un manejador robusto que utilice `siginfo_t`.

---

### Reflexiona

1. ¿Por qué `print()` no debe usarse dentro de un manejador de señales?
2. ¿Cuál es la diferencia entre `exit()` y `_exit()` desde un manejador?
3. ¿Qué técnicas permite Python para mitigar las limitaciones de los manejadores?

Te recomiendo discutir estas preguntas en clase y confirmar con tu profesor si en futuras prácticas será necesario usar `sigaction`.

Perfecto, avancemos.

---

## 6. Señales en Sistemas Multihilo

### 6.1 Explicación teórica

En un sistema **multihilo** (o multithreaded), la gestión de señales se complica, porque **la señal se entrega al proceso**, pero debe ser recibida **por un hilo específico**. En sistemas POSIX, esto tiene reglas estrictas:

#### Comportamiento por defecto:
- Las señales dirigidas al **proceso** (por ejemplo, con `kill(pid, SIGUSR1)`) pueden ser entregadas **a cualquier hilo que no tenga esa señal bloqueada**.
- Las señales generadas **por errores sincrónicos** (como `SIGFPE`, `SIGSEGV`) se entregan al hilo que causó el error.
- Los hilos pueden **bloquear o desbloquear** señales individualmente mediante `pthread_sigmask()` (en C).

En **Python**, la situación es simplificada por el intérprete:  
- **Solo el hilo principal** puede recibir señales y ejecutar manejadores.
- Los hilos secundarios no ejecutan manejadores de señales directamente.

Esto implica que, si tu aplicación Python usa `threading`, **solo el hilo principal puede registrar y manejar señales**.

---

### 6.2 Instrucciones prácticas paso a paso

1. Usá `signal.signal()` únicamente en el **hilo principal**.
2. Para que un hilo secundario reaccione a una señal, el manejador debe modificar un **estado compartido** (una variable global, una `queue`, un `Event`, etc.).
3. El hilo secundario debe monitorear ese estado y actuar en consecuencia.

---

### 6.3 Ejemplo de código comentado

Este ejemplo usa `threading` y `signal` para mostrar cómo el **hilo principal captura la señal**, y un **hilo trabajador reacciona** a ella usando una variable compartida.

```py
import signal
import threading
import time

bandera_evento = threading.Event()

def manejador(signum, frame):
    print(f"[Hilo principal] Señal {signum} recibida.")
    bandera_evento.set()

def hilo_trabajador():
    print("[Hilo trabajador] Esperando evento...")
    while not bandera_evento.is_set():
        print("[Hilo trabajador] Trabajando normalmente...")
        time.sleep(1)
    print("[Hilo trabajador] Evento recibido, cerrando...")

# Solo el hilo principal debe registrar el manejador
signal.signal(signal.SIGUSR1, manejador)

# Iniciar hilo secundario
t = threading.Thread(target=hilo_trabajador)
t.start()

print(f"[Principal] PID: {os.getpid()}. Enviá SIGUSR1 para activar el evento.")
t.join()
print("[Principal] Programa finalizado.")
```

---

### 6.4 Ejercicios prácticos

**Nivel básico**:  
Usá un `threading.Event()` como bandera para que el hilo trabajador se detenga luego de recibir `SIGINT` tres veces.

**Nivel medio**:  
Combiná `threading` y `multiprocessing`: usá un `multiprocessing.Process` con varios `threading.Thread`, y controlá el inicio de los hilos desde el manejador del proceso padre.

**Nivel avanzado**:  
Investigá `pthread_sigmask()` en C. Implementá un programa con múltiples hilos donde solo uno esté habilitado para recibir señales (`sigwait()`).

---

### Reflexiona

1. ¿Qué hilo puede recibir señales en Python?
2. ¿Qué mecanismo usarías para comunicar la señal a otros hilos?
3. ¿Por qué no deberías llamar `signal.signal()` desde un hilo secundario?

---

## 7. Comparación: Señales vs Otros Mecanismos de IPC

### 7.1 Explicación teórica

En sistemas operativos, existen varios mecanismos de **comunicación entre procesos (IPC, *Inter-Process Communication*)**. Cada uno tiene ventajas y limitaciones dependiendo del **tipo de interacción**, **nivel de complejidad**, **sincronización requerida** y **rendimiento**.

A continuación, comparamos las **señales** con los mecanismos más usados:

#### Señales (`signal`)
- **Naturaleza**: Asíncronas.
- **Propósito**: Notificar eventos (como interrupciones, errores o eventos externos).
- **Datos**: Generalmente *no transmiten datos* (excepto señales de tiempo real, e.g., `sigqueue`).
- **Velocidad**: Muy rápida.
- **Dirección**: Unidireccional (del kernel o de un proceso a otro).
- **Uso típico**: Detener, pausar o notificar a procesos.

#### Pipes y Named Pipes (`pipe`, `mkfifo`)
- **Naturaleza**: Flujo de bytes.
- **Propósito**: Transmisión de datos entre procesos con relación padre-hijo (pipes) o entre procesos independientes (named pipes).
- **Datos**: Sí transmiten datos.
- **Sincronización**: Implícita (lectura bloquea si no hay datos).
- **Dirección**: Unidireccional o bidireccional (con dos pipes).
- **Uso típico**: Envío de mensajes o datos secuenciales.

#### Sockets
- **Naturaleza**: Basados en red o local (UNIX domain sockets).
- **Propósito**: Comunicación en red o entre procesos locales.
- **Datos**: Sí.
- **Sincronización**: Debe ser manejada por el programa.
- **Dirección**: Bidireccional.
- **Uso típico**: Aplicaciones cliente-servidor, procesos distribuidos.

#### Memoria compartida (`shm`, `mmap`)
- **Naturaleza**: Acceso directo a memoria común.
- **Propósito**: Alta velocidad de intercambio.
- **Datos**: Sí.
- **Sincronización**: Requiere mecanismos adicionales (semaforos, mutex).
- **Dirección**: Bidireccional.
- **Uso típico**: Grandes volúmenes de datos, eficiencia extrema.

#### Señales vs otros:
| Mecanismo          | Asíncrono | Transfiere datos | Configuración | Rendimiento | Ideal para               |
|--------------------|-----------|------------------|---------------|-------------|--------------------------|
| Señales            | ✔️        | ❌ (excepto `sigqueue`) | Muy simple    | Alta        | Notificaciones simples   |
| Pipes              | ❌        | ✔️               | Media         | Media       | Comunicación secuencial  |
| Sockets            | ❌        | ✔️               | Compleja      | Variable    | Comunicación flexible    |
| Memoria compartida | ❌        | ✔️               | Alta          | Muy alta    | Volumen alto de datos    |

---

### 7.2 Aplicaciones prácticas

- Usá **señales** si solo querés notificar a un proceso que algo ocurrió.
- Usá **pipes** si necesitas pasar mensajes simples entre procesos relacionados.
- Usá **sockets** si los procesos están en diferentes máquinas o necesitas una arquitectura cliente-servidor.
- Usá **memoria compartida** si el rendimiento es crítico y podés manejar la sincronización.

---

### 7.3 Ejemplo simple: combinación de señal + pipe

En este ejemplo, un proceso envía una señal para notificar, y luego usa un pipe para enviar datos:

```py
import os
import signal
import time

# Creamos el pipe
r, w = os.pipe()

def manejador(signum, frame):
    print("Padre: Señal recibida. Ahora leo del pipe...")
    msg = os.read(r, 100).decode()
    print(f"Padre: Mensaje recibido: {msg}")
    os.close(r)

signal.signal(signal.SIGUSR1, manejador)

pid = os.fork()

if pid == 0:
    # Hijo escribe en el pipe y luego notifica
    os.close(r)
    os.write(w, b"Hola desde el hijo!")
    os.close(w)
    os.kill(os.getppid(), signal.SIGUSR1)
    os._exit(0)
else:
    print("Padre: Esperando señal...")
    signal.pause()
    os.waitpid(pid, 0)
```

Este patrón es útil cuando querés combinar **notificación rápida con transmisión de datos más ricos**.

---

### Reflexión

1. ¿Qué limitaciones tiene una señal frente a un pipe?
2. ¿Por qué es inseguro usar señales para enviar información estructurada?
3. ¿Cuál es el mecanismo más eficiente para transferir grandes cantidades de datos?

Recordá compartir este cuadro comparativo y ejemplo con tu profesor, especialmente si te pide justificar el uso de señales frente a otros IPC.

---

## 8. Señales de tiempo real (`SIGRTMIN`, `sigqueue`)

### 8.1 Explicación teórica

#### ¿Qué son las señales de tiempo real?

Las señales tradicionales (como `SIGINT`, `SIGTERM`, etc.) tienen ciertas **limitaciones**:

- Son limitadas en número.
- No pueden **encolarse**: si una señal se envía varias veces antes de ser manejada, solo una de ellas se procesa.
- No pueden **transportar información adicional** (salvo con extensiones).

Las **señales de tiempo real (real-time signals)**, introducidas en POSIX.1b, solucionan estos problemas:

- Se identifican por los nombres `SIGRTMIN`, `SIGRTMIN+1`, ..., hasta `SIGRTMAX`.
- **Son encolables**: si un proceso recibe varias señales antes de manejarlas, las conserva en orden.
- **Pueden llevar un valor adicional (entero)** al ser enviadas con `sigqueue()`.

#### Rango disponible

```c
#define SIGRTMIN 32
#define SIGRTMAX 64
```

Estos valores pueden variar entre sistemas; se recomienda usar `SIGRTMIN + N` en vez de hardcodear `34`, `35`, etc.

---

### 8.2 `sigqueue()` y `siginfo_t`

El sistema tradicional de envío de señales (`kill(pid, sig)`) no permite enviar datos. Para eso se usa `sigqueue()`.

**Prototipo en C**:
```c
int sigqueue(pid_t pid, int sig, const union sigval value);
```

- `pid`: proceso destino
- `sig`: número de señal (de tiempo real)
- `value`: unión que puede contener un entero o puntero (`value.sival_int`, `value.sival_ptr`)

Para recibir esa información, el manejador debe estar definido con `sigaction` y la bandera `SA_SIGINFO`.

---

### 8.3 ¿Qué soporte ofrece Python?

**Python estándar no expone directamente `sigqueue()` ni señales de tiempo real**. Para usarlas, necesitás emplear una biblioteca como `ctypes` o directamente implementarlo en C.

Por eso, esta sección incluye un ejemplo en **C**, que luego podés adaptar a un entorno mixto o estudiar para comprender el funcionamiento profundo.

---

### 8.4 Ejemplo completo en C: `sigqueue` y `SIGRTMIN`

```c
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <signal.h>
#include <string.h>

void manejador(int sig, siginfo_t *info, void *contexto) {
    printf("Padre: Señal %d recibida.\n", sig);
    printf("Valor recibido: %d\n", info->si_value.sival_int);
}

int main() {
    struct sigaction act;
    act.sa_sigaction = manejador;
    act.sa_flags = SA_SIGINFO;
    sigemptyset(&act.sa_mask);

    // Asociamos SIGRTMIN+1 al manejador
    sigaction(SIGRTMIN + 1, &act, NULL);

    pid_t pid = fork();

    if (pid == 0) {
        // Proceso hijo
        sleep(1);
        union sigval val;
        val.sival_int = 42;
        sigqueue(getppid(), SIGRTMIN + 1, val);
        exit(0);
    } else {
        pause();  // Espera señal
    }

    return 0;
}
```

Este programa crea un proceso hijo que **envía una señal de tiempo real con un valor entero** al padre usando `sigqueue`. El padre, con un manejador extendido, imprime ese valor.

---

### 8.5 Puesta en común con la clase

1. ¿Qué ventajas ofrece `sigqueue` frente a `kill`?
2. ¿Cuál es la principal diferencia entre señales tradicionales y señales de tiempo real?
3. ¿Por qué Python no soporta `sigqueue()` de forma directa?

Te recomiendo discutir esta implementación con tu profesor o grupo si estás trabajando en tareas donde la **comunicación rica entre procesos** es necesaria.
