from numpy import mean, std 

# Se calculan las medias y desviacion según el self.__tipo__ entonces:
# Frecuen: media = mean(datos) se devuelve la media datos, donde datos es la lista de frecuencias cardiacas de ventana
# Presión: media = (mean(datos sistólicos), mean(datos diastólicos)) se devuelve una tupla con las medias (sistólica, diastólica)
#          donde: 
#               - `datos sistólicos` son, para cada dato de la lista de datos, el primer elemento (dato[0] for dato in datos)
#               - `datos diastólicos` son, para cada dato de la lista de datos, el segundo elemento (dato[1] for dato in datos)
# Oxigeno: media = mean(datos) al igual que frecuencia
# Para la desviación estándar es lo mismo

def media(tipo:str='', datos:list=[]):
    '''
    Calcula la media según el tipo de dato.

    Parameters
    ----------
    tipo : str
        Tipo de dato. Puede ser 'frecuencia', 'presion' o 'oxigeno'.
    datos : list
        Lista de datos numéricos.

    Returns
    -------
    float or list of float
        La media de los datos. Si tipo es 'presion', devuelve una lista con las medias
        de los datos sistólicos y diastólicos.
    '''
    return float(mean(datos)) if tipo != 'presion' else [float(mean([dato[0] for dato in datos])), float(mean([dato[1] for dato in datos]))]

def desviacion(tipo:str='', datos:list=[]):
    '''
    Calcula la desviación estándar según el tipo de dato.

    Parameters
    ----------
    tipo : str
        Tipo de dato. Puede ser 'frecuencia', 'presion' o 'oxigeno'.
    datos : list
        Lista de datos numéricos.

    Returns
    -------
    float or list of float
        La desviación estándar de los datos. Si tipo es 'presion', devuelve una lista con las
        desviaciones estándar de los datos sistólicos y diastólicos.
    '''
    if tipo != 'presion':
        if len(datos) <= 1:
            return 0.0
        else:
            return float(std(datos, ddof=1))
    else:
        if len(datos) <= 1:
            return [0.0, 0.0]
        else:
            return [float(std([d[0] for d in datos], ddof=1)),
                    float(std([d[1] for d in datos], ddof=1))]
