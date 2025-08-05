# Resumen

# Pipes

## ¿Qué es un pipe?

Un pipe (o "tubería") es un mecanismo de comunicación unidireccional entre procesos que permite que la salida de un proceso se utilice como entrada de otro. Su uso está muy relacionado con el principio de composición de procesos, común en sistemas UNIX y Linux.

## Características principales
- Comunicación unidireccional: un extremo escribe, el otro lee.
- Los pipes tradicionales (anónimos) solo funcionan entre procesos con un ancestro común (por ejemplo, padre-hijo).
- Existe también la variante named pipe (FIFO), que permite comunicación entre procesos no relacionados directamente.

## Implementación de Pipes en Python

Para trabajar con pipes en Python, se puede usar:

- `os.pipe()`: para crear pipes de bajo nivel, similar a C.
- `multiprocessing.Pipe()`: para comunicación entre procesos usando la librería multiprocessing.

## Paso a paso con os.pipe()

1. Crear el pipe
    ```py
    import os

    r, w = os.pipe()  # r: descriptor de lectura, w: descriptor de escritura

        Bifurcar el proceso

    pid = os.fork()
    ```

2. Gestionar extremos según el proceso
    ```py
    if pid == 0:
        # Proceso hijo (escribe)
        os.close(r)  # Cierra lectura
        w_fd = os.fdopen(w, 'w')  # Abre descriptor como archivo para escribir
        w_fd.write("Hola desde el hijo\n")
        w_fd.close()
    else:
        # Proceso padre (lee)
        os.close(w)  # Cierra escritura
        r_fd = os.fdopen(r)  # Abre descriptor como archivo para leer
        print("Padre lee:", r_fd.read())
        r_fd.close()
    ```

>📌 Este ejemplo ilustra la comunicación unidireccional clásica entre un padre que lee y un hijo que escribe. La sincronización implícita ocurre porque read() bloquea hasta que el hijo termina de escribir y cierra el descriptor.

## Pipeline

Un pipeline es cuando la salida de un proceso se conecta como entrada del siguiente, tal como en:
```bash
ls | grep ".py" | sort
```
Vamos a replicar algo similar en Python: tres procesos que simulan este encadenamiento.

📄 **Ejemplo: pipeline de 3 procesos**

Objetivo: Proceso A genera datos → Proceso B los transforma → Proceso C los muestra

```py
import os

# Creamos dos pipes: A->B y B->C
r1, w1 = os.pipe()  # Pipe entre A y B
r2, w2 = os.pipe()  # Pipe entre B y C

pid_a = os.fork()
if pid_a == 0:
    # Proceso A (escribe al pipe1)
    os.close(r1)
    os.close(r2)
    os.close(w2)
    w1_fd = os.fdopen(w1, 'w')
    w1_fd.write("uno\ndos\ntres\n")
    w1_fd.close()
    exit()

pid_b = os.fork()
if pid_b == 0:
    # Proceso B (lee de pipe1, escribe en pipe2)
    os.close(w1)
    os.close(r2)
    r1_fd = os.fdopen(r1)
    w2_fd = os.fdopen(w2, 'w')
    for line in r1_fd:
        w2_fd.write(line.upper())  # Transforma a mayúsculas
    r1_fd.close()
    w2_fd.close()
    exit()

# Proceso C (padre)
os.close(w1)
os.close(w2)
os.close(r1)
r2_fd = os.fdopen(r2)
print("Proceso C recibe:")
for line in r2_fd:
    print(line.strip())
r2_fd.close()
```

---

# FIFOs en Sistemas Unix/Linux: Fundamentos, Implementación y Aplicaciones Avanzadas

## Introducción

En el ecosistema Unix/Linux, los mecanismos de comunicación entre procesos (IPC, por sus siglas en inglés) constituyen una piedra angular del diseño de sistemas operativos robustos y eficientes. Entre estos mecanismos, los *FIFOs* (First-In-First-Out), también conocidos como *named pipes*, ofrecen una forma elegante y persistente de intercambio de datos unidireccional o bidireccional entre procesos no emparentados. Este documento aborda en profundidad el modelo FIFO, desde su fundamentación teórica y evolución histórica hasta su implementación en el kernel, acompañado de ejemplos prácticos y análisis comparativos.

## 2. Fundamentos Teóricos

### 2.1 Comunicación entre procesos: panorama general

La comunicación entre procesos es necesaria para lograr cooperación, coordinación y compartición de información. Unix ofrece diversos mecanismos: pipes anónimos y FIFOs. La elección depende de factores como persistencia, necesidad de bloqueo, estructura de datos y requisitos de sincronización.

### 2.2 El modelo FIFO: principios y características

Un FIFO es un archivo especial que actúa como canal de comunicación. Su característica principal es que el primer byte escrito es el primero en ser leído, garantizando un orden de llegada (semántica FIFO). A diferencia de un pipe anónimo, un FIFO tiene una entrada en el sistema de archivos, lo que lo hace accesible por procesos no relacionados y persistente entre ejecuciones.

## 3. Contexto Histórico

### 3.1 Evolución de los mecanismos IPC en sistemas Unix

Los primeros sistemas Unix (Bell Labs, década de 1970) incorporaban *pipes* como mecanismos de comunicación unidireccional entre procesos relacionados. Sin embargo, esto limitaba su aplicabilidad. Con la introducción de los *named pipes* en System III y posteriormente System V, se amplió el paradigma IPC a procesos disociados, permitiendo arquitecturas más flexibles.

### 3.2 De pipes anónimos a named pipes

Mientras los pipes anónimos requieren herencia del descriptor de archivo (normalmente vía fork), los FIFOs pueden ser accedidos por cualquier proceso con los permisos adecuados. Esta independencia favoreció diseños más desacoplados y modulares.

## 4. Arquitectura Interna

### 4.1 Implementación a nivel de kernel

El kernel trata los FIFOs como archivos especiales con semántica de buffer circular. Están asociados a una estructura `inode` y gestionan la cola de bytes mediante `pipe_inode_info`. Internamente, usan mecanismos de sincronización como *wait queues* para gestionar la espera de procesos lectores y escritores. Los accesos se coordinan para evitar condiciones de carrera.

### 4.2 Estructuras de datos y buffers

Los FIFOs utilizan una región de memoria en el espacio del kernel para almacenar los datos temporalmente. Su tamaño suele ser configurable a nivel de sistema (`/proc/sys/fs/pipe-max-size`) y se implementa como una cola circular. Esta estructura permite evitar copias innecesarias y reducir la latencia.

### 4.3 Sincronización y bloqueo

Si un proceso intenta leer un FIFO vacío, quedará bloqueado hasta que haya datos. Igualmente, un proceso que escribe puede ser bloqueado si no hay lectores. Alternativamente, pueden usarse las flags `O_NONBLOCK` para evitar esta espera. El kernel sincroniza ambos extremos y administra correctamente los estados de espera.

## 5. Operaciones Fundamentales

### 5.1 Creación de FIFOs

La llamada al sistema `mkfifo(const char *pathname, mode_t mode)` o el comando `mkfifo` permite crear un FIFO persistente:

```bash
$ mkfifo /tmp/mi_fifo
```

Este archivo especial puede ser abierto por múltiples procesos para escritura o lectura.

### 5.2 Mecanismos de lectura y escritura (modo bajo nivel con `os`)

La lectura y escritura en un FIFO puede realizarse no solo con la función `open()` de alto nivel en Python, sino también utilizando la librería `os`, que permite trabajar con descriptores de archivo y banderas POSIX de forma más cercana al sistema operativo. Esto es útil cuando se requiere control fino sobre bloqueo, apertura no bloqueante, o tratamiento explícito de errores.

---

### Ejemplo básico con `os.open`, `os.read`, `os.write`

Antes de ejecutar estos scripts, crear el FIFO desde terminal:

```bash
mkfifo /tmp/mi_fifo
```

#### Escritura:
```python
# escribir_fifo_os.py
import os
import time

fd = os.open('/tmp/mi_fifo', os.O_WRONLY)
os.write(fd, b'Hola desde os.write\n')
os.close(fd)
```

#### Lectura:
```python
# leer_fifo_os.py
import os

fd = os.open('/tmp/mi_fifo', os.O_RDONLY)
data = os.read(fd, 1024)
print('Lectura:', data.decode())
os.close(fd)
```

---

### Control de bloqueo con `O_NONBLOCK`

Con `O_NONBLOCK`, es posible evitar que el proceso quede bloqueado si no hay otro extremo abierto todavía.

```python
# lector_no_block.py
import os
import errno
import time

try:
    fd = os.open('/tmp/mi_fifo', os.O_RDONLY | os.O_NONBLOCK)
    data = os.read(fd, 1024)
    print('Leído:', data.decode() if data else '[sin datos]')
    os.close(fd)
except OSError as e:
    if e.errno == errno.ENXIO:
        print('No hay escritor disponible aún.')
```

---

### Comportamiento del cursor y consumo de datos

A diferencia de un archivo tradicional, en un FIFO **los datos se consumen en la lectura**. Esto significa que **no pueden ser leídos nuevamente por otro proceso**, aunque cada uno tenga su propio descriptor de archivo.

Ejemplo:

```bash
mkfifo /tmp/fifo_cursor_os
```

```python
# escribir_fifo_cursor_os.py
import os

fd = os.open('/tmp/fifo_cursor_os', os.O_WRONLY)
os.write(fd, b'ABCDEF')
os.close(fd)
```

```python
# lector_1_os.py
import os

fd = os.open('/tmp/fifo_cursor_os', os.O_RDONLY)
print('Lector 1 lee:', os.read(fd, 3).decode())  # ABC
os.close(fd)
```

```python
# lector_2_os.py
import os

fd = os.open('/tmp/fifo_cursor_os', os.O_RDONLY)
print('Lector 2 lee:', os.read(fd, 3).decode())  # DEF o vacío si ya se consumió
os.close(fd)
```

> Como los datos ya fueron consumidos por el primer lector, el segundo proceso lee solo los restantes, o nada si el buffer ya se vació. Esto demuestra que en un FIFO los datos **no persisten** y el **acceso es secuencial y destructivo**.

---

Este modo de trabajo con `os` y descriptores de archivo es fundamental para aplicaciones que requieren operaciones sin bloqueo, multiplexado con `select()`, o integración con estructuras de bajo nivel del sistema operativo.

### 5.3 Llamadas del sistema relacionadas

- `open()`
- `read()` / `write()`
- `close()`
- `mkfifo()`
- `select()` / `poll()` (para detección de disponibilidad)

## 6. Patrones de Implementación

### 6.1 Modelo productor-consumidor

Uno o más procesos escriben datos que otros procesos consumen. La FIFO garantiza orden y aislamiento entre productores y consumidores. El buffer interno actúa como zona crítica.

### 6.2 Comunicación unidireccional

Un FIFO puede ser leído por un proceso y escrito por otro. Ideal para flujos de datos simples donde no se necesita respuesta.

### 6.3 Comunicación bidireccional

Se crea un par de FIFOs (ej: `/tmp/fifo_in`, `/tmp/fifo_out`) para lograr ida y vuelta, replicando un canal de duplexidad básica. Se requiere cuidado para evitar deadlocks.

## 7. Comparativa con Otros Mecanismos IPC

### 7.1 FIFOs vs Pipes anónimos

| Característica     | FIFO                   | Pipe anónimo            |
|--------------------|------------------------|--------------------------|
| Persistencia       | Sí                     | No                       |
| Acceso             | Procesos no relacionados | Solo procesos relacionados |
| Ubicación          | Sistema de archivos    | Descriptores de archivo  |
| Supervisión externa| Posible con `ls`, `stat`| No visible               |

