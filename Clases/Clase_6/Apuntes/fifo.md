# 1. ¿Qué es un FIFO (Named Pipe)?

## Concepto teórico
Un FIFO (First In, First Out), también llamado pipe con nombre (named pipe), es un tipo especial de archivo en Unix/Linux que permite la comunicación entre procesos de forma unidireccional, como los pipes anónimos, pero con una gran diferencia: existe en el sistema de archivos como un archivo especial.

Esto significa que:
- Puede ser creado y referenciado por nombre, lo cual permite que procesos que no tienen relación de parentesco (por ejemplo, que no son padre e hijo) puedan comunicarse.

- A diferencia de los pipes anónimos, que solo existen mientras viven los procesos relacionados, los FIFOs existen en el sistema de archivos hasta que se eliminan manualmente.

Se comportan como archivos: se pueden abrir con open(), leer con read(), escribir con write(), y eliminar con unlink().


# 2. Creación y uso básico de FIFOs en Python

## Parte teórica

Para trabajar con FIFOs en Python, usamos funciones del módulo os:

- os.mkfifo(path): Crea un FIFO en la ruta indicada.
- open(path, mode): Abre el FIFO para lectura ('r') o escritura ('w').
- os.remove(path): Elimina el FIFO del sistema de archivos.

**Importante:**
- Si abrís un FIFO para lectura y no hay escritor, se bloquea hasta que alguien lo abra para escritura.
- Lo mismo ocurre al revés: si abrís para escritura y no hay lector, el proceso se bloquea.

Esto refleja cómo los FIFOs esperan una conexión completa para operar correctamente.

## Parte práctica: Crear y usar un FIFO

Vamos a crear un script Python que cree un FIFO, y luego dos scripts distintos: uno para escribir y otro para leer.

### Paso 1: Crear el FIFO (script de setup)

```py
import os

fifo_path = "/tmp/mi_fifo"

if not os.path.exists(fifo_path):
    os.mkfifo(fifo_path)
    print(f"FIFO creado en {fifo_path}")
else:
    print("El FIFO ya existe.")
```

### Paso 2: Script escritor

```py
# escritor.py
with open("/tmp/mi_fifo", "w") as fifo:
    fifo.write("Hola desde el proceso escritor\n")
```

### Paso 3: Script lector

```py
# lector.py
with open("/tmp/mi_fifo", "r") as fifo:
    mensaje = fifo.readline()
    print(f"Mensaje recibido: {mensaje}")
```

# 3. Cursor y descriptores en FIFOs

## Teoría: ¿Los procesos comparten el cursor en un FIFO?
Un FIFO no guarda estado de lectura/escritura entre procesos. Esto significa:

- Cada proceso que abre un FIFO recibe un descriptor independiente.
- No hay cursor compartido entre lectores o escritores.
- Si dos procesos abren un FIFO en modo lectura al mismo tiempo:
    - Ambos pueden leer el mismo contenido si lo hacen antes que se consuma.
    - Pero no comparten la posición de lectura automáticamente

## Práctica: Demostrar que dos procesos lectores no comparten cursor

### Paso 1: Crear el FIFO (si no existe)
```py
import os
fifo_path = "/tmp/fifo_cursor"
if not os.path.exists(fifo_path):
    os.mkfifo(fifo_path)
```

### Paso 2: Script escritor
```py
# escritor_cursor.py
with open("/tmp/fifo_cursor", "w") as f:
    f.write("Primera línea\n")
    f.write("Segunda línea\n")
    f.write("Tercera línea\n")
```

### Paso 3: Script lector A
```py
# lector_a.py
with open("/tmp/fifo_cursor", "r") as f:
    linea = f.readline()
    print(f"Lector A recibió: {linea}")
```

### Paso 4: Script lector B
```py
# lector_b.py
with open("/tmp/fifo_cursor", "r") as f:
    linea = f.readline()
    print(f"Lector B recibió: {linea}")
```

### Ejecutá así:

- Terminal 1: python3 lector_a.py (queda esperando)
- Terminal 2: python3 lector_b.py (queda esperando)
- Terminal 3: python3 escritor_cursor.py


# 4. Ejemplo aplicado: sistema de log centralizado con FIFO
Vamos a implementar un escenario útil: un logger que escribe en un FIFO, y múltiples procesos que generan mensajes.

Este patrón es muy usado para:
- Registrar actividad de scripts o servicios.
- Unificar la salida de varias tareas.

## Teoría: ¿por qué usar un FIFO para logs?

**Ventajas:**
- No se necesita archivo compartido.
- El logger puede correr como un proceso independiente.
- Si un proceso se cae, no afecta a los demás (desacople).
- El FIFO se puede redirigir fácilmente hacia un archivo físico, otro proceso o incluso una interfaz gráfica.

## Práctica

### Paso 1: Crear el FIFO del log
```py
import os

fifo_log = "/tmp/fifo_log"

if not os.path.exists(fifo_log):
    os.mkfifo(fifo_log)
    print(f"FIFO de log creado en {fifo_log}")
```

### Paso 2: Logger que lee del FIFO y escribe en archivo
```py
# logger.py
with open("/tmp/fifo_log", "r") as fifo, open("registro.log", "a") as log:
    while True:
        linea = fifo.readline()
        if linea:
            print(f"[LOG] {linea.strip()}")
            log.write(linea)
            log.flush()
```

### Paso 3: Script que escribe logs 

```py
# emisor.py
import time
with open("/tmp/fifo_log", "w") as fifo:
    for i in range(3):
        fifo.write(f"Mensaje #{i} desde el emisor\n")
        fifo.flush()
        time.sleep(1)
```

**Probalo así:**
- Terminal 1: python3 logger.py
- Terminal 2: python3 emisor.py