import getopt
import sys

try:
    opts, args = getopt.getopt(sys.argv[1:], "hf:o:", ["help", "file=", "output="])
except getopt.GetoptError as err:
    print(err)
    sys.exit(1)

for opt, arg in opts:
    if opt in ("-h", "--help"):
        print("Uso: script.py -f <archivo> -o <salida>")
        sys.exit()
    elif opt in ("-f", "--file"):
        print(f"Archivo de entrada: {arg}")
    elif opt in ("-o", "--output"):
        print(f"Archivo de salida: {arg}")

