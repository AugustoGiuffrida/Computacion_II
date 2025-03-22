import argparse

parser = argparse.ArgumentParser(description="Ejemplo de uso de argparse")
parser.add_argument("-f", "--file", help="Nombre del archivo de entrada", required=True)
parser.add_argument("-o", "--output", help="Archivo de salida", default="salida.txt")
parser.add_argument("-v", "--verbose", action="store_true", help="Modo detallado")

args = parser.parse_args()

print(f"Archivo de entrada: {args.file}")
print(f"Archivo de salida: {args.output}")
if args.verbose:
    print("Modo detallado activado")