## 8. Análisis de Rendimiento

### 8.1 Factores que afectan la latencia

- Tamaño del buffer FIFO
- Frecuencia de lectura/escritura
- Prioridad y afinidad de los procesos
- Carga del sistema y contenido del buffer

### 8.2 Consideraciones sobre el throughput

La transferencia sostenida depende de la eficiencia del buffer y el scheduler de procesos. El uso de `select()` o `poll()` puede optimizar la disponibilidad de lectura sin bloqueo activo.

### 8.3 Limitaciones y tamaño de buffer

El tamaño máximo está limitado por la configuración del sistema. El uso excesivo puede llevar a cuellos de botella si los consumidores no vacían la cola con suficiente rapidez.

## 9. Implementaciones Prácticas

### 9.1 Comunicación básica entre procesos

```python
# escritor.py
with open('/tmp/canal', 'w') as fifo:
    fifo.write('Mensaje enviado\n')
```

```python
# lector.py
with open('/tmp/canal', 'r') as fifo:
    print('Receptor:', fifo.readline())
```

### 9.2 Implementación de un sistema de log

```python
# logger.py
with open('/tmp/log_fifo', 'r') as fifo, open('registro.log', 'a') as log:
    for line in fifo:
        log.write(line)
```


---

# Queues (multiprocessing)

Instrucciones detalladas para implementar Queues en Python
En Python, la forma más común y segura de usar Queues para comunicación entre procesos es a través del módulo multiprocessing. Este módulo abstrae muchos detalles complejos y permite una implementación clara y eficiente.

## Herramienta principal: multiprocessing.Queue
Este objeto actúa como una cola de mensajes compartida entre procesos. Internamente utiliza un pipe y mecanismos de sincronización para garantizar la seguridad de los datos.

## Estructura básica
```py
from multiprocessing import Process, Queue

def productor(queue):
    for i in range(5):
        queue.put(f"Dato {i}")
        print(f"Productor puso: Dato {i}")

def consumidor(queue):
    while not queue.empty():
        dato = queue.get()
        print(f"Consumidor recibió: {dato}")

if __name__ == "__main__":
    q = Queue()

    p1 = Process(target=productor, args=(q,))
    p2 = Process(target=consumidor, args=(q,))

    p1.start()
    p1.join()  # Esperamos a que termine de poner datos

    p2.start()
    p2.join()  # Esperamos a que consuma todo
```

**Detalles importantes:**
- queue.put(dato) añade un elemento.
- queue.get() lo extrae.
- queue.empty() comprueba si la cola está vacía (aunque no es 100% confiable si hay concurrencia activa).
- join() espera a que el proceso termine.
- El código debe estar dentro del `if __name__ == "__main__"` para evitar problemas en Windows

# Pipe (multiprocessing)

La función `multiprocessing.Pipe()` en Python permite crear un **canal de comunicación bidireccional** entre dos procesos. Este canal se implementa mediante un par de **extremos conectados** llamados **conexiones** (`Connection` objects). Es útil cuando deseas que dos procesos (por ejemplo, un padre y su hijo) puedan intercambiar datos de forma directa.

## Funcionamiento general

Cuando invocas `multiprocessing.Pipe()`, se devuelve una **tupla con dos objetos** de tipo `Connection`, por ejemplo:

```python
conn1, conn2 = multiprocessing.Pipe()
```

Ambos extremos del pipe permiten enviar y recibir datos usando los métodos:

* `send(obj)`: envía un objeto a través del pipe.
* `recv()`: recibe un objeto desde el otro extremo del pipe.

### Ejemplo básico

```python
from multiprocessing import Process, Pipe

def child(conn):
    conn.send("Mensaje desde el hijo")
    respuesta = conn.recv()
    print("Hijo recibió:", respuesta)

if __name__ == '__main__':
    parent_conn, child_conn = Pipe()

    p = Process(target=child, args=(child_conn,))
    p.start()

    print("Padre recibió:", parent_conn.recv())
    parent_conn.send("Hola hijo")
    p.join()
```

**Salida esperada:**

```
Padre recibió: Mensaje desde el hijo
Hijo recibió: Hola hijo
```

## Características importantes

* **Bidireccionalidad:** Por defecto, ambos extremos pueden enviar y recibir. Si deseas un pipe **unidireccional**, puedes pasar `duplex=False` al constructor, y entonces:

  * El primer extremo solo podrá **enviar**.
  * El segundo extremo solo podrá **recibir**.

  Ejemplo:

  ```python
  send_conn, recv_conn = Pipe(duplex=False)
  ```

* **Serialización automática:** Los objetos enviados por `send` se serializan usando `pickle`. Por tanto, puedes enviar cualquier objeto que sea "pickleable".

* **Bloqueo implícito:** Las operaciones `recv()` se bloquean hasta que se recibe algo. Para evitar bloqueos, podés usar `conn.poll(timeout)` para verificar si hay algo que leer.

### Comparación con `Queue`

Aunque `Pipe` es útil para **comunicación directa entre dos procesos**, para situaciones más complejas (por ejemplo, varios productores/consumidores) es preferible `multiprocessing.Queue()`, que es más flexible y está basada en colas seguras entre procesos.

Si necesitás un ejemplo específico de comunicación entre varios procesos usando `Pipe`, o querés ver cómo se diferencia internamente de otros mecanismos como `os.pipe()` o `Queue`, puedo ayudarte con eso también.

# Métodos de sincronización

## 1. Lock: El Guardián de la Exclusión Mutua

### 1.1. ¿Qué es y qué hace?
Un `Lock` (cerrojo o candado) es la primitiva de sincronización más fundamental. Su propósito es implementar la **exclusión mutua**, garantizando que solo **un proceso** pueda ejecutar una *sección crítica* (un bloque de código que accede a un recurso compartido) a la vez. Funciona como un interruptor binario: puede estar **adquirido (locked)** o **liberado (unlocked)**. Un proceso intenta adquirirlo con `acquire()`; si está libre, lo toma y entra en su sección crítica; si está ocupado, se bloquea hasta que se libere. Al salir, lo libera con `release()`. [cite: fileName: Sincronización en Python con multiprocessing]

### 1.2. ¿Cuándo usarlo? (Casos de Uso Prácticos)
Se usa siempre que se necesite asegurar que una operación o un conjunto de operaciones sobre un recurso compartido sean **atómicas**, es decir, que no sean interrumpidas por otro proceso que accede al mismo recurso.

* **Protección de Datos Compartidos**: Evitar condiciones de carrera al modificar variables, listas, diccionarios u otros objetos compartidos [cite: fileName: crash_problem.py].
* **Acceso Exclusivo a Recursos**: Garantizar que solo un proceso a la vez use un dispositivo (impresora, puerto serie) o escriba en un archivo.
* **Implementación de Primitivas**: Sirve como base para construir otras primitivas más complejas.

### 1.3. Consideraciones Técnicas Clave

* **Atomicidad de `acquire`/`release`**: Estas operaciones están garantizadas por el sistema operativo para ser atómicas.

* **`with` Statement**: Es la forma **recomendada** de usar `Lock`. Automáticamente llama a `acquire()` al entrar al bloque y a `release()` al salir, incluso si ocurren excepciones. Esto previene deadlocks por locks no liberados.

* **Deadlocks**: Es posible crear deadlocks si los procesos intentan adquirir múltiples locks en órdenes inconsistentes. La regla es: adquirir siempre los locks en el mismo orden global.

* **No Reentrante**: Un proceso *no puede* adquirir un `Lock` que ya posee; se bloqueará a sí mismo.

* **Contexto Histórico**: Deriva de los semáforos binarios de Dijkstra (1965) y es una implementación de los mutexes presentes en sistemas operativos modernos. `multiprocessing.Lock` usa primitivas del SO (semáforos POSIX o mutexes de Windows).

* **Implementación Subyacente**: `multiprocessing.Lock` utiliza semáforos POSIX en sistemas tipo Unix y objetos Mutex en Windows. Esto implica un cierto *overhead* por llamadas al sistema.

* **`acquire(blocking=True, timeout=-1)`**: Permite intentos de adquisición no bloqueantes (`blocking=False`) o con tiempo de espera (`timeout`).

### 1.4. Ejemplo Práctico (Contador Seguro)
```python
from multiprocessing import Process, Lock, Value
import time
import ctypes

def safe_increment(counter, lock):
    """ Incrementa un contador 10000 veces usando un Lock. """
    for _ in range(10000):
        with lock: # Adquiere y libera automáticamente
            temp = counter.value
            # time.sleep(0.0001) # Descomentar para ver más claramente el efecto sin lock
            counter.value = temp + 1

if __name__ == '__main__':
    shared_counter = Value(ctypes.c_int, 0)
    lock = Lock()
    
    p1 = Process(target=safe_increment, args=(shared_counter, lock))
    p2 = Process(target=safe_increment, args=(shared_counter, lock))

    p1.start()
    p2.start()
    p1.join()
    p2.join()

    print(f"Valor final (seguro con Lock): {shared_counter.value}") # Debería ser 20000
```
**Explicación**: El `with lock:` asegura que la secuencia lectura-modificación-escritura (`+=`) sea atómica, previniendo la condición de carrera y garantizando el resultado correcto. [cite: fileName: Sincronización en Python con multiprocessing]

### 1.5. Ejercicios

#### Ejercicio Propuesto: Log Concurrente
Escribe un programa donde 5 procesos intentan escribir mensajes en un único archivo de log (`log.txt`). Cada mensaje debe incluir el ID del proceso y una marca de tiempo. Usa un `Lock` para asegurar que las líneas de log no se mezclen y cada escritura sea completa.

#### Ejercicio Resuelto: Acceso Exclusivo a Archivo
```python
from multiprocessing import Process, Lock
import time
import os

def write_to_log_safe(lock, process_id, filename="log_safe.txt"):
    """ Adquiere el lock y escribe una línea en el archivo de log. """
    with lock:
        timestamp = time.ctime()
        pid = os.getpid()
        line = f"Proceso {process_id} (PID: {pid}) escribió a las {timestamp}\n"
        with open(filename, 'a') as f:
            print(f"Proceso {process_id} escribiendo...")
            f.write(line)
            time.sleep(0.1) # Simula I/O o trabajo dentro de la sección crítica
        print(f"Proceso {process_id} terminó de escribir.")

if __name__ == '__main__':
    log_filename = "log_safe.txt"
    if os.path.exists(log_filename): os.remove(log_filename) # Limpia el log anterior
    
    lock = Lock()
    processes = [Process(target=write_to_log_safe, args=(lock, i, log_filename)) for i in range(5)]
    
    for p in processes: p.start()
    for p in processes: p.join()
    
    print(f"\nContenido de {log_filename}:\n---")
    with open(log_filename, 'r') as f: print(f.read())
    print("---")
```
**Explicación**: El `with lock:` garantiza que cada proceso escriba su línea completa sin ser interrumpido, resultando en un archivo de log ordenado (aunque el orden entre procesos no está garantizado, cada *línea* está intacta).

---

## 2. RLock: El Lock Reentrante

### 2.1. ¿Qué es y qué hace?
Un `RLock` (Reentrant Lock) es una variante del `Lock` que permite a un **mismo proceso adquirir el lock múltiples veces** sin bloquearse a sí mismo. Internamente, mantiene un contador de adquisiciones y un registro del proceso "dueño" del lock. El lock solo se libera completamente (permitiendo que otro proceso lo adquiera) cuando el proceso dueño ha llamado a `release()` tantas veces como llamó a `acquire()`. [cite: fileName: Sincronización en Python con multiprocessing]

