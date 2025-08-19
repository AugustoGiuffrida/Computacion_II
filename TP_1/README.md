
# Sistema Concurrente de Análisis Biométrico con Blockchain

Este proyecto se implemento un sistema de monitoreo biométrico en tiempo real usando múltiples procesos de Python que se comunican entre sí. Tenemos un **proceso generador** que cada segundo crea datos simulados (un diccionario JSON con campos `timestamp`, `frecuencia`, `presion` y `oxigeno`), tres **procesos analizadores** que calculan en paralelo la media y desviación estándar de las lecturas de cada señal, y un **proceso verificador** que agrupa los resultados, comprueba si hay valores fuera de rango y construye bloques que se enlazan formando una cadena de bloques local. Al final se obtiene un archivo `blockchain.json` con todos los bloques encadenados, garantizando la integridad de los datos.

## Componentes principales

* **Proceso Generador**: simula `n` muestras (por defecto 60), una por segundo. Cada muestra es un JSON con un timestamp actual y valores aleatorios para `frecuencia`, `presion` y `oxigeno`. En el código, la función `generar_dato()` arma este JSON usando `datetime.now()` y `random.randint()`. Luego, el proceso generador envía cada dato completo a los procesos analizadores mediante **pipes** (un pipe por cada analizador). Esto se hace dentro de un bucle que duerme 1 segundo entre envíos.

* **Procesos Analizadores** (3 procesos): cada analizador está dedicado a un tipo de señal (`'frecuencia'`, `'presion'` o `'oxigeno'`). Cada uno lee de su pipe los datos completos enviados por el generador. Mantiene internamente una *ventana móvil* con las últimas 30 muestras recibidas. En cada paso extrae de esa ventana los valores de su señal (por ejemplo, todas las frecuencias o las tuplas de presión arterial) y calcula la media y desviación estándar usando funciones auxiliares. El resultado es un diccionario con el timestamp, el tipo de señal y los valores calculados:

  ```python
  {
    "tipo": "frecuencia",  # o "presion" / "oxigeno"
    "timestamp": "YYYY-MM-DDTHH:MM:SS",
    "media": ...,
    "desv": ...
  }
  ```

  Este resultado se envía al proceso verificador mediante una **cola compartida** (`multiprocessing.Queue`). Para garantizar que los tres analizadores avanzan sincronizados, el código utiliza un `Value` y un `Condition` compartidos: cada analizador incrementa un contador al terminar y luego espera a que los demás terminen antes de continuar.

* **Proceso Verificador y Cadena de Bloques**: este proceso recopila continuamente los resultados desde la cola. Cada vez lee los tres resultados (uno por cada analizador) correspondientes a un mismo `timestamp`. Luego verifica condiciones de seguridad: marca una alerta si la frecuencia supera 200, la presión sistólica supera 200 o el oxígeno está fuera de 90-100. A partir de estos datos construye un bloque con la estructura:

  ```python
  {
    "timestamp": "...",
    "datos": {
      "frecuencia": {"media": ..., "desv": ...},
      "presion":   {"media": ..., "desv": ...},
      "oxigeno":   {"media": ..., "desv": ...}
    },
    "alerta": true/false,
    "prev_hash": "...",
    "hash": "..."
  }
  ```

  La función `crear_bloque` (en `blockchain.py`) combina los datos procesados con el `prev_hash` del bloque anterior y calcula el nuevo hash SHA-256 sobre la concatenación de `prev_hash + JSON(datos) + timestamp`. Cada nuevo bloque se agrega al final de la cadena y luego se guarda en el archivo `blockchain.json`. El verificador también imprime en pantalla el número del bloque, su hash y si tiene alerta o no.

* **Cadena de Bloques (Blockchain)**: es básicamente una lista de bloques almacenada en `blockchain.json`. Cada bloque almacena el hash del bloque anterior, lo que vincula todos los registros. De este modo, la integridad de los datos biométricos procesados queda garantizada.

Se usan pipes sobre named pipes (o fifos) porque python presenta una abastraccion de alto nivel de pipes y no tiene sentido crear un fd para crear un named pipe para comunicar dos procesos. Esta tarea la hacen mas eficientemente los pipes anonimos.

Se eligieron queues porque python tiene abstraciones de alto nivel y ademas este ipc ideal cuando se tiene varios productores y un consumidor como en este caso.

Es importante utilizar values o conditions para sincronizar los procesos analizadores y que escriban todos en la queue en orden.

## Ejecución

Para ejecutar el programa:

```sh
python3 main.py
```

Y esto tomará los valores por defecto (60 bloques). Para modificar la cantidad de bloques puede usar el parametro `-h` para ver las opciones disponibles.

```sh
python3 main.py -h
```

El programa acepta los siguientes argumentos de línea de comandos (configurados con `argparse`):

* `-n N` o `--num N`: cantidad de datos a generar (por defecto 60).
* `-v` o `--verbose`: activa el modo detallado, mostrando más información de los procesos.

Por ejemplo:

```sh
python3 main.py -n 100 -v
```

Para generar el reporte:

```sh
python3 verificar_cadena.py
```
