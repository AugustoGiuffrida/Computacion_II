import argparse

def validate_txt(file):
    if not file.endswith(".txt"):
        raise argparse.ArgumentTypeError("El archivo de salida debe tener extensión .txt")
    return file

def validate_csv(file):
    if not file.endswith(".csv"):
        raise argparse.ArgumentTypeError("El archivo de salida debe tener extensión.csv")
    return file    


def main():
    parser = argparse.ArgumentParser(description = "Ejemplo de script con argparse")
    parser.add_argument("-i", "--input", help = "Nombre del archivo de entrada",type =validate_csv, required = True)
    parser.add_argument("-o", "--output", help = "Nombre del archivo de salida", type = validate_txt, default = "salida.txt")
    parser.add_argument("-v", "--verbose", action ="store_true", help = "Modo detallado")

    args = parser.parse_args()


    print(f"Archivo de entrada: {args.input}")
    print(f"Archivo de salida: {args.output}")
    if args.verbose:
        print("Modo detallado activado")

if __name__ == "__main__":
    main()