### 2.2. ¿Cuándo usarlo? (Casos de Uso Prácticos)
Los `RLock` son útiles principalmente en escenarios donde un mismo proceso puede necesitar acceder a un recurso protegido desde diferentes funciones o niveles de recursión, y cada uno de esos accesos necesita adquirir el lock.

* **Funciones Recursivas**: Si una función recursiva necesita proteger un recurso.

* **Llamadas Anidadas**: Cuando una función que adquiere un lock llama a otra función que *también* necesita adquirir *el mismo* lock.

* **Clases con Métodos Sincronizados**: Si un método sincronizado llama a otro método sincronizado del *mismo* objeto que usa el mismo lock.

**Advertencia**: El uso de `RLock` a menudo puede ser una señal de un diseño de concurrencia complejo o potencialmente problemático. Siempre considere si es posible rediseñar para evitar la necesidad de re-adquisición antes de optar por `RLock`.

### 2.3. Consideraciones Técnicas Clave

* **Propiedad**: A diferencia de `Lock` (que conceptualmente no tiene dueño estricto en `multiprocessing`), `RLock` sí tiene un dueño claro: solo el proceso que lo adquirió puede liberarlo.

* **Contador**: El núcleo del `RLock` es su contador. Cada `acquire()` por el dueño lo incrementa, y cada `release()` lo decrementa. El lock se libera cuando el contador llega a cero.

* **Rendimiento**: `RLock` es ligeramente más lento que `Lock` debido a la gestión adicional del dueño y el contador.

### 2.4. Ejemplo Práctico
```python
from multiprocessing import Process, RLock
import time

def worker_rlock(rlock, i):
    """ Función que adquiere el RLock dos veces. """
    print(f"Proceso {i}: Intentando adquirir (1ra vez)...")
    rlock.acquire()
    print(f"Proceso {i}: Adquirido (1ra vez).")
    try:
        print(f"Proceso {i}: Intentando adquirir (2da vez)...")
        rlock.acquire() # Esto funcionará gracias a RLock
        print(f"Proceso {i}: Adquirido (2da vez).")
        try:
            print(f"Proceso {i}: Trabajando...")
            time.sleep(0.5)
        finally:
            print(f"Proceso {i}: Liberando (2da vez)...")
            rlock.release()
            print(f"Proceso {i}: Liberado (2da vez).")
    finally:
        print(f"Proceso {i}: Liberando (1ra vez)...")
        rlock.release()
        print(f"Proceso {i}: Liberado (1ra vez).")

if __name__ == '__main__':
    rlock = RLock()
    processes = [Process(target=worker_rlock, args=(rlock, i)) for i in range(3)]
    for p in processes: p.start()
    for p in processes: p.join()
```
**Explicación**: Cada proceso adquiere el `RLock`, y luego, *sin liberarlo*, lo vuelve a adquirir. Con un `Lock` normal, esto causaría un deadlock. Con `RLock`, funciona, y el lock solo se libera para el siguiente proceso cuando se han ejecutado ambas llamadas a `release()`. [cite: fileName: Sincronización en Python con multiprocessing]

### 2.5. Ejercicios

#### Ejercicio Propuesto: Explorador de Directorios Recursivo Sincronizado
Escribe un programa con una función recursiva que explora un árbol de directorios. Esta función debe actualizar una estructura de datos compartida (por ejemplo, un `Value` o un `Array` que cuente archivos por tipo). Lanza varios procesos para explorar *diferentes* partes del árbol, pero asegúrate de que *todos* usen un **`RLock`** para proteger la estructura compartida cuando la actualicen. Demuestra que la recursión y la sincronización funcionan juntas.

#### Ejercicio Resuelto: Objeto con Métodos Sincronizados Anidados
```python
from multiprocessing import Process, RLock, Value
import ctypes
import time

class AccountRL: # Renombrado para evitar conflicto con otros Account
    def __init__(self, lock):
        self.balance = Value(ctypes.c_double, 1000.0)
        self.lock = lock # Debe ser un RLock

    def _internal_update(self, amount, process_id, operation_name):
        # Este método es llamado por deposit y withdraw, ya dentro del lock
        # No necesita 'with self.lock:' aquí si es llamado por un método que ya lo tiene.
        # Pero si pudiera ser llamado externamente, necesitaría 'with self.lock:'
        print(f"Proceso {process_id}: {operation_name} {abs(amount)}...")
        time.sleep(0.1)
        self.balance.value += amount
        print(f"Proceso {process_id}: Nuevo balance {self.balance.value}")


    def deposit(self, amount, process_id):
        with self.lock: # Adquiere RLock
            print(f"Proceso {process_id}: Entrando a deposit.")
            self._internal_update(amount, process_id, "Depositando")
            print(f"Proceso {process_id}: Saliendo de deposit.")


    def withdraw_and_log(self, amount, process_id):
        with self.lock: # Adquiere RLock
            print(f"Proceso {process_id}: Entrando a withdraw_and_log.")
            if self.balance.value >= amount:
                self._internal_update(-amount, process_id, "Retirando") # Llama a otro método
                print(f"Proceso {process_id}: Retiro exitoso.")
                return True
            else:
                print(f"Proceso {process_id}: Fondos insuficientes.")
                return False

def task_rl(account, i):
    account.deposit(200, i)
    account.withdraw_and_log(100, i)

if __name__ == '__main__':
    rl = RLock() # Importante que sea RLock
    acc_rl = AccountRL(rl)

    procs = [Process(target=task_rl, args=(acc_rl, i)) for i in range(2)]
    for p in procs: p.start()
    for p in procs: p.join()
    print(f"Balance final de la cuenta (RLock): {acc_rl.balance.value}")
```
**Explicación**: `deposit` y `withdraw_and_log` adquieren el `RLock`. `withdraw_and_log` luego llama a `_internal_update`. Si `_internal_update` también intentara adquirir el mismo lock (y no fuera un `RLock`), causaría un deadlock. Con `RLock`, la re-adquisición implícita o explícita por el mismo proceso es permitida.

---

## 3. Semaphore: El Semáforo Contador

### 3.1. ¿Qué es y qué hace?
Un `Semaphore` es una primitiva de sincronización que gestiona un **contador interno**. A diferencia de un `Lock` (que es como un semáforo con contador 1), un `Semaphore` se inicializa con un valor $N$ y permite que hasta **$N$ procesos** adquieran el semáforo simultáneamente. Cada `acquire()` decrementa el contador (bloqueando si es cero) y cada `release()` lo incrementa (despertando a un proceso en espera si lo hay). [cite: fileName: Sincronización en Python con multiprocessing]

### 3.2. ¿Cuándo usarlo? (Casos de Uso Prácticos)
Se usan cuando se necesita limitar el acceso concurrente a un **conjunto finito de recursos idénticos**.

* **Pools de Recursos**: Limitar el número de conexiones a una base de datos, el número de *workers* procesando una tarea específica, o el número de licencias de software disponibles.

* **Buffers Limitados**: En el problema del productor-consumidor, se pueden usar semáforos para controlar cuántos elementos hay en el buffer (para que el productor no añada si está lleno) y cuántos espacios vacíos hay (para que el consumidor no intente quitar si está vacío).

* **Control de Carga**: Limitar el número de peticiones simultáneas que se procesan para evitar sobrecargar un sistema.

### 3.3. Consideraciones Técnicas Clave

* **Valor Inicial ($N$)**: Define la capacidad del recurso.

* **Sin Propiedad**: A diferencia de `RLock`, `Semaphore` no tiene concepto de propiedad. Cualquier proceso puede llamar a `release()`, incluso si no llamó a `acquire()`. Esto es potente pero peligroso: un `release()` erróneo puede corromper la lógica del recurso.

* **Espera**: Si `acquire()` se llama cuando el contador es 0, el proceso se bloquea.

### 3.4. Ejemplo Práctico (Pool de Conexiones)
```python
from multiprocessing import Process, Semaphore
import time
import random

def database_worker_sem(semaphore, process_id): # Renombrado
    """ Simula un worker que necesita una conexión a la BD. """
    print(f"Proceso {process_id}: Esperando conexión a la BD...")
    semaphore.acquire()
    print(f"Proceso {process_id}: Conexión obtenida. Trabajando...")
    try:
        # Simula trabajo con la BD
        time.sleep(random.uniform(0.5, 2.0))
    finally:
        print(f"Proceso {process_id}: Liberando conexión.")
        semaphore.release()

if __name__ == '__main__':
    # Creamos un semáforo que permite hasta 3 conexiones simultáneas
    db_connections_sem = Semaphore(3) # Renombrado
    
    processes_sem = [] # Renombrado
    print("Lanzando 10 workers para acceder a 3 conexiones de BD (Semaphore)...")
    for i in range(10):
        p = Process(target=database_worker_sem, args=(db_connections_sem, i))
        processes_sem.append(p)
        p.start()

    for p in processes_sem:
        p.join()
    print("Todos los workers (Semaphore) han terminado.")
```
**Explicación**: Se crea un `Semaphore` con valor 3. Se lanzan 10 procesos. Solo 3 procesos podrán "obtener conexión" (pasar el `acquire()`) a la vez. Cuando uno termina y llama a `release()`, otro que estaba esperando puede adquirirlo. [cite: fileName: Sincronización en Python con multiprocessing]

### 3.5. Ejercicios

#### Ejercicio Propuesto: Sistema de Reservas de Cine
Simula un sistema de reservas de cine con un número limitado de asientos (por ejemplo, 50). Crea 100 procesos, cada uno intentando reservar un número aleatorio de asientos (entre 1 y 4). Usa un `Semaphore` para controlar el número de asientos disponibles. Si un proceso intenta reservar más asientos de los que quedan, debe fallar (o esperar si decides complicarlo). Asegúrate de que el número total de asientos reservados nunca exceda el límite.

#### Ejercicio Resuelto: Buffer Limitado (Productor-Consumidor Simple con Semaphore)
```python
from multiprocessing import Process, Semaphore, Queue, current_process
import time
import random

def producer_sem_pc(queue, empty_sem, full_sem): # Renombrado
    """ Produce 10 items y los pone en la cola. """
    for i in range(10):
        item = f"Item-{i} by {current_process().name}"
        
        empty_sem.acquire() # Espera si el buffer está lleno (no hay 'empty' slots)
        print(f"Productor {current_process().name}: Produciendo {item}")
        queue.put(item)
        time.sleep(random.uniform(0.1, 0.3))
        full_sem.release() # Señala que hay un 'full' slot más

def consumer_sem_pc(queue, empty_sem, full_sem): # Renombrado
    """ Consume 10 items de la cola. """
    for _ in range(10):
        full_sem.acquire() # Espera si el buffer está vacío (no hay 'full' slots)
        item = queue.get()
        print(f"Consumidor {current_process().name}: Consumiendo {item}")
        time.sleep(random.uniform(0.2, 0.5))
        empty_sem.release() # Señala que hay un 'empty' slot más

if __name__ == '__main__':
    buffer_size_sem = 5 # Renombrado
    queue_sem = Queue(buffer_size_sem) # Renombrado
    
    empty_s = Semaphore(buffer_size_sem) # Renombrado
    full_s = Semaphore(0) # Renombrado

    p_sem = Process(target=producer_sem_pc, args=(queue_sem, empty_s, full_s), name="P-Sem")
    c_sem = Process(target=consumer_sem_pc, args=(queue_sem, empty_s, full_s), name="C-Sem")

    p_sem.start()
    c_sem.start()

    p_sem.join()
    c_sem.join()
    print("Sistema Productor-Consumidor (Semaphore) terminado.")
```
**Explicación**: Se usan dos semáforos: `empty_s` controla cuántos espacios vacíos hay (el productor adquiere `empty_s` antes de poner) y `full_s` controla cuántos espacios llenos hay (el consumidor adquiere `full_s` antes de quitar). Esto asegura que el productor se bloquee si la cola está llena y el consumidor se bloquee si está vacía, usando `Semaphore` para contar los recursos (slots llenos/vacíos).

