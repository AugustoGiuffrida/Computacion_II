import unittest
from unittest.mock import  patch, MagicMock
from src.analizador import leer_datos, analizar, procesar

class TestAnalizador(unittest.TestCase):
    def test_analizar(self):
        canal_entrada = MagicMock()
        canal_salida = MagicMock()

    @patch('src.analizador.loads')
    def test_leer_dato(self, mock_jsonloads):
        canal_mock = MagicMock()

        dato_json = {"timestamp": "2025-08-05T12:00:00", "frecuencia": 120, "presion": [140, 85], "oxigeno": 95}
        mock_jsonloads.return_value = dato_json

        ventana = []

        leer_datos(canal_entrada=canal_mock, ventana=ventana, ventana_size=1)

        canal_mock.recv.assert_called_once()
        mock_jsonloads.assert_called_once()

        self.assertEqual(len(ventana),1)

        dato_esperado = {
            "timestamp": "2025-08-05T12:00:00", 
            "frecuencia": 120, 
            "presion": [140, 85], 
            "oxigeno": 95
        }

        self.assertEqual(ventana[0], dato_esperado)

    @patch('src.analizador.sleep')
    def test_procesar_frecuencia_2_datos(self, mock_sleep):
        tipo = 'frecuencia'
        
        # Aquí solo me importa la frecuencia en los datos
        dato1 = {"timestamp": "2025-08-05T12:00:00", "frecuencia": 120, "presion": [140, 85], "oxigeno": 95}
        dato2 = {"timestamp": "2025-08-05T12:00:01", "frecuencia": 100, "presion": [140, 85], "oxigeno": 95}

        ventana = [dato1,dato2]

        resultado = procesar(tipo=tipo, ventana=ventana)
        mock_sleep.assert_called_once()

        esperado = {
            'tipo': tipo,
            'timestamp': '2025-08-05T12:00:01',
            'media': 110.0, # calculado como (120+110)/2
            'desv': 14.142135623730951 # calculado como sqrt(((120-110)**2)/1 + ((100-110)**2)/1)
        }

        self.assertEqual(resultado, esperado)

    @patch('src.analizador.sleep')
    def test_procesar_presion_2_datos(self, mock_sleep):
        tipo = 'presion'
        
        # Aquí solo me importa la frecuencia en los datos
        dato1 = {"timestamp": "2025-08-05T12:00:00", "frecuencia": 120, "presion": [140, 85], "oxigeno": 95}
        dato2 = {"timestamp": "2025-08-05T12:00:01", "frecuencia": 100, "presion": [110, 65], "oxigeno": 95}

        ventana = [dato1,dato2]

        resultado = procesar(tipo=tipo, ventana=ventana)
        mock_sleep.assert_called_once()

        esperado = {
            'tipo': tipo,
            'timestamp': '2025-08-05T12:00:01',
            'media': [125.0,75.0], # calculado como (140+110)/2 y (85+65)/2
            'desv': [21.213203435596427, 14.142135623730951] # calculado como sqrt((140-125)**2/1 + (110-125)**2/1) (para el primero de la lista)
        }

        self.assertEqual(resultado, esperado)

    @patch('src.analizador.sleep')
    def test_procesar_oxigeno_2_datos(self, mock_sleep):
        tipo = 'oxigeno'
        
        # Aquí solo me importa la frecuencia en los datos
        dato1 = {"timestamp": "2025-08-05T12:00:00", "frecuencia": 120, "presion": [140, 85], "oxigeno": 98}
        dato2 = {"timestamp": "2025-08-05T12:00:01", "frecuencia": 100, "presion": [110, 65], "oxigeno": 96}

        ventana = [dato1,dato2]

        resultado = procesar(tipo=tipo, ventana=ventana)
        mock_sleep.assert_called_once()

        esperado = {
            'tipo': tipo,
            'timestamp': '2025-08-05T12:00:01',
            'media': 97.0, # calculado como (98-96)/2
            'desv': 1.4142135623730951 # calculado como sqrt((140-125)**2/1 + (110-125)**2/1) (para el primero de la lista)
        }

        self.assertEqual(resultado, esperado)

    def test_procesar_tipo_invalido(self):
        with self.assertRaises(ValueError):
            procesar(tipo='prueba',ventana=[])

    # Creo estos dos métodos para no tener que repetir el código en todos los tests
    # de analizar()

    def crear_condition_mock(self):
        """Helper para crear un mock de Condition que funciona como context manager"""
        cond_mock = MagicMock()
        # Para que funcione como context manager (with cond:)
        cond_mock.__enter__ = MagicMock(return_value=cond_mock)
        cond_mock.__exit__ = MagicMock(return_value=None)
        return cond_mock

    def crear_value_mock(self, initial_value=0):
        """Helper para crear un mock de multiprocessing.Value"""
        value_mock = MagicMock()
        value_mock.value = initial_value
        return value_mock

    @patch('builtins.print')  # Silenciar prints
    @patch('src.analizador.procesar')  # Mockear procesar
    @patch('src.analizador.leer_datos')  # Mockear leer_datos
    @patch('src.analizador.getpid')
    def test_analizar_ultimo_proceso_notifica_a_todos(self, mock_getpid, mock_leer_datos, mock_procesar, mock_print):
        """Test que simula el último proceso que completa y debe notificar"""
        
        # Setup mocks
        mock_getpid.return_value = 12345
        mock_procesar.return_value = {"resultado": "test"}
        
        # Crear mocks para pipe y queue
        pipe_mock = MagicMock()
        queue_mock = MagicMock()
        
        # Crear mock de Value que simula ser el último proceso (done_count llegará a total_procs)
        done_count_mock = self.crear_value_mock(initial_value=2)  # Empezamos en 2
        total_procs = 3
        
        # Crear mock de Condition
        cond_mock = self.crear_condition_mock()
        
        # Ejecutar con n=1 para simplificar
        analizar(
            pipe_to_read=pipe_mock,
            queue=queue_mock,
            tipo='frecuencia',
            n=1,
            done_count=done_count_mock,
            cond=cond_mock,
            total_procs=total_procs,
            verbose=False
        )
        
        # Verificar que se usó como context manager
        cond_mock.__enter__.assert_called_once()
        cond_mock.__exit__.assert_called_once()
        
        # Verificar que done_count se incrementó
        self.assertEqual(done_count_mock.value, 0)  # Se resetea cuando llega al total
        
        # Verificar que notify_all fue llamado (último proceso)
        cond_mock.notify_all.assert_called_once()
        
        # Verificar que wait() NO fue llamado (es el último)
        cond_mock.wait.assert_not_called()

    @patch('builtins.print')
    @patch('src.analizador.procesar')
    @patch('src.analizador.leer_datos')
    @patch('src.analizador.getpid')
    def test_analizar_proceso_no_ultimo_espera(self, mock_getpid, mock_leer_datos, mock_procesar, mock_print):
        """Test que simula un proceso que NO es el último y debe esperar"""
        
        # Setup mocks
        mock_getpid.return_value = 12345
        mock_procesar.return_value = {"resultado": "test"}
        
        pipe_mock = MagicMock()
        queue_mock = MagicMock()
        
        # Crear mock de Value que simula NO ser el último proceso
        done_count_mock = self.crear_value_mock(initial_value=0)  # Empezamos en 0
        total_procs = 3
        
        cond_mock = self.crear_condition_mock()
        
        # Ejecutar
        analizar(
            pipe_to_read=pipe_mock,
            queue=queue_mock,
            tipo='presion',
            n=1,
            done_count=done_count_mock,
            cond=cond_mock,
            total_procs=total_procs,
            verbose=False
        )
        
        # Verificar que se usó como context manager
        cond_mock.__enter__.assert_called_once()
        cond_mock.__exit__.assert_called_once()
        
        # Verificar que done_count se incrementó pero no llegó al total
        self.assertEqual(done_count_mock.value, 1)
        
        # Verificar que wait() fue llamado (no es el último)
        cond_mock.wait.assert_called_once()
        
        # Verificar que notify_all NO fue llamado (no es el último)
        cond_mock.notify_all.assert_not_called()

    @patch('builtins.print')
    @patch('src.analizador.procesar')
    @patch('src.analizador.leer_datos')
    @patch('src.analizador.getpid')
    def test_analizar_multiples_iteraciones(self, mock_getpid, mock_leer_datos, mock_procesar, mock_print):
        """Test con n=2 para verificar múltiples iteraciones del bucle"""
        
        mock_getpid.return_value = 12345
        mock_procesar.return_value = {"resultado": "test"}
        
        pipe_mock = MagicMock()
        queue_mock = MagicMock()
        done_count_mock = self.crear_value_mock(initial_value=0)
        cond_mock = self.crear_condition_mock()
        
        # Ejecutar con n=2
        analizar(
            pipe_to_read=pipe_mock,
            queue=queue_mock,
            tipo='oxigeno',
            n=2,
            done_count=done_count_mock,
            cond=cond_mock,
            total_procs=3,
            verbose=False
        )
        
        # Verificar que se llamó n veces
        self.assertEqual(mock_leer_datos.call_count, 2)
        self.assertEqual(mock_procesar.call_count, 2)
        self.assertEqual(queue_mock.put.call_count, 2)
        
        # Verificar que el context manager se usó n veces
        self.assertEqual(cond_mock.__enter__.call_count, 2)
        self.assertEqual(cond_mock.__exit__.call_count, 2)

    def test_analizar_tipo_invalido_lanza_excepcion(self):
        """Test que verifica validación del parámetro tipo"""
        
        pipe_mock = MagicMock()
        queue_mock = MagicMock()
        done_count_mock = self.crear_value_mock()
        cond_mock = self.crear_condition_mock()
        
        with self.assertRaises(ValueError):
            analizar(
                pipe_to_read=pipe_mock,
                queue=queue_mock,
                tipo='tipo_invalido',  # Tipo inválido
                n=1,
                done_count=done_count_mock,
                cond=cond_mock,
                total_procs=3,
                verbose=False
            )

    @patch('builtins.print')
    @patch('src.analizador.procesar')
    @patch('src.analizador.leer_datos')
    @patch('src.analizador.getpid')
    def test_analizar_tipos_validos(self, mock_getpid, mock_leer_datos, mock_procesar, mock_print):
        """Test que verifica que los tipos válidos funcionan"""
        
        mock_getpid.return_value = 12345
        mock_procesar.return_value = {"resultado": "test"}
        
        pipe_mock = MagicMock()
        queue_mock = MagicMock()
        done_count_mock = self.crear_value_mock()
        cond_mock = self.crear_condition_mock()
        
        tipos_validos = ['frecuencia', 'presion', 'oxigeno']
        
        for tipo in tipos_validos:
            with self.subTest(tipo=tipo):
                # Resetear mocks para cada subtests
                queue_mock.reset_mock()
                mock_procesar.reset_mock()
                
                # No debería lanzar excepción
                try:
                    analizar(
                        pipe_to_read=pipe_mock,
                        queue=queue_mock,
                        tipo=tipo,
                        n=1,
                        done_count=done_count_mock,
                        cond=cond_mock,
                        total_procs=3,
                        verbose=False
                    )
                except ValueError:
                    self.fail(f"Tipo '{tipo}' debería ser válido")

if __name__ == '__main__':
    unittest.main()
