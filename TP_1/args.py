import argparse

def set_args():
    parser = argparse.ArgumentParser(
        prog='python3 main.py',
        description="Sistema Concurrente de Análisis Biométrico con Cadena de Bloques Local. Se generan n (default=60) datos, se analizan y se verifican como procesos."
    )
    
    parser.add_argument("-n", "--num", type=int, default=60, required=False, help="Indica la cantidad de datos que se generan.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Modo verboso")

    args = parser.parse_args()
    return args