---

## 4. BoundedSemaphore: El Semáforo Acotado

### 4.1. ¿Qué es y qué hace?
Un `BoundedSemaphore` es idéntico a un `Semaphore`, con una **única pero importante diferencia**: **impide que se llame a `release()` más veces de las que se ha llamado a `acquire()`**. Mantiene el contador interno, pero si una llamada a `release()` intentara incrementar el contador por encima de su valor inicial (el valor con el que fue creado), lanzará una excepción `ValueError`. [cite: fileName: Sincronización en Python con multiprocessing]

### 4.2. ¿Cuándo usarlo? (Casos de Uso Prácticos)
Se utiliza en los mismos escenarios que `Semaphore`, pero cuando se desea una **mayor robustez contra errores de programación**. Si un `release()` accidental o erróneo podría desestabilizar la lógica de gestión de recursos, un `BoundedSemaphore` lo detectará inmediatamente.

* **Depuración**: Ayuda a encontrar errores donde un recurso se libera incorrectamente.

* **Sistemas Críticos**: Donde la integridad del contador de recursos es vital y un error podría tener consecuencias graves.

* **Implementaciones Complejas**: Donde es más fácil perder la cuenta de las llamadas `acquire`/`release`.

### 4.3. Consideraciones Técnicas Clave

* **Excepción `ValueError`**: Es su característica distintiva.

* **Mismo Rendimiento**: Su rendimiento es prácticamente idéntico al de `Semaphore`.

* **Elección**: Si no hay una razón fuerte para no hacerlo, usar `BoundedSemaphore` en lugar de `Semaphore` puede ser una práctica defensiva recomendable.

### 4.4. Ejemplo Práctico
```python
from multiprocessing import Process, BoundedSemaphore
import time

def worker_bs(b_sem, i):
    """ Intenta liberar el semáforo sin adquirirlo primero o de más. """
    print(f"Proceso {i} (BSem): Intentando adquirir...")
    b_sem.acquire()
    print(f"Proceso {i} (BSem): Adquirido.")
    time.sleep(1)
    print(f"Proceso {i} (BSem): Liberando...")
    b_sem.release()
    print(f"Proceso {i} (BSem): Liberado.")
    
    # Intento de liberación extra
    try:
        print(f"Proceso {i} (BSem): Intentando liberar OTRA VEZ (esto causará error)...")
        b_sem.release()
    except ValueError as e:
        print(f"Proceso {i} (BSem): ¡ERROR! {e}")

if __name__ == '__main__':
    # Creamos un BoundedSemaphore con valor 1 (actúa como un Lock acotado)
    bounded_sem_ex = BoundedSemaphore(1) # Renombrado
    
    p_bs = Process(target=worker_bs, args=(bounded_sem_ex, 1)) # Renombrado
    p_bs.start()
    p_bs.join()
    
    # Intentamos liberar desde el principal (también causará error si el contador ya está en el límite)
    try:
        print("Principal (BSem): Intentando liberar (esto podría causar error)...")
        # Si el worker lo dejó en 1, esta liberación fallará.
        bounded_sem_ex.release() 
    except ValueError as e:
        print(f"Principal (BSem): ¡ERROR! {e}")
```
**Explicación**: El `worker_bs` adquiere y libera el semáforo correctamente una vez. Sin embargo, el segundo intento de `release()` falla con un `ValueError` porque el contador ya está en su valor inicial (1) y no puede excederlo. Lo mismo ocurre cuando el proceso principal intenta liberarlo si ya está en su valor máximo. [cite: fileName: Sincronización en Python con multiprocessing]

### 4.5. Ejercicios

#### Ejercicio Propuesto: Depuración de Semáforos con BoundedSemaphore
Toma el ejercicio resuelto del `Semaphore` (Productor-Consumidor) y modifícalo para usar `BoundedSemaphore` donde creas que tiene sentido. Luego, introduce deliberadamente un error en el código (por ejemplo, un `release()` extra en el productor) y observa cómo `BoundedSemaphore` te ayuda a detectar el problema lanzando una excepción, mientras que un `Semaphore` normal podría no hacerlo (o podría causar un comportamiento incorrecto más adelante).

#### Ejercicio Resuelto: Pool de Conexiones Robusto con BoundedSemaphore
```python
from multiprocessing import Process, BoundedSemaphore
import time
import random

MAX_CONNECTIONS_BS = 2 # Renombrado
connections_bs = BoundedSemaphore(MAX_CONNECTIONS_BS) # Renombrado

def get_connection_bs(process_id): # Renombrado
    """ Obtiene una conexión. """
    connections_bs.acquire()
    print(f"Proceso {process_id} (BSem-Pool): Conexión obtenida.")

def release_connection_bs(process_id): # Renombrado
    """ Libera una conexión. Lanza ValueError si se libera de más. """
    print(f"Proceso {process_id} (BSem-Pool): Liberando conexión.")
    connections_bs.release()

def use_resource_bs(process_id): # Renombrado
    """ Simula el uso de una conexión, con un error deliberado. """
    connection_held = False
    try:
        get_connection_bs(process_id)
        connection_held = True
        time.sleep(random.uniform(0.5, 1.5))
        
        release_connection_bs(process_id)
        connection_held = False # Liberada correctamente
        
        print(f"Proceso {process_id} (BSem-Pool): ¡Intentando liberar de nuevo por error!")
        release_connection_bs(process_id) # Esto debería causar ValueError
    except ValueError:
        print(f"Proceso {process_id} (BSem-Pool): ¡ERROR DETECTADO! Se intentó liberar una conexión de más.")
    except Exception as e:
        print(f"Proceso {process_id} (BSem-Pool): Otro error: {e}")
    finally:
        # Asegurar que si se obtuvo una conexión y no se liberó por una excepción ANTES del error,
        # se intente liberar.
        if connection_held: # Si el error ocurrió antes de la primera liberación
            try:
                release_connection_bs(process_id)
                print(f"Proceso {process_id} (BSem-Pool): Conexión liberada en finally.")
            except ValueError:
                 print(f"Proceso {process_id} (BSem-Pool): Error al liberar en finally (posiblemente ya estaba en el límite).")


if __name__ == '__main__':
    processes_bs_pool = [] # Renombrado
    for i in range(5):
        p = Process(target=use_resource_bs, args=(i,))
        processes_bs_pool.append(p)
        p.start()

    for p in processes_bs_pool:
        p.join()
```
**Explicación**: Este código simula un pool de 2 conexiones. La función `use_resource_bs` introduce un error deliberado al intentar llamar a `release_connection_bs` dos veces. Gracias a `BoundedSemaphore`, el segundo `release` lanza un `ValueError`, permitiendo que el programa detecte y reporte el error de lógica inmediatamente. El `finally` intenta manejar casos donde la conexión podría no haberse liberado debido a otros errores, aunque la lógica de recuperación de errores puede ser compleja.

---

## 5. Condition: La Variable de Condición

### 5.1. ¿Qué es y qué hace?
Una `Condition` es una primitiva de sincronización más avanzada que permite a los procesos **esperar hasta que una condición específica (relacionada con el estado de los datos compartidos) se cumpla**. Funciona siempre asociada a un `Lock` (o `RLock`). Proporciona los métodos:

* `acquire()` / `release()`: Heredados del `Lock` asociado (o se puede pasar un `Lock` externo).

* `wait()`: Libera el `Lock` asociado y bloquea el proceso actual hasta que otro proceso lo "despierte" con `notify()` o `notify_all()`. Una vez despierto, *re-adquiere* automáticamente el `Lock` antes de continuar.

* `notify(n=1)`: Despierta hasta `n` procesos que estén esperando en esta `Condition`.

* `notify_all()`: Despierta a *todos* los procesos que estén esperando en esta `Condition`.
[cite: fileName: Sincronización en Python con multiprocessing]

### 5.2. ¿Cuándo usarlo? (Casos de Uso Prácticos)
Se utiliza cuando la sincronización no depende solo de si un recurso está "libre" u "ocupado", sino del **estado específico** de los datos compartidos.

* **Productor-Consumidor Avanzado**: Es el caso canónico. Los consumidores esperan (`wait()`) si el buffer está vacío. El productor, al añadir un item, notifica (`notify()`) a un consumidor. Los productores esperan si el buffer está lleno. El consumidor, al quitar un item, notifica a un productor.

* **Sincronización Basada en Estado**: Cualquier escenario donde un proceso deba esperar a que otro proceso cambie el estado del sistema a uno específico (ej: "esperar a que la lista tenga al menos 10 elementos", "esperar a que todos los workers estén listos").

* **Lectores-Escritores**: Se puede usar (aunque es complejo) para implementar patrones donde múltiples lectores pueden acceder, pero los escritores necesitan acceso exclusivo, y deben esperar a que se cumplan ciertas condiciones.

### 5.3. Consideraciones Técnicas Clave

* **Lock Asociado**: Toda `Condition` necesita un `Lock`. Las operaciones `wait`, `notify`, y `notify_all` *deben* llamarse solo cuando se posee el `Lock` asociado.

* **`wait()` y el Bucle `while`**: ¡Fundamental! Debido a los "despertares espurios" (un proceso puede despertar sin que `notify` haya sido llamado) y a que la condición puede haber cambiado entre la notificación y el despertar, **`wait()` siempre debe usarse dentro de un bucle `while` que re-verifique la condición**:
    
```python
    with condition: # Adquiere el lock asociado
        while not es_mi_turno_o_condicion_ok():
            condition.wait() # Libera el lock y espera
        # Ahora sé que la condición es (o era) cierta, procedo...
```

* **`notify()` vs. `notify_all()`**: `notify()` es más eficiente si sabes que solo un proceso puede (o debe) proceder. `notify_all()` es más simple y seguro si no estás seguro o si múltiples procesos pueden proceder, pero puede causar el "efecto estampida" (muchos procesos despiertan, compiten por el lock y solo uno gana, los demás vuelven a esperar).

