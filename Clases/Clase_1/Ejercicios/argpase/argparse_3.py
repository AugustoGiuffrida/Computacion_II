import argparse

def validate_txt(file):
    if not file.endswith(".txt"):
        raise argparse.ArgumentTypeError("El archivo de salida debe tener extensión .txt")
    return file

def validate_input_file(file):
    if not (file.endswith(".csv") or file.endswith(".json")):
        raise argparse.ArgumentTypeError("El archivo de entrada debe tener extensión .csv o .json")
    return file    

def main():
    parser = argparse.ArgumentParser(description="Ejemplo de script con argparse")
    parser.add_argument("-i", "--input", nargs="+", help="Archivos de entrada", type=validate_input_file, required=True)
    parser.add_argument("-o", "--output", help="Nombre del archivo de salida", type=validate_txt)
    parser.add_argument("-v", "--verbose", action="store_true", help="Modo detallado")

    args = parser.parse_args()

    if args.output is None:
        while True:
            args.output = input("No ingresaste un archivo de salida. Por favor, ingresa uno con extensión .txt: ")
            if args.output.endswith(".txt"):
                break
            else:
                print("⚠️ Error: El archivo debe tener la extensión .txt")

    print(f"Archivos de entrada: {args.input}")
    print(f"Archivo de salida: {args.output}")
    if args.verbose:
        print("Modo detallado activado")

if __name__ == "__main__":
    main()
