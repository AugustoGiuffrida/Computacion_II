import unittest, json
from unittest.mock import patch, MagicMock, call
from src.generador import generar_dato, generar

class TestGenerador(unittest.TestCase):
    @patch('random.randint')
    @patch('src.generador.datetime')
    def test_generar_dato_correcto(self, mock_datetime, mock_randint):
        mock_datetime.now.return_value.isoformat.return_value = '2025-08-05T00:00:00'
        mock_randint.side_effect = [90,125,70,98] # [frecuencia, sistólica, diastólica, oxigeno]
        
        resultado = generar_dato()

        esperado = json.dumps({
            "timestamp": '2025-08-05T00:00:00',
            "frecuencia": 90,
            "presion": [125,70], # [sistolica, diastolica]
            "oxigeno": 98
        })
        self.assertEqual(resultado, esperado)

    @patch('builtins.print')
    @patch('src.generador.time.sleep')
    @patch('src.generador.generar_dato')
    @patch('src.generador.getpid')
    def test_gerenar_con_3_pipes(self, mock_getpid, mock_generar_dato, mock_sleep, mock_print):
       mock_getpid.return_value = 5
       mock_generar_dato.return_value = 'dato_en_formato_json'

       pipe1 = MagicMock()
       pipe2 = MagicMock()
       pipe3 = MagicMock()
       pipes = [pipe1,pipe2,pipe3]

       generar(n=2,pipes=pipes,verbose=False)

       self.assertEqual(mock_generar_dato.call_count, 2)
       self.assertEqual(mock_sleep.call_count, 2)

       pipe1.send.assert_has_calls([call('dato_en_formato_json'), call('dato_en_formato_json')])
       pipe2.send.assert_has_calls([call('dato_en_formato_json'), call('dato_en_formato_json')])
       pipe3.send.assert_has_calls([call('dato_en_formato_json'), call('dato_en_formato_json')])


    @patch('builtins.print')
    @patch('src.generador.time.sleep')
    @patch('src.generador.generar_dato')
    @patch('src.generador.getpid')
    def test_gerenar_con_1_pipe(self, mock_getpid, mock_generar_dato, mock_sleep, mock_print):
       mock_getpid.return_value = 5
       mock_generar_dato.return_value = 'dato_en_formato_json'

       pipe = MagicMock()
       pipes = [pipe]

       generar(n=2,pipes=pipes,verbose=False)

       self.assertEqual(mock_generar_dato.call_count, 2)
       self.assertEqual(mock_sleep.call_count, 2)
       pipe.send.assert_has_calls([call('dato_en_formato_json'), call('dato_en_formato_json')])

    @patch('builtins.print')
    @patch('src.generador.time.sleep')
    @patch('src.generador.generar_dato')
    @patch('src.generador.getpid')
    def test_gerenar_con_6_pipes_y_10_datos(self, mock_getpid, mock_generar_dato, mock_sleep, mock_print):
       mock_getpid.return_value = 5
       mock_generar_dato.return_value = 'dato_en_formato_json'

       pipe1 = MagicMock()
       pipe2 = MagicMock()
       pipe3 = MagicMock()
       pipe4 = MagicMock()
       pipe5 = MagicMock()
       pipe6 = MagicMock()
       pipes = [pipe1,pipe2,pipe3,pipe4,pipe5,pipe6]

       generar(n=10,pipes=pipes,verbose=False)

       self.assertEqual(mock_generar_dato.call_count, 10)
       self.assertEqual(mock_sleep.call_count, 10)

       pipe1.send.assert_has_calls([call('dato_en_formato_json'), call('dato_en_formato_json')])
       pipe2.send.assert_has_calls([call('dato_en_formato_json'), call('dato_en_formato_json')])
       pipe3.send.assert_has_calls([call('dato_en_formato_json'), call('dato_en_formato_json')])
       pipe4.send.assert_has_calls([call('dato_en_formato_json'), call('dato_en_formato_json')])
       pipe5.send.assert_has_calls([call('dato_en_formato_json'), call('dato_en_formato_json')])
       pipe6.send.assert_has_calls([call('dato_en_formato_json'), call('dato_en_formato_json')])

    def test_llamar_generar_con_datos_invalidos(self):
        with self.assertRaises(ValueError):
            generar(n=-1,pipes=[])

    @patch('builtins.print')
    @patch('src.generador.time.sleep')
    @patch('src.generador.generar_dato')
    def test_llamar_generar_con_n0(self, mock_generar_dato, mock_sleep, mock_print):
        pipe = MagicMock()
        pipes = [pipe]
        generar(n=0,pipes=pipes)

        self.assertEqual(mock_generar_dato.call_count, 0)
        self.assertEqual(mock_sleep.call_count, 0)
        self.assertEqual(pipe.send.call_count, 0)

if __name__ == '__main__':
    unittest.main()