### 5.4. Ejemplo Práctico (Productor-Consumidor Simple con Condition)
```python
from multiprocessing import Process, Condition, Lock, Value
import time
import ctypes

def producer_cond_ex(condition, shared_value, process_id): # Renombrado
    """ Produce valores y notifica. """
    for i in range(1, 6):
        with condition: # Adquiere el lock asociado
            shared_value.value = i
            print(f"Proceso {process_id} (Productor-Cond): Producido {i}")
            print(f"Proceso {process_id} (Productor-Cond): Notificando a todos...")
            condition.notify_all() # Notifica a todos los waiters
            time.sleep(1) # Da tiempo a que los consumidores reaccionen

def consumer_cond_ex(condition, shared_value, process_id): # Renombrado
    """ Espera una condición y consume. """
    with condition: # Adquiere el lock asociado
        print(f"Proceso {process_id} (Consumidor-Cond): Esperando valor >= 3...")
        while shared_value.value < 3:
            condition.wait() # Libera el lock y espera
        # Cuando despierta, tiene el lock y la condición es (o era) >= 3
        print(f"Proceso {process_id} (Consumidor-Cond): ¡Condición cumplida! Valor = {shared_value.value}")

if __name__ == '__main__':
    lock_cond = Lock() # Renombrado
    condition_ex = Condition(lock_cond) # Renombrado, Condition usa un Lock
    value_cond = Value(ctypes.c_int, 0) # Renombrado

    p_cond = Process(target=producer_cond_ex, args=(condition_ex, value_cond, 0))
    consumers_cond = [Process(target=consumer_cond_ex, args=(condition_ex, value_cond, i+1)) for i in range(3)]

    for c in consumers_cond:
        c.start()
    time.sleep(0.1) # Asegurar que los consumidores esperen primero
    p_cond.start()

    p_cond.join()
    for c in consumers_cond:
        c.join()
    print("Sistema Productor-Consumidor (Condition) terminado.")
```
**Explicación**: Los consumidores adquieren la condición y entran en `wait()` porque el valor inicial es 0. El productor adquiere la condición, cambia el valor y llama a `notify_all()`. Cuando el valor llega a 3 o más, los consumidores despiertan, *re-verifican* la condición en el `while`, la encuentran cierta, e imprimen el mensaje. [cite: fileName: Sincronización en Python con multiprocessing]

### 5.5. Ejercicios

#### Ejercicio Propuesto: Barrera Reutilizable con `Condition`
Implementa una barrera de sincronización *reutilizable* para N procesos usando `Condition` y `Value`/`Lock`. Debe funcionar de la siguiente manera: N procesos llaman a un método `wait_on_barrier()`. Ninguno debe proceder hasta que los N procesos hayan llamado al método. Una vez que los N llegan, todos deben ser liberados. La barrera debe poder "reiniciarse" para ser usada en múltiples puntos de encuentro.

#### Ejercicio Resuelto: Buffer Productor-Consumidor con `Condition` y `Queue`
```python
from multiprocessing import Process, Condition, Lock, Queue
import time
import random

BUFFER_SIZE_COND_Q = 3 # Renombrado
def producer_cond_q(queue, condition): # Renombrado
    for i in range(10):
        item = f"Item-CQ {i}" # Renombrado
        with condition:
            while queue.qsize() >= BUFFER_SIZE_COND_Q:
                print(f"Productor-CQ: Buffer lleno ({queue.qsize()}), esperando...")
                condition.wait() # Espera si está lleno
            
            print(f"Productor-CQ: Añadiendo {item}")
            queue.put(item)
            condition.notify() # Notifica al consumidor (podría ser notify_all si hay varios consumidores)
        time.sleep(random.uniform(0.0, 0.2))

def consumer_cond_q(queue, condition): # Renombrado
    for _ in range(10):
        with condition:
            while queue.empty():
                print(f"Consumidor-CQ: Buffer vacío, esperando...")
                condition.wait() # Espera si está vacío

            item = queue.get()
            print(f"Consumidor-CQ: Consumiendo {item}")
            condition.notify() # Notifica al productor (si podría estar esperando por espacio)
        time.sleep(random.uniform(0.1, 0.4))

if __name__ == '__main__':
    q_cq = Queue() # Renombrado
    lock_cq = Lock() # Renombrado
    cond_cq = Condition(lock_cq) # Renombrado

    p_proc_cq = Process(target=producer_cond_q, args=(q_cq, cond_cq))
    c_proc_cq = Process(target=consumer_cond_q, args=(q_cq, cond_cq))

    p_proc_cq.start()
    c_proc_cq.start()

    p_proc_cq.join()
    c_proc_cq.join()
    print("Productor-Consumidor con Condition y Queue terminado.")
```
**Explicación**: Productor y consumidor usan la misma `Condition` (y su `Lock` asociado). El productor espera (`wait()`) si la cola (`queue.qsize()`) está llena, y notifica (`notify()`) después de añadir. El consumidor espera si la cola está vacía (`queue.empty()`) y notifica después de quitar. Los bucles `while` aseguran que la condición se verifique correctamente antes de proceder.

---

## 6. Event: La Señal de Evento

### 6.1. ¿Qué es y qué hace?
Un `Event` es una de las primitivas de sincronización más simples. Es esencialmente una **bandera (flag) booleana segura para procesos**. Puede estar en uno de dos estados: **establecido (set)** o **no establecido (clear)**. Proporciona los métodos:

* `is_set()`: Devuelve `True` si el evento está establecido, `False` si no.

* `set()`: Establece el evento. Todos los procesos que estén esperando (`wait()`) serán despertados. Los procesos que llamen a `wait()` *después* de `set()` no se bloquearán.

* `clear()`: Restablece el evento (lo pone en no establecido). Los procesos que llamen a `wait()` *después* de `clear()` se bloquearán.

* `wait(timeout=None)`: Bloquea el proceso actual *solo si* el evento no está establecido. Si el evento está establecido, retorna inmediatamente. Si se establece mientras espera, retorna. Si se provee `timeout`, retorna después de ese tiempo si el evento no se establece.
[cite: fileName: Sincronización en Python con multiprocessing]

### 6.2. ¿Cuándo usarlo? (Casos de Uso Prácticos)
Se usa para **comunicar una señal simple entre procesos**, a menudo para indicar que ha ocurrido algo importante o que se ha alcanzado una fase específica.

* **Señal de Inicio**: Un proceso principal puede preparar recursos y luego `set()` un evento para indicar a los procesos trabajadores que pueden comenzar.

* **Señal de Finalización**: Un proceso trabajador puede `set()` un evento para indicar que ha terminado su tarea.

* **Señal de Cierre/Apagado**: Un proceso puede `set()` un evento para pedir a otros procesos que terminen limpiamente.

* **Pausa/Reanudación**: Se puede usar `clear()` para pausar y `set()` para reanudar a otros procesos que estén esperando en `wait()`.

### 6.3. Consideraciones Técnicas Clave

* **Simplicidad**: Es su mayor ventaja. Es fácil de entender y usar para señalización simple.

* **Difusión (Broadcast)**: Cuando `set()` se llama, *todos* los procesos en espera se despiertan. No hay `notify()` selectivo.

* **Sin Estado Complejo**: No es adecuado para sincronización basada en condiciones complejas; para eso está `Condition`.

### 6.4. Ejemplo Práctico
```python
from multiprocessing import Process, Event
import time

def worker_waiter_event(event, i): # Renombrado
    """ Espera a que el evento se establezca. """
    print(f"Proceso {i} (Event): Esperando el evento...")
    event.wait() # Se bloquea aquí hasta que event.set() sea llamado
    print(f"Proceso {i} (Event): ¡Evento detectado! Continuando...")

def event_setter_event(event): # Renombrado
    """ Espera un poco y luego establece el evento. """
    print("Setter (Event): Voy a dormir por 3 segundos...")
    time.sleep(3)
    print("Setter (Event): ¡Estableciendo el evento!")
    event.set()

if __name__ == '__main__':
    event_ex = Event() # Renombrado, El evento empieza como 'no establecido'

    waiters_ev = [Process(target=worker_waiter_event, args=(event_ex, i)) for i in range(5)] # Renombrado
    setter_ev = Process(target=event_setter_event, args=(event_ex,)) # Renombrado

    for w in waiters_ev:
        w.start()
    setter_ev.start()

    for w in waiters_ev:
        w.join()
    setter_ev.join()
    print("Todos los procesos (Event) terminaron.")
```
**Explicación**: Se crea un `Event`. Se lanzan 5 procesos `worker_waiter_event` que inmediatamente llaman a `event.wait()` y se bloquean. El proceso `event_setter_event` espera 3 segundos y luego llama a `event.set()`. En ese momento, los 5 `worker_waiter_event` se desbloquean simultáneamente y continúan su ejecución. [cite: fileName: Sincronización en Python con multiprocessing]

### 6.5. Ejercicios

#### Ejercicio Propuesto: Control de Pipeline con `Event`
Crea un pipeline de 3 procesos (A, B, C). El proceso A hace un trabajo, luego debe esperar a que B esté listo. El proceso B no puede empezar hasta que A termine. Cuando B termina, debe esperar a que C esté listo. C no puede empezar hasta que B termine. Usa `Event`s para coordinar el paso de "testigo" entre los procesos A -> B -> C.

#### Ejercicio Resuelto: Sistema de Alarma Simple con Event
```python
from multiprocessing import Process, Event, Value
import ctypes
import time
import random

def monitor_sensor_event(event, temperature, sensor_id): # Renombrado
    """ Simula un sensor que mide temperatura y activa un evento. """
    while True:
        # En un sistema real, la lectura de temperatura podría ser una operación bloqueante
        # o requerir su propia sincronización si el sensor es compartido.
        # Aquí, asumimos que la lectura es simple.
        temp = random.uniform(15.0, 35.0)
        
        # Actualizar un valor compartido es opcional, el Event es el mecanismo principal aquí.
        # Si se actualiza, se necesitaría un Lock para shared_temp.
        # temperature.value = temp 
        
        print(f"Sensor {sensor_id} (Event): Temperatura = {temp:.2f}°C")
        if temp > 30.0:
            print(f"Sensor {sensor_id} (Event): ¡ALERTA! Temperatura > 30°C. ¡Activando evento!")
            event.set() # Activa la alarma
            break # El sensor deja de medir una vez que activa la alarma
        
        if event.is_set(): # Otro sensor podría haber activado la alarma
            print(f"Sensor {sensor_id} (Event): Alarma ya activada por otro. Terminando.")
            break
        time.sleep(1)

def alarm_system_event(event): # Renombrado
    """ Espera el evento de alarma. """
    print("Sistema de Alarma (Event): Esperando señal de alerta...")
    event.wait() # Se bloquea hasta que event.set() es llamado
    print("Sistema de Alarma (Event): ¡ALARMA RECIBIDA! ¡ACTIVANDO SIRENA!")
    # Aquí iría el código para activar la sirena, enviar notificaciones, etc.

if __name__ == '__main__':
    alarm_event_ex = Event() # Renombrado
    # shared_temp_ev = Value(ctypes.c_float, 20.0) # Opcional, no usado directamente por Event

    sensor1_ev = Process(target=monitor_sensor_event, args=(alarm_event_ex, None, 1)) # Renombrado
    sensor2_ev = Process(target=monitor_sensor_event, args=(alarm_event_ex, None, 2)) # Renombrado
    alarm_proc_ev = Process(target=alarm_system_event, args=(alarm_event_ex,)) # Renombrado

    alarm_proc_ev.start()
    sensor1_ev.start()
    sensor2_ev.start()

    alarm_proc_ev.join() # El sistema de alarma terminará cuando reciba la señal
    
    # Una vez que la alarma ha sonado y terminado, podemos detener los sensores.
    # En un sistema real, se usaría un mecanismo de cierre más elegante (otro Event, Pipe, etc.)
    print("Sistema de Alarma (Event) terminado. Deteniendo sensores...")
    if sensor1_ev.is_alive(): sensor1_ev.terminate()
    if sensor2_ev.is_alive(): sensor2_ev.terminate()
    
    # Esperar a que terminen si fueron terminados
    sensor1_ev.join(timeout=1)
    sensor2_ev.join(timeout=1)
    
    print("Sistema de Monitoreo (Event) terminado.")
```
**Explicación**: Dos procesos `monitor_sensor_event` simulan medir la temperatura. Si la temperatura excede 30°C, llaman a `event.set()`. El proceso `alarm_system_event` está bloqueado en `event.wait()`. Tan pronto como *cualquier* sensor llame a `set()`, el proceso de alarma se desbloquea y "activa la sirena". Los sensores también verifican `is_set()` para terminar si otro ya activó la alarma.

