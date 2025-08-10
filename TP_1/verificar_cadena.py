from json import loads, dumps, dump
from hashlib import sha256
from numpy import mean

def signal_data_mean(data_type:str,signals:list,pres_signal:int=-1):
    if pres_signal == -1:
        return round(float(mean([signal.get(data_type) for signal in signals])),2)
    else:
        return round(float(mean([signal.get(data_type)[pres_signal] for signal in signals])),2)

def leer_datos():
    with open('blockchain.json','r') as blockchain:
        data = loads(blockchain.read())

    cant = len(data)

    hash_calc = '0'*64
    alert_num = 0
    invalid_hashes = 0
    frec_signals = []
    pres_signals = []
    oxig_signals = []
    for block in data:
        cuerpo = block.get('datos')
        timestamp = block.get('timestamp')
        prev_hash = block.get('prev_hash')
        # Es imposible que el hash previo sea distinto al calculado anteriormente. 
        # Si esto sucede, el resto serán invalidos y no hay necesidad que calcularlos.
        # Además, si hubiese un hash incorrecto, no tiene sentido leer el resto de 
        # datos, estos serán también invalidos. Entonces estos datos se 
        # leen solo si el hash es válido
        if prev_hash == hash_calc:
            hash_input = prev_hash + dumps(cuerpo, sort_keys=True) + timestamp
            hash_calc = sha256(hash_input.encode()).hexdigest()
            
            if hash_calc == block.get('hash'):
                alert = block.get('alerta')
                if alert:
                    alert_num+=1 

                frec_signals.append(cuerpo.get('frecuencia'))
                pres_signals.append(cuerpo.get('presion'))
                oxig_signals.append(cuerpo.get('oxigeno'))
            else:
                invalid_hashes += 1
                hash_calc = 'invalid'
        else:
            invalid_hashes += 1
            hash_calc = 'invalid'

    general_means = {'medias':{
        'frecuencia': signal_data_mean('media',frec_signals),
        'presión sistólica': signal_data_mean('media',pres_signals,0),
        'presión diastólica': signal_data_mean('media',pres_signals,1),
        'saturación de oxigeno': signal_data_mean('media',oxig_signals)
    },
    'desviaciones':{
        'frecuencia': signal_data_mean('desv',frec_signals),
        'presión sistólica': signal_data_mean('desv',pres_signals,0),
        'presión diastólica': signal_data_mean('desv',pres_signals,1),
        'saturación de oxigeno': signal_data_mean('desv',oxig_signals)
    }}
    return cant, alert_num, general_means, invalid_hashes

def generar_reporte():
    cant, alert_num, general_means, invalid_hashes = leer_datos()
    with open('reporte.txt','w',encoding='utf-8') as reporte:
        if invalid_hashes == 0:
            reporte.write('Todos los bloques han sido correctamente encadenados.\n')
        else:
            reporte.write(f'Hay datos corruptos. Total de datos corruptos: {invalid_hashes} (los datos invalidos son ignorados)\n')
        reporte.write(f'Cantidad de bloques leídos: {cant}\n')
        reporte.write(f'Cantidad de alertas: {alert_num}\n')
        dump(general_means,reporte,indent=2,ensure_ascii=False)

if __name__ == '__main__':
    generar_reporte()
