# 🧩 a) Fundamentos de procesos y programación concurrente
## 📘 Explicación teórica

### ¿Qué es un proceso?
Un proceso es una instancia de un programa en ejecución. Tiene su propio espacio de memoria, registros de CPU, pila y otras estructuras internas que permiten su ejecución independiente.

### ¿Qué es un hilo?
Un hilo (o thread) es una unidad de ejecución dentro de un proceso. Comparte la memoria del proceso principal con otros hilos, lo que facilita la comunicación entre ellos pero puede generar conflictos si no se sincronizan bien.

### 🆚 Diferencias clave entre procesos e hilos
| Característica | Procesos                        | Hilos                           |
| -------------- | ------------------------------- | ------------------------------- |
| Memoria        | Separada                        | Compartida                      |
| Comunicación   | Más costosa (ej. pipes, queues) | Más rápida (memoria compartida) |
| Seguridad      | Mayor aislamiento               | Menor aislamiento               |
| Uso en Python  | multiprocessing                 | threading                       |

### ✅ ¿Cuándo usar multiprocessing en Python?
- Cuando necesitas usar múltiples núcleos del CPU.
- Cuando las tareas son pesadas en cómputo (CPU-bound).
- Cuando el Global Interpreter Lock (GIL) limita el uso de hilos en Python.

### 🔄 Ciclo de vida de un proceso
- Creación: El proceso es creado desde el proceso padre.
- Ejecución: Comienza a correr su código.
- Espera (wait): Puede esperar por E/S o a otros procesos.
- Terminación: Termina normalmente o por error, liberando recursos.

### 🧪 Ejemplo básico: creación de un proceso

```py
from multiprocessing import Process
import os

def tarea():
    print(f"Proceso hijo: PID = {os.getpid()}")

if __name__ == '__main__':
    print(f"Proceso padre: PID = {os.getpid()}")
    p = Process(target=tarea)
    p.start()
    p.join()
```

# 🔧 b) Creación y gestión de procesos con la biblioteca multiprocessing

## 📘 Explicación teórica

En Python, la biblioteca multiprocessing permite crear y gestionar procesos de forma sencilla, aprovechando múltiples núcleos del procesador.

### ✅ Clase Process
Es la base para crear un nuevo proceso. Podés pensarla como un objeto que representa una nueva ejecución independiente de código.

```py
from multiprocessing import Process
```

**🔑 Métodos esenciales**
- start(): inicia el proceso.
- join(): espera que el proceso termine.
- is_alive(): devuelve True si el proceso sigue en ejecución.
- terminate(): fuerza la terminación del proceso (con precaución).

**📌 Ejemplo práctico detallado**

```py
from multiprocessing import Process
import os
import time

def tarea():
    print(f"[Hijo] PID = {os.getpid()}")
    time.sleep(2)
    print("[Hijo] Termina su ejecución")

if __name__ == '__main__':
    print(f"[Padre] PID = {os.getpid()}")
    proceso = Process(target=tarea)

    proceso.start()  # Inicia el proceso hijo
    print(f"[Padre] ¿Sigue vivo el hijo? {proceso.is_alive()}")
    
    proceso.join()   # Espera a que termine
    print(f"[Padre] ¿Sigue vivo el hijo después de join()? {proceso.is_alive()}")
```

**🔍 Gestión de procesos padre e hijo**
- El proceso padre es quien crea y controla el hijo.
- Cada proceso tiene su propio PID (Identificador de Proceso).
- En Linux podés verificar esto con herramientas como ps, htop, o mirando /proc.

# 🧩 c) Comunicación entre procesos

## 📘 Fundamento teórico

Cuando trabajás con multiprocessing, los procesos no comparten memoria. Esto significa que no podés pasar variables directamente entre ellos, como sí ocurre con los hilos.

🔴 Por eso es necesario un mecanismo que permita el intercambio de información. Los dos más comunes en multiprocessing son:

### 🔗 Pipes (tuberías)

**Concepto:**
- Conectan dos procesos: uno escribe y el otro lee.
- Comunicación unidireccional o bidireccional (según cómo se use).
- Parecidos a los pipes en UNIX.

### Implementación básica:

```py
from multiprocessing import Process, Pipe

def hijo(conn):
    conn.send("Mensaje desde el hijo")
    conn.close()

if __name__ == '__main__':
    parent_conn, child_conn = Pipe()
    p = Process(target=hijo, args=(child_conn,))
    p.start()
    
    print(parent_conn.recv())  # Espera y recibe mensaje del hijo
    
    p.join()
```

📌 Pipe() devuelve dos extremos: conn1, conn2. Ambos pueden enviar y recibir si lo necesitás.

### 📦 Queues (colas)

**Concepto:**
- Permiten comunicación entre múltiples procesos.
- Internamente utilizan una cola segura y sincronizada.
- Ideal para enviar varios mensajes o tareas entre procesos.

**Implementación básica:**

```py
from multiprocessing import Process, Queue

def hijo(q):
    q.put("Mensaje del hijo")

if __name__ == '__main__':
    q = Queue()
    p = Process(target=hijo, args=(q,))
    p.start()
    
    print(q.get())  # Espera y obtiene mensaje
    
    p.join()
```    

