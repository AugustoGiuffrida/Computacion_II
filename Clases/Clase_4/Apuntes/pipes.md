# 1. Fundamentos teóricos de Pipes
## ¿Qué es un pipe?

Un pipe (o "tubería") es un mecanismo de comunicación unidireccional entre procesos que permite que la salida de un proceso se utilice como entrada de otro. Su uso está muy relacionado con el principio de composición de procesos, común en sistemas UNIX y Linux.

> 📌 Se utilizan para que dos procesos (padre-hijo o independientes, según el tipo de pipe) se comuniquen sin necesidad de recurrir a archivos intermedios.

## Características principales
- Comunicación unidireccional: un extremo escribe, el otro lee.

- Implementado en el núcleo del sistema operativo.

- El buffer intermedio entre lectura y escritura evita bloqueos inmediatos, pero tiene capacidad limitada.

- Los pipes tradicionales (anónimos) solo funcionan entre procesos con un ancestro común (por ejemplo, padre-hijo).

- Existe también la variante named pipe (FIFO), que permite comunicación entre procesos no relacionados directamente.

## Importancia de los pipes en sistemas operativos
- Son una forma eficiente y simple de IPC (Inter Process Communication).
- Refuerzan el modelo de diseño "divide y vencerás", al permitir que un proceso realice una tarea específica y pase el resultado a otro.
- Se usan ampliamente en scripts de shell


# 2. Implementación interna y ciclo de vida de un pipe
## ¿Cómo se implementa un pipe en el sistema operativo?

Cuando un proceso crea un pipe, el sistema operativo:

1. Reserva un área de memoria en el kernel, que funcionará como buffer circular.

2. Crea dos descriptores de archivo:
    - Uno para escritura.
    - Otro para lectura.

3. Estos descriptores se usan como si fueran archivos normales, pero en lugar de apuntar a disco, están conectados a ese buffer en memoria.

>📌 Internamente, el pipe está gestionado como una estructura con:

- Cabezal de lectura
- Cabezal de escritura
- Límites del buffer

## Ciclo de vida típico de un pipe
1. Un proceso (padre) crea un pipe (con pipe() en C o os.pipe() en Python).

2. El proceso se bifurca (fork() en C o multiprocessing en Python).

3. El pipe se hereda: ambos procesos (padre e hijo) pueden acceder a los 
descriptores.
4. Cada proceso cierra el extremo que no va a usar.

5. Uno escribe datos, el otro los lee.

6. Cuando se termina de escribir o leer, se cierran ambos extremos y el pipe se elimina automáticamente.

>🔒 Importante: si ningún proceso lee, y uno escribe mucho, el buffer se llena y el proceso escritor se bloquea. Esto puede llevar a un deadlock si no se maneja bien.

# 3. Implementación de Pipes en Python

## Módulos relevantes

Para trabajar con pipes en Python, se puede usar:

- `os.pipe()`: para crear pipes de bajo nivel, similar a C.

- `multiprocessing.Pipe()`: para comunicación entre procesos usando la librería multiprocessing.

>🔧 En esta sección, nos enfocaremos en os.pipe() porque se alinea más con el modelo clásico de IPC en sistemas operativos.

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

# 4. Ejercicios prácticos con patrones más avanzados
Un pipeline es cuando la salida de un proceso se conecta como entrada del siguiente, tal como en:
```bash
ls | grep ".py" | sort
```
Vamos a replicar algo similar en Python: tres procesos que simulan este encadenamiento.

## 📄 Ejemplo: pipeline de 3 procesos

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

# 5. 🧯 Estrategias para prevenir problemas comunes con pipes

Cuando trabajás con pipes en programación concurrente, hay varios problemas clásicos que pueden aparecer. Acá van las estrategias clave para evitarlos:
## 🛑 1. Evitar bloqueos (deadlocks)

- Cerrá los extremos no utilizados tan pronto como sea posible.

    ⛔ Si un proceso está esperando leer y nadie cierra el extremo de escritura, se queda bloqueado esperando EOF.

- Escribí solo cuando el lector está listo, especialmente en comunicación circular.

    ⚠️ En comunicaciones recíprocas (padre↔hijo), usar turnos estrictos o señalización.

    - No uses read() sin control si no sabés cuánto esperar.
    - Usá readline() o delimitadores, y evitá bucles while True sin condiciones de corte.

## 🧼 2. Evitar fugas de descriptores

- Cada pipe() devuelve dos descriptores: si no los usás, cerralos.
- Después de un fork(), cada proceso debe cerrar los extremos que no usará.
- Si un proceso mantiene abierto un descriptor de escritura innecesario, los lectores se bloquean indefinidamente esperando datos.

## 🔐 3. Controlar la sincronización

- Los pipes no tienen control de concurrencia incorporado.

    Si múltiples procesos escriben al mismo pipe, y los mensajes son grandes (> `PIPE_BUF`), los datos pueden entremezclarse.

- Soluciones posibles:

    - Garantizar que cada pipe tenga un solo escritor y un solo lector.

    - Usar multiprocessing.Pipe() o Queue() en lugar de os.pipe() cuando sea posible (veremos esto si avanzás a Python multiprocessing).

    - Implementar tu propio protocolo: delimitar los mensajes, esperar confirmaciones, etc.

## 🔎 4. Debugging de pipes

- Si tu programa se queda colgado, preguntate:

    - ¿Todos los extremos innecesarios están cerrados?

    - ¿Hay algún read() esperando EOF que nunca llegará?

    - ¿Se escribió más de lo permitido sin leer?

- Podés usar comandos como lsof -p <PID> para ver qué descriptores siguen abiertos.

## 5. Buenas prácticas

- Usar os.fdopen() si vas a trabajar con texto.

- Cerrar los descriptores innecesarios en cada proceso.

- Manejar correctamente el orden de lectura/escritura.

- Asegurar que no haya escrituras simultáneas sin control.

- Leer hasta recibir EOF o tener delimitadores claros.

- Documentar los pipes y roles de cada proceso.