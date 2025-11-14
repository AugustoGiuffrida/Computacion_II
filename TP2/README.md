# TP2 - Sistema de Scraping y Análisis Web Distribuido

Este proyecto implementa un sistema distribuido de dos servidores. El sistema separa las tareas de I/O (Scraping) y las tareas de CPU (Procesamiento) en dos servicios independientes que se comunican por sockets.

  * **`server_scraping.py` (Servidor A):** Un servidor asíncrono basado en `aiohttp` que actúa como interfaz pública. Gestiona las peticiones HTTP, realiza el scraping y coordina con el Servidor B.
  * **`server_processing.py` (Servidor B):** Un servidor de sockets multihilo que utiliza un pool de procesos (`ProcessPoolExecutor`) para ejecutar tareas computacionalmente intensivas.

## Características Principales

  * **Servidor A (Asyncio):** Maneja múltiples clientes de forma no bloqueante (`asyncio`) y realiza peticiones HTTP asíncronas (`aiohttp`). Soporta direcciones **IPv4 e IPv6**.
  * **Servidor B (Multiprocessing):** Utiliza `socketserver.ThreadingMixIn` para manejar múltiples conexiones del Servidor A en hilos separados. Cada tarea pesada se delega a un `ProcessPoolExecutor` para paralelismo real (CPU-Bound).
  * **Protocolo de Comunicación:** Se utiliza un protocolo binario simple para la comunicación entre A y B: `[Header de 4 Bytes (Big-Endian)] + [Payload JSON]`.
  * **Funcionalidad Completa:**
    1.  **Scraping HTML:** Extracción de título, enlaces, estructura (H1-H6) y conteo de imágenes.
    2.  **Extracción de Metadatos:** Búsqueda de tags `description`, `keywords` y `Open Graph`.
    3.  **Screenshot:** Generación de captura de pantalla (PNG) usando Selenium.
    4.  **Análisis de Rendimiento:** Cálculo de `load_time_ms`, `total_size_kb` y `num_requests` usando la API de Performance del navegador.
    5.  **Thumbnails:** Descarga y procesamiento de imágenes para crear miniaturas.

## Instalación y Dependencias

1.  **Crear Entorno Virtual:**
    Se recomienda crear un entorno virtual para aislar las dependencias del proyecto.

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

2.  **Instalar Dependencias:**
    Instalar las librerías necesarias listadas en `requirements.txt`.

    ```bash
    pip install -r requirements.txt
    ```

3.  **Configurar WebDriver:**
    El Servidor B (`server_processing.py`) requiere **Selenium** y un **WebDriver** (ej. ChromeDriver) para funcionar.

## Instrucciones de Ejecución

El sistema requiere 3 terminales para funcionar: una para cada servidor y una para el cliente.

### 1\. Terminal 1: Servidor B (Procesamiento)

Inicia el servidor de procesamiento primero. Este escuchará las tareas de la CPU.

```bash
# Ejemplo: Escucha en IPv4 (127.0.0.1), puerto 8001, con 4 procesos
python3 server_processing.py -i 127.0.0.1 -p 8001 -n 4
```

### 2\. Terminal 2: Servidor A (Scraping)

Inicia el servidor asíncrono, indicándole cómo conectarse al Servidor B.

```bash
# Ejemplo: Escucha en IPv6 (::1), puerto 8080.
# Se conecta a B en 127.0.0.1:8001
python3 server_scraping.py -i ::1 -p 8080 --processor-ip 127.0.0.1 --processor-port 8001
```

### 3\. Terminal 3: Cliente de Prueba

Una vez que ambos servidores estén corriendo, puedes enviar una solicitud al Servidor A.

```bash
# Pide al Servidor A (en ::1) que analice 'https://example.com'
python3 client.py https://example.com --host ::1 --port 8080
```

El cliente mostrará un resumen y la respuesta JSON completa consolidada.

## Arquitectura y Decisiones de Diseño

### Servidor A (I/O-Bound)

El Servidor A está diseñado para ser altamente concurrente y no bloqueante.

  * **`aiohttp`:** Se utiliza para gestionar el frontend HTTP (`web.Application`) y el backend de scraping (`aiohttp.ClientSession`). Esto asegura que el servidor pueda manejar miles de peticiones de clientes y realizar scraping de sitios web sin bloquear el *event loop*.
  * **Comunicación Asíncrona:** La función `talk_with_processor` utiliza `asyncio.open_connection` para comunicarse con el Servidor B. Esto es crucial: la espera de la respuesta del Servidor B (que puede tardar segundos) no bloquea al Servidor A, permitiéndole seguir aceptando otras peticiones de clientes.

### Servidor B (CPU-Bound)

El Servidor B está diseñado para el paralelismo y la ejecución de tareas pesadas.

  * **`ThreadingMixIn` + `ProcessPoolExecutor`:** Esta es la arquitectura central. `socketserver.ThreadingMixIn` permite que el servidor maneje cada conexión entrante del Servidor A en un **hilo separado**.
  * Dentro del `TaskHandler` (hilo), la llamada `future = pool.submit(...)` envía el trabajo al *pool* de **procesos**.
  * El hilo se bloquea (sincrónicamente) esperando `future.result()`, pero solo bloquea a *ese* cliente, no al servidor principal ni a otros hilos. Esto permite al Servidor B manejar múltiples peticiones de análisis en paralelo, limitadas por el número de procesos (`-n`).

### Optimización del Worker (Selenium)

Una decisión clave de diseño se encuentra en la función `worker_process` del Servidor B. Para evitar el alto costo de iniciar un navegador web, el *worker*:

1.  Inicia **una sola instancia** del driver de Selenium (`webdriver.Chrome`).
2.  Navega a la URL (`driver.get(url)`).
3.  Reutiliza esta instancia para ejecutar ambas tareas pesadas:
      * Generar el *screenshot*.
      * Analizar el *rendimiento* (extrayendo datos de `window.performance`).
4.  Finalmente, cierra el driver (`driver.quit()`).

Esto reduce drásticamente el tiempo de procesamiento en comparación con iniciar un driver para cada tarea.

### Protocolo de Comunicación

Para la comunicación A → B, se implementó un protocolo simple en `common/protocol.py`.

1.  El emisor (Servidor A) serializa el `dict` del trabajo a JSON.
2.  Calcula la longitud de ese JSON (en bytes).
3.  Empaqueta esa longitud como un entero de 4 bytes *sin signo* y en formato *Big-Endian* (`struct.Struct('!I')`).
4.  Envía el `header` (4 bytes) seguido del `payload` (JSON).
5.  El receptor (Servidor B) lee primero exactamente 4 bytes, los decodifica para saber el tamaño del payload, y luego lee exactamente esa cantidad de bytes para obtener el JSON.

Este enfoque es robusto y evita problemas de *buffering* en TCP.