📌 Queue() permite put() para enviar y get() para recibir mensajes, en forma segura.

### 🔍 Comparación rápida
| Característica           | `Pipe`                       | `Queue`                                     |
| ------------------------ | ---------------------------- | ------------------------------------------- |
| Comunicación             | Punto a punto (dos extremos) | Multipunto (varios procesos)                |
| Seguridad/sincronización | Manual                       | Automática                                  |
| Casos ideales            | Simple entre 2 procesos      | Comunicación múltiple, productor/consumidor |


# 🛡️ d) Sincronización básica con Lock

## 📘 Fundamento teórico

Cuando varios procesos acceden al mismo recurso compartido (por ejemplo, una Queue, un archivo o una sección crítica del código), puede haber condiciones de carrera. Esto ocurre si los accesos son concurrentes y no están controlados, provocando resultados erróneos o inconsistentes.

🔐 Para evitar esto, Python proporciona Locks (cerrojos) en el módulo multiprocessing.

### 🔧 ¿Qué es un Lock?

Un Lock (cerrojo) actúa como una puerta exclusiva:
- Solo un proceso puede pasar a la vez.
- Los demás deben esperar hasta que el lock se libere.

✍️ Sintaxis básica:

```py
from multiprocessing import Process, Lock

def tarea(lock, n):
    lock.acquire()
    try:
        print(f'Proceso {n} está escribiendo...')
    finally:
        lock.release()

if __name__ == '__main__':
    lock = Lock()
    for i in range(3):
        Process(target=tarea, args=(lock, i)).start()
```

### 🧠 ¿Cuándo usar un Lock?
- Cuando varios procesos modifican un mismo recurso (archivo, estructura compartida, consola).
- Para asegurar que solo un proceso a la vez accede a una sección crítica del código.
- En modelos como productor-consumidor, si el acceso no está mediado por Queue.

⚠️ Cuidado: usar locks incorrectamente puede llevar a deadlocks (bloqueos mutuos).


# 🔄 e) Uso de Pool para procesos simultáneos

## 📘 Fundamento teórico

Cuando necesitás ejecutar muchas tareas similares, como procesar una lista de elementos, usar multiprocessing.Process uno por uno puede ser ineficiente y engorroso.

📌 Para esto, Python ofrece Pool, que permite:

- Crear un conjunto fijo de procesos (pool).
- Distribuir automáticamente las tareas entre esos procesos.
- Reutilizar los procesos sin crear uno nuevo por cada tarea.

### 🧠 ¿Por qué usar Pool?

✅ Ventajas:
- Ahorra recursos: no se crean procesos nuevos todo el tiempo.
- Fácil de usar con colecciones de datos.
- Se adapta muy bien a paralelismo de tareas independientes (por ejemplo, procesar archivos, aplicar funciones a una lista).

### 🔧 Sintaxis básica:

```py
from multiprocessing import Pool

def cuadrado(n):
    return n * n

if __name__ == '__main__':
    with Pool(processes=4) as pool:
        resultados = pool.map(cuadrado, [1, 2, 3, 4, 5])
        print(resultados)
```
📌 Esto crea 4 procesos que ejecutan cuadrado() sobre cada número en paralelo.

### Métodos más usados de Pool:
| Método                | ¿Qué hace?                                                      |
| --------------------- | --------------------------------------------------------------- |
| `map(func, iterable)` | Aplica `func` a cada elemento del iterable. Devuelve una lista. |
| `apply(func, args)`   | Ejecuta `func(*args)` en un solo proceso del pool.              |
| `close()` y `join()`  | Cierra el pool y espera a que terminen los procesos.            |


# 🧠 f) Memoria compartida básica

## 📘 Fundamento teórico

En multiprocessing, cada proceso tiene su propio espacio de memoria, lo que significa que las variables globales no se comparten automáticamente.

Pero a veces sí necesitamos compartir datos, como un contador o una lista que todos los procesos puedan modificar.

📌 Para esto, Python ofrece:
- Value → para compartir un solo valor (int, float, etc.)
- Array → para compartir una colección de datos (lista fija)

Ambos se importan desde multiprocessing.

### 🔧 Ejemplo: Value

```py
from multiprocessing import Process, Value
import time

def incrementar(contador):
    for _ in range(100):
        time.sleep(0.01)
        with contador.get_lock():  # Acceso sincronizado
            contador.value += 1

if __name__ == '__main__':
    contador = Value('i', 0)  # 'i' = entero
    p1 = Process(target=incrementar, args=(contador,))
    p2 = Process(target=incrementar, args=(contador,))
    p1.start()
    p2.start()
    p1.join()
    p2.join()
    print("Valor final:", contador.value)  # Debería ser 200
```
📌 Value('i', 0) crea un entero compartido entre procesos.


### 🔧 Ejemplo: Array

```py
from multiprocessing import Process, Array

def llenar(arr):
    for i in range(len(arr)):
        arr[i] = i * i

if __name__ == '__main__':
    datos = Array('i', 5)  # array de 5 enteros
    p = Process(target=llenar, args=(datos,))
    p.start()
    p.join()
    print(list(datos))  # [0, 1, 4, 9, 16]
```