---

## 7. Barrier: La Barrera de Sincronización

### 7.1. ¿Qué es y qué hace?
Una `Barrier` es una primitiva diseñada para que un **número fijo de procesos se esperen mutuamente en un punto específico** antes de que cualquiera de ellos pueda continuar. Es un punto de encuentro o "rendezvous". Se inicializa con un número de "partes" (parties), que es el número de procesos que deben llegar a la barrera. Cuando un proceso llega, llama a `wait()`. Este proceso se bloqueará hasta que *todos* los N procesos hayan llamado a `wait()`. Una vez que el N-ésimo proceso llega, *todos* los procesos se desbloquean simultáneamente. [cite: fileName: Sincronización en Python con multiprocessing]

### 7.2. ¿Cuándo usarlo? (Casos de Uso Prácticos)
Es fundamental en algoritmos paralelos donde el cálculo se divide en **fases** y todos los procesos deben completar una fase antes de que cualquiera pueda comenzar la siguiente.

* **Computación Científica Paralela**: En simulaciones o cálculos matriciales donde cada proceso trabaja en una parte de los datos y necesita intercambiar resultados o sincronizarse antes de la siguiente iteración.

* **Inicialización Sincronizada**: Asegurarse de que N procesos han completado su configuración inicial antes de que comience el trabajo principal.

* **Pruebas de Concurrencia**: Para forzar a que múltiples procesos lleguen a un punto específico al mismo tiempo para probar escenarios de carrera.

### 7.3. Consideraciones Técnicas Clave

* **Número Fijo de Partes**: Se define al crear la `Barrier`. No se puede cambiar dinámicamente.

* **`wait()`**: Es la llamada bloqueante. Devuelve un número (de 0 a N-1) único para cada proceso en esa "ronda" de la barrera, útil si un proceso necesita hacer algo especial (por ejemplo, el proceso 0 imprime un mensaje).

* **Barreras Rotas (`BrokenBarrierError`)**: Si un proceso llama a `wait()` y otro proceso se reinicia (`reset()`) o aborta (`abort()`), o si el número de procesos esperando excede el número de partes, los procesos en espera recibirán esta excepción.

* **`reset()`**: Restablece la barrera a su estado inicial, permitiendo su reutilización.

* **`abort()`**: Pone la barrera en estado roto. Todos los `wait()` futuros y actuales lanzarán `BrokenBarrierError`.

### 7.4. Ejemplo Práctico (Trabajo por Fases)
```python
from multiprocessing import Process, Barrier
import time
import random

def phase_worker_barrier(barrier, process_id): # Renombrado
    """ Simula un worker que trabaja en dos fases. """
    
    # Fase 1
    work_time1 = random.uniform(0.5, 3.0)
    print(f"Proceso {process_id} (Barrier): Iniciando Fase 1 ({work_time1:.2f}s)...")
    time.sleep(work_time1)
    print(f"Proceso {process_id} (Barrier): Fase 1 completada. Esperando en Barrera...")
    
    idx = barrier.wait() # Espera a que todos lleguen
    print(f"Proceso {process_id} (Barrier): Soy el {idx}-ésimo en llegar. ¡Todos llegaron!")
    
    # Fase 2
    print(f"Proceso {process_id} (Barrier): Iniciando Fase 2...")
    work_time2 = random.uniform(0.5, 2.0)
    time.sleep(work_time2)
    print(f"Proceso {process_id} (Barrier): Fase 2 completada.")
    
    # Podría haber otra barrera aquí si hubiera una Fase 3

if __name__ == '__main__':
    NUM_PROCESSES_BAR = 4 # Renombrado
    # Creamos una barrera para NUM_PROCESSES_BAR procesos
    barrier_ex = Barrier(NUM_PROCESSES_BAR) # Renombrado
    
    processes_bar = [] # Renombrado
    print(f"Lanzando {NUM_PROCESSES_BAR} workers (Barrier)...")
    for i in range(NUM_PROCESSES_BAR):
        p = Process(target=phase_worker_barrier, args=(barrier_ex, i))
        processes_bar.append(p)
        p.start()

    for p in processes_bar:
        p.join()
    print("Todas las fases (Barrier) completadas.")
```
**Explicación**: Se crea una `Barrier` para 4 procesos. Cada proceso simula trabajar un tiempo aleatorio en la Fase 1 y luego llama a `barrier.wait()`. Ninguno puede pasar a la Fase 2 hasta que los 4 hayan llamado a `wait()`. Una vez que el cuarto llega, todos se desbloquean y comienzan la Fase 2. La llamada `wait()` devuelve un índice que puede ser útil. [cite: fileName: Sincronización en Python con multiprocessing]

### 7.5. Ejercicios

#### Ejercicio Propuesto: Juego de Carreras Sincronizado con Barrier
Simula una carrera con 5 corredores (procesos). La carrera tiene 3 "vueltas". Todos los corredores deben empezar al mismo tiempo (usa una `Barrier` para la línea de salida). Después de cada vuelta, deben esperar en la línea de meta hasta que *todos* hayan completado esa vuelta antes de empezar la siguiente (usa la *misma* `Barrier` u otras si prefieres, considera `reset()` si la reutilizas). Imprime mensajes para ver cómo se sincronizan.

#### Ejercicio Resuelto: Actualización de Matriz por Fases con Barrier
```python
from multiprocessing import Process, Barrier, Array
import time
import random

def update_row_barrier(barrier, row_index, matrix, num_cols, num_phases): # Renombrado
    """ Actualiza una fila de la matriz en varias fases usando Barrier. """
    for phase in range(num_phases):
        print(f"Proceso {row_index} (Mat-Bar): Iniciando Fase {phase} para fila {row_index}...")
        # Simula cálculo basado en valores anteriores
        # Aquí, simplemente incrementamos elementos de la fila
        with matrix.get_lock(): # Protege el acceso al Array compartido
            for col in range(num_cols):
                matrix[row_index * num_cols + col] += (row_index + 1) * (phase + 1) * random.randint(1,5)
            
            current_row_vals = matrix[row_index * num_cols : (row_index + 1) * num_cols]
            print(f"Proceso {row_index} (Mat-Bar): Fila {row_index} en Fase {phase} = {current_row_vals}")
            
        time.sleep(random.uniform(0.1, 0.5)) # Simula tiempo de cómputo
        arrival_idx = barrier.wait() # Espera a que todas las filas se actualicen en esta fase
        if arrival_idx == 0: # Solo un proceso (el que llega con índice 0) imprime esto
            print(f"--- Fase {phase} completada por todos los procesos (Mat-Bar). Barrera cruzada. ---")


if __name__ == '__main__':
    ROWS_BAR = 3 # Renombrado
    COLS_BAR = 4 # Renombrado
    PHASES_BAR = 2 # Renombrado
    
    # Matriz compartida (Array), inicializada a ceros
    shared_matrix_bar = Array('i', [0] * (ROWS_BAR * COLS_BAR)) # Renombrado
    
    # Barrera para ROWS_BAR procesos
    barrier_mat = Barrier(ROWS_BAR) # Renombrado
    
    processes_mat_bar = [] # Renombrado
    print("Iniciando actualización de matriz por fases (Barrier)...")
    print(f"Matriz inicial (Barrier): {shared_matrix_bar[:]}")
    for i in range(ROWS_BAR):
        p = Process(target=update_row_barrier, args=(barrier_mat, i, shared_matrix_bar, COLS_BAR, PHASES_BAR))
        processes_mat_bar.append(p)
        p.start()

    for p in processes_mat_bar:
        p.join()
        
    print(f"\nActualización (Barrier) finalizada. Matriz final:")
    for r in range(ROWS_BAR):
        print(shared_matrix_bar[r * COLS_BAR : (r + 1) * COLS_BAR])
```
**Explicación**: Cada proceso es responsable de actualizar una fila de una matriz compartida. El cálculo se divide en fases. Después de cada fase, todos los procesos deben esperar en la `Barrier` para asegurarse de que toda la matriz esté en un estado consistente (según la lógica de la fase) antes de comenzar la siguiente fase de actualización. El proceso que llega con índice 0 a la barrera imprime un mensaje de finalización de fase.

---

## 8. Queue: La Cola Segura para Procesos

### 8.1. ¿Qué es y qué hace?
Una `Queue` (cola) en `multiprocessing` es una estructura de datos **FIFO (First-In, First-Out)** diseñada específicamente para ser **segura para la comunicación entre procesos**. Permite que múltiples procesos añadan (`put()`) y quiten (`get()`) objetos de la cola sin preocuparse por las condiciones de carrera o la corrupción de datos. Internamente, utiliza `Pipe`s y `Lock`s/`Semaphore`s para garantizar esta seguridad. [cite: fileName: Sincronización en Python con multiprocessing]

### 8.2. ¿Cuándo usarlo? (Casos de Uso Prácticos)
Es el mecanismo **preferido y más robusto para pasar mensajes o datos entre procesos**.

* **Paso de Mensajes**: Enviar datos, comandos o resultados de un proceso a otro.

* **Distribución de Tareas (Task Queues)**: Un proceso (o varios) actúa como maestro, poniendo tareas en una `Queue`. Múltiples procesos *workers* toman tareas de esa `Queue` para procesarlas en paralelo.

* **Recolección de Resultados**: Los *workers* ponen sus resultados en otra `Queue`, y un proceso colector los recoge.

* **Productor-Consumidor**: Es una implementación natural y segura de este patrón.

### 8.3. Consideraciones Técnicas Clave

* **Serialización (Pickling)**: Los objetos puestos en una `Queue` deben ser "picklable" (serializables), ya que Python los serializa para enviarlos a través del `Pipe` subyacente. No todos los objetos son picklables (ej: generadores, conexiones de BD abiertas, algunos objetos con locks).

* **Bloqueo**: `put()` puede bloquearse si la cola tiene un tamaño máximo (especificado en el constructor) y está llena. `get()` se bloquea si la cola está vacía. Se pueden usar `put_nowait()` y `get_nowait()` (lanzan excepciones `queue.Full` y `queue.Empty` respectivamente) o especificar `timeout` en `put()` y `get()`.

* **Seguridad**: `Queue` maneja toda la sincronización interna por ti. No necesitas `Lock`s externos para acceder a ella.

* **`JoinableQueue`**: Una subclase que añade métodos `task_done()` y `join()`. `task_done()` es llamado por un consumidor para indicar que un ítem obtenido de la cola ha sido completamente procesado. `join()` bloquea hasta que todos los ítems puestos en la cola hayan sido obtenidos y procesados (es decir, `task_done()` haya sido llamado para cada ítem). Muy útil para saber cuándo todas las tareas de una cola de trabajo han sido completadas.

* **Tamaño Máximo**: Si no se especifica `maxsize` al crear la `Queue`, su tamaño es "ilimitado" (limitado por la memoria disponible).

