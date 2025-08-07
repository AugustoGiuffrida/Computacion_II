import unittest
from unittest.mock import MagicMixin, patch, MagicMock
from json import dumps, loads
from src.analizador import leer_datos, analizar, procesar

class TestAnalizador(unittest.TestCase):
    def test_analizar(self):
        pass

    def test_leer_dato(self):
        canal_mock = MagicMock()

        dato_json = '{"timestamp": "2025-08-05T12:00:00", "frecuencia": 120, "presion": [140, 85], "oxigeno": 95}'
        canal_mock.recv.return_value = dato_json

        ventana = []

        leer_datos(canal_entrada=canal_mock, ventana=ventana, ventana_size=1)

        canal_mock.recv.assert_called_once()

        self.assertEqual(len(ventana),1)

        dato_esperado = {
            "timestamp": "2025-08-05T12:00:00", 
            "frecuencia": 120, 
            "presion": [140, 85], 
            "oxigeno": 95
        }

        self.assertEqual(ventana[0], dato_esperado)

if __name__ == '__main__':
    unittest.main()
