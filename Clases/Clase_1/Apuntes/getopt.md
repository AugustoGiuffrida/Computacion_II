## **Uso Básico de `getopt` en Python**
Python proporciona la librería `getopt` para manejar argumentos en la línea de comandos. Su funcionamiento es similar a `getopt` en Bash.  

### **Ejemplo 1: Parsear argumentos con `getopt`**
```python
import sys
import getopt

def main(argv):
    input_file = ''
    output_file = ''
    
    try:
        opts, args = getopt.getopt(argv, "hi:o:", ["help", "input=", "output="])
    except getopt.GetoptError:
        print('Uso: script.py -i <inputfile> -o <outputfile>')
        sys.exit(2)
    
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print('Uso: script.py -i <inputfile> -o <outputfile>')
            sys.exit()
        elif opt in ("-i", "--input"):
            input_file = arg
        elif opt in ("-o", "--output"):
            output_file = arg

    print(f"Archivo de entrada: {input_file}")
    print(f"Archivo de salida: {output_file}")

if __name__ == "__main__":
    main(sys.argv[1:])
```
### **Explicación del código:**
1. `getopt.getopt(argv, "hi:o:", ["help", "input=", "output="])`
   - `"hi:o:"`: Define opciones cortas (-h, -i, -o). El `:` indica que `-i` y `-o` requieren un valor.
   - `["help", "input=", "output="]`: Define opciones largas equivalentes (--help, --input, --output).
2. Se recorre la lista `opts` para procesar cada opción y asignar su valor.
3. Si el usuario ejecuta `python script.py -h`, se muestra la ayuda.
4. Se imprimen los valores de los argumentos introducidos.

### **Prueba el script con estos comandos:**
```sh
python script.py -i entrada.txt -o salida.txt
python script.py --input entrada.txt --output salida.txt
python script.py -h
```

