## ****Uso Básico de `argparse` en Python****

### **Introducción a `argparse`**
`argparse` es el módulo recomendado para el manejo de argumentos en Python, ofreciendo una interfaz más flexible y robusta.

### **Uso Básico de `argparse`**
Ejemplo mínimo:

```python
import argparse

parser = argparse.ArgumentParser(description="Ejemplo de argparse")
parser.add_argument("-i", "--input", required=True, help="Archivo de entrada")
parser.add_argument("-o", "--output", required=True, help="Archivo de salida")
args = parser.parse_args()

print(f"Archivo de entrada: {args.input}")
print(f"Archivo de salida: {args.output}")
```

Ejecutando el script:

```sh
python script.py -i entrada.txt -o salida.txt
```

Salida esperada:

```sh
Archivo de entrada: entrada.txt
Archivo de salida: salida.txt
```

### **Validación y Tipos de Datos**
Se pueden especificar tipos de datos en los argumentos:

```python
parser.add_argument("-n", "--numero", type=int, help="Número entero obligatorio")
```
Esto permite validar que se ingrese un número entero en lugar de una cadena.

### **Argumentos Posicionales vs. Opcionales**
- **Argumentos posicionales**: No requieren prefijo (`-` o `--`).

  ```python
  parser.add_argument("archivo", help="Archivo de entrada")
  ```
- **Argumentos opcionales**: Se especifican con `-` o `--`.

  ```python
  parser.add_argument("--modo", choices=["rapido", "lento"], help="Modo de ejecución")
  ```

### **Generación Automática de Ayuda**
`argparse` genera automáticamente mensajes de ayuda con `--help`:

```sh
python script.py --help
```

Salida esperada:

```sh
usage: script.py [-h] -i INPUT -o OUTPUT

Ejemplo de argparse

optional arguments:

  -h, --help            muestra este mensaje y sale
  -i INPUT, --input INPUT
                        Archivo de entrada
  -o OUTPUT, --output OUTPUT
                        Archivo de salida
```