### 8.4. Ejemplo Práctico (Productor-Consumidor Simple con Queue)
```python
from multiprocessing import Process, Queue
import time
import os

def producer_queue(queue): # Renombrado
    """ Pone 5 tareas en la cola. """
    pid = os.getpid()
    for i in range(5):
        task = f"Tarea {i} from PID {pid} (Queue)"
        print(f"Productor (Queue): Poniendo '{task}'")
        queue.put(task)
        time.sleep(0.5)
    # Señal de fin para CADA consumidor. Si hay N consumidores, N señales.
    queue.put("DONE_Q") # Renombrado 

def consumer_queue(queue, worker_id): # Renombrado
    """ Toma tareas de la cola hasta recibir 'DONE_Q'. """
    pid = os.getpid()
    while True:
        task = queue.get() # Bloquea si la cola está vacía
        print(f"Consumidor {worker_id} (PID {pid}, Queue): Obtenido '{task}'")
        if task == "DONE_Q":
            print(f"Consumidor {worker_id} (Queue): Señal de fin recibida.")
            # Si hay varios consumidores, es crucial que el productor ponga
            # una señal "DONE_Q" por cada consumidor.
            break 
        # Procesa la tarea...
        print(f"Consumidor {worker_id} (Queue): Procesando '{task}'...")
        time.sleep(random.uniform(0.5,1.5)) # Simula trabajo
        print(f"Consumidor {worker_id} (Queue): Terminado con '{task}'.")


if __name__ == '__main__':
    q_ex = Queue() # Renombrado

    p_q = Process(target=producer_queue, args=(q_ex,))
    c1_q = Process(target=consumer_queue, args=(q_ex, 1))
    # c2_q = Process(target=consumer_queue, args=(q_ex, 2)) # Si hay 2 consumidores, el productor necesita 2 "DONE_Q"

    p_q.start()
    c1_q.start()
    # c2_q.start()

    p_q.join()
    c1_q.join()
    # c2_q.join()
    print("Sistema Productor-Consumidor (Queue) terminado.")
```
**Explicación**: El productor pone tareas en la `Queue`. El consumidor las obtiene. `Queue` se encarga de que `put()` y `get()` sean seguros, incluso si hay múltiples productores y consumidores (aunque la lógica de señalización `DONE_Q` debe manejarse con cuidado en esos casos, enviando una señal por cada consumidor). [cite: fileName: Sincronización en Python con multiprocessing]

### 8.5. Ejercicios

#### Ejercicio Propuesto: Pool de Workers con `Queue` y `JoinableQueue`
Crea un sistema con un proceso "Maestro" y N procesos "Workers" (por ejemplo, N=4). El Maestro debe generar 50 tareas (pueden ser simples números o strings) y ponerlas en una `JoinableQueue` de entrada. Los Workers deben tomar tareas de esa cola, procesarlas (simula con `time.sleep` y una impresión), y llamar a `task_done()` en la cola de entrada. Los resultados (si los hay) pueden ir a una `Queue` de salida normal. El Maestro, después de poner todas las tareas, debe llamar a `join()` en la `JoinableQueue` de entrada para esperar a que todas las tareas sean procesadas antes de recolectar los resultados de la cola de salida y terminar.

#### Ejercicio Resuelto: Log Distribuido con `Queue`
```python
from multiprocessing import Process, Queue, current_process
import time
import logging
import random # Añadido para el sleep

# Configuración básica de logging para el proceso logger
# Esto solo se configura en el proceso logger.
def setup_logger():
    logger = logging.getLogger('distributed_logger')
    logger.setLevel(logging.INFO)
    # Evitar añadir múltiples handlers si la función se llama varias veces
    if not logger.handlers: 
        fh = logging.FileHandler('distributed_app.log', mode='w') # 'w' para empezar limpio
        formatter = logging.Formatter('%(asctime)s - %(processName)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    return logger

def logger_process_q(queue): # Renombrado
    """ Proceso dedicado a escribir logs desde una cola. """
    logger = setup_logger()
    print("Logger Process (Queue): Iniciado y esperando mensajes.")
    while True:
        try:
            # Espera por un mensaje, con timeout para permitir cierre si es necesario
            record = queue.get(timeout=1) 
            if record == "STOP_LOGGING":
                logger.info("Señal de parada recibida. Terminando logger.")
                print("Logger Process (Queue): Señal de parada recibida. Terminando.")
                break
            logger.info(record)
        except Exception: # queue.Empty si hay timeout y nada en la cola
            # Si la cola está vacía, simplemente continuamos esperando.
            # Podríamos añadir lógica aquí para terminar si no hay actividad por mucho tiempo.
            pass 
    print("Logger Process (Queue): Terminado.")

def worker_process_q_log(log_queue, worker_id): # Renombrado
    """ Worker que realiza trabajo y envía logs a la cola. """
    proc_name = current_process().name # Para incluir en el log
    for i in range(5):
        msg = f"Worker {worker_id} ({proc_name}): Realizando paso {i}"
        print(msg) # También imprime en consola para ver actividad
        log_queue.put(msg) # Envía el mensaje al proceso logger
        time.sleep(random.uniform(0.3, 1.0))
    log_queue.put(f"Worker {worker_id} ({proc_name}): Trabajo finalizado.")
    print(f"Worker {worker_id} ({proc_name}): Trabajo finalizado y mensaje enviado.")

if __name__ == '__main__':
    log_queue_ex = Queue() # Renombrado
    
    logger_p = Process(target=logger_process_q, args=(log_queue_ex,), name="LoggerProcess") # Renombrado
    logger_p.start()

    worker_procs = [Process(target=worker_process_q_log, args=(log_queue_ex, i), name=f"Worker-{i}") for i in range(3)] # Renombrado
    for w in worker_procs:
        w.start()

    # Espera a que los workers terminen
    for w in worker_procs:
        w.join()
    print("Todos los workers (Queue-Log) han terminado.")

    # Envía la señal de parada al logger
    log_queue_ex.put("STOP_LOGGING")
    
    # Espera a que el logger termine
    logger_p.join(timeout=5) # Añade timeout por si acaso
    if logger_p.is_alive():
        print("Logger process (Queue-Log) no terminó a tiempo, forzando.")
        logger_p.terminate()
        logger_p.join()

    print("Todos los procesos (Queue-Log) terminados. Revisa 'distributed_app.log'.")
```
**Explicación**: Varios procesos `worker` realizan trabajo y, en lugar de escribir directamente en un archivo (lo cual requeriría un `Lock` y podría ser un cuello de botella), envían sus mensajes de log a una `Queue`. Un único proceso `logger_process_q` se encarga de tomar los mensajes de la `Queue` y escribirlos de forma segura y ordenada en un archivo de log usando el módulo `logging`. Esto centraliza la escritura y desacopla la lógica de logging del trabajo principal de los workers.

---

## 9. Value: El Valor Compartido

### 9.1. ¿Qué es y qué hace?
`Value` permite crear un **objeto de memoria compartida** que puede almacenar **un único valor** de un tipo de dato C específico (definido usando `ctypes`). Es útil para compartir variables simples como contadores, flags o estados entre procesos. [cite: fileName: Sincronización en Python con multiprocessing, fileName: shared0.py]

### 9.2. ¿Cuándo usarlo? (Casos de Uso Prácticos)
Se usa cuando necesitas que varios procesos lean y/o escriban una variable simple y compartida.

* **Contadores Compartidos**: Como en el `crash_problem.py`, aunque requiere un `Lock` para operaciones no atómicas.

* **Flags de Estado**: Un proceso puede establecer un `Value` para indicar un estado global que otros procesos pueden leer.

* **Resultados Simples**: Un proceso trabajador puede poner su resultado final (si es un número o booleano) en un `Value`.

### 9.3. Consideraciones Técnicas Clave

* **`ctypes`**: Debes especificar el tipo de dato C usando `ctypes` (ej: `ctypes.c_int`, `ctypes.c_float`, `ctypes.c_bool`).

* **`.value`**: Se accede al valor real a través del atributo `.value`.

* **Atomicidad y Locks**: **¡CRUCIAL!** El acceso (lectura/escritura) a `Value` *no* es inherentemente atómico para operaciones compuestas como `v.value += 1`. [cite: fileName: crash_problem.py] Para protegerlo, debes usar el `Lock` asociado que `Value` puede proporcionar: `with v.get_lock(): v.value += 1`, o un `Lock` externo. Si *solo* necesitas atomicidad para tipos simples y el SO lo soporta (y estás seguro de las implicaciones), a veces se puede omitir el lock para operaciones simples de asignación o lectura, pero es mucho más seguro usarlo explícitamente para cualquier operación de lectura-modificación-escritura.

* **Overhead**: Es más ligero que `Queue` para compartir un solo dato, pero requiere gestión manual de la sincronización.

### 9.4. Ejemplo Práctico (Contador Seguro con Value y Lock)
```python
from multiprocessing import Process, Value, Lock
import ctypes
import time

def modifier_value(shared_value, lock): # Renombrado
    """ Incrementa el valor compartido 10000 veces de forma segura. """
    for _ in range(10000):
        with lock: # Usa el lock para proteger la operación RMW (Read-Modify-Write)
            shared_value.value += 1

def reader_value(shared_value, lock): # Renombrado
    """ Lee el valor periódicamente de forma segura. """
    for i in range(5):
        with lock: # También usa lock para lectura consistente
            print(f"Lector (Value): Valor actual en iteración {i} = {shared_value.value}")
        time.sleep(0.5)

if __name__ == '__main__':
    # 'i' para entero C, 0 es el valor inicial
    v_ex = Value(ctypes.c_int, 0) # Renombrado
    # Creamos un Lock explícito para proteger v_ex. Alternativamente, v_ex.get_lock()
    l_val = Lock() # Renombrado

    m1_val = Process(target=modifier_value, args=(v_ex, l_val)) # Renombrado
    m2_val = Process(target=modifier_value, args=(v_ex, l_val)) # Renombrado
    r_val = Process(target=reader_value, args=(v_ex, l_val)) # Renombrado

    m1_val.start()
    m2_val.start()
    r_val.start()

    m1_val.join()
    m2_val.join()
    r_val.join()

    # Leer el valor final (también debería estar protegido si otros procesos aún pudieran modificarlo)
    with l_val:
        final_val = v_ex.value
    print(f"Valor final (Value): {final_val}") # Debería ser 20000
```
**Explicación**: Se crea un `Value` de tipo entero. Se crea un `Lock` separado (también se podría usar `v_ex.get_lock()`). Los procesos `modifier_value` usan `with lock:` para asegurar que la operación `+=` (lectura-modificación-escritura) sea atómica. El lector `reader_value` también usa el lock para obtener una lectura consistente del valor mientras está siendo modificado. [cite: fileName: Sincronización en Python con multiprocessing]

### 9.5. Ejercicios

#### Ejercicio Propuesto: Termómetro Global con `Value`
Simula varios sensores (procesos) que miden la temperatura y actualizan tres `Value`s compartidos: `temperatura_actual`, `temperatura_maxima`, y `temperatura_minima`. Asegúrate de usar `Lock`s (preferiblemente `get_lock()` de cada `Value` o locks individuales) para proteger el acceso y las actualizaciones (especialmente para `maxima` y `minima`, que requieren leer y luego posiblemente escribir). Un proceso "Display" debe leer estos valores periódicamente y mostrarlos.

