import argparse

def main():
    parser = argparse.ArgumentParser(description = "Ejemplo de script con argparse")
    parser.add_argument("-i", "--input", help = "Nombre del archivo de entrada", required = True)
    parser.add_argument("-o", "--output", help = "Nombre del archivo de salida", default = "salida.txt")
    parser.add_argument("-v", "--verbose", action ="store_true", help = "Modo detallado")

    args = parser.parse_args()


    print(f"Archivo de entrada: {args.input}")
    print(f"Archivo de salida: {args.output}")
    if args.verbose:
        print("Modo detallado activado")

if __name__ == "__main__":
    main()