#### Ejercicio Resuelto: Flag de Parada con `Value`
```python
from multiprocessing import Process, Value, Lock
import ctypes
import time

def worker_stoppable_value(stop_flag, lock, worker_id): # Renombrado
    """ Trabaja hasta que el flag de parada (un Value) se active. """
    count = 0
    while True:
        with lock: # Necesario para leer el flag de forma segura
            if stop_flag.value == 1: # 1 significa parar
                print(f"Worker {worker_id} (Value-Flag): ¡Señal de parada recibida! Terminando tras {count} iteraciones.")
                break
        
        print(f"Worker {worker_id} (Value-Flag): Trabajando (iteración {count})...")
        count += 1
        time.sleep(random.uniform(0.5,1.0)) # Simula trabajo

def manager_value_flag(stop_flag, lock): # Renombrado
    """ Espera un tiempo y luego activa el flag de parada. """
    duration = 5
    print(f"Manager (Value-Flag): Workers trabajando por {duration} segundos...")
    time.sleep(duration)
    print("Manager (Value-Flag): ¡Enviando señal de parada!")
    with lock:
        stop_flag.value = 1 # Establece el flag a 1

if __name__ == '__main__':
    # 'i' para entero C, 0 es el valor inicial (0=seguir, 1=parar)
    flag_val = Value(ctypes.c_int, 0) # Renombrado
    lock_flag = Lock() # Renombrado

    workers_vf = [Process(target=worker_stoppable_value, args=(flag_val, lock_flag, i)) for i in range(3)] # Renombrado
    mgr_vf = Process(target=manager_value_flag, args=(flag_val, lock_flag)) # Renombrado

    for w in workers_vf:
        w.start()
    mgr_vf.start()

    for w in workers_vf:
        w.join()
    mgr_vf.join()
    print("Sistema (Value-Flag) terminado.")
```
**Explicación**: Se usa un `Value` como flag booleano (representado por 0 y 1). Los `worker`s lo comprueban periódicamente (dentro de un `Lock` para lectura segura) para ver si deben parar. El `manager` espera y luego establece el flag (también dentro de un `Lock` para escritura segura), causando que los workers terminen su bucle.

---

## 10. Array: El Arreglo Compartido

### 10.1. ¿Qué es y qué hace?
`Array` permite crear un **arreglo de memoria compartida**, similar a `Value` pero para **múltiples elementos**. Todos los elementos del `Array` deben ser del **mismo tipo de dato C** (`ctypes`). Permite el acceso por índice y slicing. [cite: fileName: Sincronización en Python con multiprocessing, fileName: shared0.py]

### 10.2. ¿Cuándo usarlo? (Casos de Uso Prácticos)
Se usa cuando necesitas que varios procesos lean y/o escriban en una **estructura de datos tipo arreglo o buffer**.

* **Buffers Compartidos**: Un proceso escribe datos en el `Array`, otro los lee.

* **Procesamiento de Datos Paralelo**: Cada proceso trabaja sobre una sección diferente del `Array`.

* **Almacenamiento de Estado Distribuido**: Cada proceso maneja un índice del `Array` para su propio estado, pero otros pueden consultarlo.

* **Matrices Compartidas**: Se pueden representar matrices aplanándolas en un `Array` unidimensional.

### 10.3. Consideraciones Técnicas Clave

* **`ctypes` y Tamaño**: Debes especificar el tipo de dato C y el tamaño del `Array` al crearlo. El tamaño es fijo una vez creado.

* **Acceso**: Se accede como una lista (ej: `arr[i] = x`, `print(arr[:])`).

* **Sincronización**: **¡CRUCIAL!** Al igual que `Value`, el acceso a los elementos de `Array` *no* es inherentemente seguro si múltiples procesos pueden modificar el mismo índice o si hay lecturas y escrituras concurrentes. Necesitas usar un `Lock` para proteger el acceso. Puedes usar un `Lock` general para todo el array, o el `Lock` asociado con `arr.get_lock()`. Para mayor granularidad (y potencial paralelismo si los procesos trabajan en diferentes secciones), podrías usar un array de Locks, uno por elemento o sección, pero esto añade complejidad.

### 10.4. Ejemplo Práctico (Llenado Paralelo de Array)
```python
from multiprocessing import Process, Array, Lock
import ctypes
import random

def fill_array_parallel(arr, lock, start_index, count, value_base, process_id): # Renombrado
    """ Rellena una porción del array de forma segura. """
    for i in range(count):
        index_to_fill = start_index + i
        # Simula algún cálculo para el valor
        value_to_write = value_base + random.randint(0, i*10) 
        with lock: # Protege la escritura en el índice específico
            arr[index_to_fill] = value_to_write
            print(f"Proceso {process_id} (Array): Escribió {arr[index_to_fill]} en índice {index_to_fill}")
        time.sleep(random.uniform(0.01, 0.05)) # Simula trabajo

if __name__ == '__main__':
    ARRAY_SIZE = 10 # Renombrado
    # 'i' para entero C, ARRAY_SIZE es el tamaño
    shared_array_ex = Array(ctypes.c_int, ARRAY_SIZE) # Renombrado
    # Usamos el lock interno del Array o un Lock externo
    lock_arr = shared_array_ex.get_lock() # Renombrado
    # Alternativamente: lock_arr = Lock()

    # Proceso 1 llena la primera mitad
    p1_arr = Process(target=fill_array_parallel, args=(shared_array_ex, lock_arr, 0, ARRAY_SIZE // 2, 100, 1))
    # Proceso 2 llena la segunda mitad
    p2_arr = Process(target=fill_array_parallel, args=(shared_array_ex, lock_arr, ARRAY_SIZE // 2, ARRAY_SIZE - (ARRAY_SIZE // 2), 200, 2))

    # Imprime el estado inicial (antes de que los procesos escriban)
    # Es importante notar que si se accede aquí sin lock mientras los workers están activos,
    # se podría obtener un estado inconsistente.
    with lock_arr:
        print(f"Array inicial (Array): {shared_array_ex[:]}")
    
    p1_arr.start()
    p2_arr.start()
    p1_arr.join()
    p2_arr.join()
    
    with lock_arr: # Proteger la lectura final también
        print(f"Array final (Array): {shared_array_ex[:]}")
```
**Explicación**: Se crea un `Array` de 10 enteros. Dos procesos lo llenan, cada uno en su mitad. Se usa un `Lock` (obtenido de `shared_array_ex.get_lock()`) para proteger cada escritura individual. Aunque en este caso particular los procesos escriben en índices diferentes y no superpuestos, usar el lock es una buena práctica, especialmente si hubiera lecturas concurrentes o si la lógica de asignación de índices fuera más compleja. [cite: fileName: Sincronización en Python con multiprocessing]

### 10.5. Ejercicios

#### Ejercicio Propuesto: Histograma Concurrente con `Array`
Crea un `Array` compartido para representar los "bins" de un histograma (por ejemplo, 10 bins para números de 0 a 99). Lanza N procesos. Cada proceso debe generar M números aleatorios (entre 0 y 99) y, por cada número, incrementar el bin correspondiente en el `Array` compartido. Asegúrate de usar un `Lock` (puede ser el `get_lock()` del `Array` o un `Lock` externo) para proteger las operaciones de incremento en cada bin. Al final, imprime el histograma resultante.

#### Ejercicio Resuelto: Inversión de Arreglo Paralelo con `Array`
```python
from multiprocessing import Process, Array, Lock
import ctypes
import time # Necesario para time.sleep

def swap_elements_array(arr, lock, index1, index2, worker_id): # Renombrado
    """ Intercambia dos elementos del array de forma segura. """
    with lock:
        # Guardamos temporalmente antes de que otro proceso pueda cambiarlo
        # Esto es crucial si el lock es granular y otro proceso podría estar
        # modificando index2 mientras este proceso lee index1.
        # Con un lock global para todo el array, es menos crítico pero buena práctica.
        temp = arr[index1]
        arr[index1] = arr[index2]
        arr[index2] = temp
        print(f"Worker {worker_id} (Array-Rev): Intercambió arr[{index1}] ({arr[index2]}) <-> arr[{index2}] ({temp})")
    # Simula un poco de trabajo o retardo
    time.sleep(random.uniform(0.01, 0.05))


def parallel_reverser_array(arr, lock, worker_id, num_total_workers, array_size): # Renombrado
    """ 
    Invierte el array de forma paralela. Cada worker se encarga de una
    fracción de los intercambios necesarios.
    """
    # Cada worker procesa un subconjunto de los pares a intercambiar.
    # El bucle va hasta la mitad del array.
    # El 'step' es num_total_workers para que cada worker tome un par,
    # luego el siguiente worker tome el siguiente, y así sucesivamente.
    for i in range(worker_id, array_size // 2, num_total_workers):
        j = array_size - 1 - i
        # Solo hacemos el swap si i y j son diferentes (para arrays de tamaño impar, el del medio no se mueve)
        if i < j : # Asegura que no intentemos swapear el mismo elemento consigo mismo ni crucemos
            swap_elements_array(arr, lock, i, j, worker_id)


if __name__ == '__main__':
    ARRAY_REV_SIZE = 11 # Renombrado
    NUM_REV_WORKERS = 2 # Renombrado
    
    # 'i' para entero C, creamos el array [0, 1, 2, ..., ARRAY_REV_SIZE-1]
    my_array_rev = Array(ctypes.c_int, list(range(ARRAY_REV_SIZE))) # Renombrado
    lock_rev = my_array_rev.get_lock() # Renombrado

    with lock_rev: # Leer estado inicial de forma segura
        print(f"Array inicial (Array-Rev): {my_array_rev[:]}")
    
    processes_rev = [] # Renombrado
    for i in range(NUM_REV_WORKERS):
        p = Process(target=parallel_reverser_array, args=(my_array_rev, lock_rev, i, NUM_REV_WORKERS, ARRAY_REV_SIZE))
        processes_rev.append(p)
        p.start()

    for p in processes_rev:
        p.join()

    with lock_rev: # Leer estado final de forma segura
        print(f"Array final (Array-Rev):   {my_array_rev[:]}")

```
**Explicación**: La versión `parallel_reverser_array` divide el trabajo de invertir un arreglo entre varios workers. Cada worker se encarga de una parte de los intercambios necesarios (i-ésimo con N-1-i). Se usa un `Lock` global (obtenido del `Array`) para proteger *cada operación de intercambio* (`swap_elements_array`), asegurando que dos procesos no intenten modificar los mismos elementos o elementos conflictivos al mismo tiempo. Esto garantiza que la inversión se realice correctamente, aunque la concurrencia se limita a nivel de swaps individuales.


# Dudas sobre el TP1

El generador:
```python
def generar_dato():
    '''
    Genera un diccionario por segundo:
    {
       "timestamp": "YYYY-MM-DDTHH:MM:SS",
       "frecuencia": int(60-180),
       "presion": [int(110-180), int(70-110)],
       "oxigeno": int(90-100)
    }
    '''
    # Devuelve un diccionario con los campos frecuencia, presión y oxígeno
    # {"timestamp": "2025-06-11T15:32:09", "frecuencia": 122, "presion": [166, 99], "oxigeno": 100}
    dato = json.dumps({
        "timestamp": datetime.now().isoformat(timespec='seconds'),
        "frecuencia": random.randint(60, 180),
        "presion": [random.randint(110, 180), random.randint(70, 110)], # [sistolica, diastolica]
        "oxigeno": random.randint(90, 100)
    })

def generar(pipe_frec,pipe_press,pipe_ox):
    for i in range(60):
        dato = generar_dato()
        pipe_frec.send(dato)
        pipe_press.send(dato)
        pipe_ox.send(dato)
        time.sleep(1)
```
Genera el json de dato cada 1 segundo. Luego se manda el mismo json a los 3 pipes, y cada analizador separa los datos. Esto se podría hacer directamente en el generador. Que directamente envíe los datos que corresponden a cada analizador.