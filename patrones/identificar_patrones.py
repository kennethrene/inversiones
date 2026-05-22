import pandas as pd
import config
from . import patron_2_velas
from . import patron_3_velas
from . import patrones_complejos

def identificar_patrones(total_velas, valor_adx):
    global datos_compartidos,cuerpo3,vela3_valor_abrio,vela3_valor_maximo,vela3_valor_minimo,vela3_valor_cerro,es_roja3,es_verde3,cuerpo2,num_velas_disponibles
    global vela2_valor_abrio,vela2_valor_cerro,cuerpo1,vela1_valor_abrio,vela2_valor_cerro,es_verde1,es_roja1,tendencia_alcista,tendencia_bajista
    global nombre_patron,vela_actual,vela_previa,vela_antepenultima,idx_actual,es_tendencia_bajista,macd_debil_bajista,macd_debil_alcista,picos_indices,suelos_indices
    
    config.datos_compartidos["indice_senal"] = None
    config.datos_compartidos["tipo_senal"] = None
    
    num_velas_disponibles = total_velas
    if len(num_velas_disponibles) < 3:
        config.datos_compartidos["senal_accion"] = "🔎 ESPERANDO HISTORIAL DE VELAS"
        return "Construyendo historial de barras"
    
    if valor_adx is None:
        config.datos_compartidos["senal_accion"] = "🔎 ESPERANDO LECTURA DE ADX"
        return "Faltan osciladores de apoyo en el DOM"

    # PARAMETROS GENERALES PARA IDENTIFICAR TODOS LOS PATRONES
    vela_actual = num_velas_disponibles.iloc[-1] # Vela 3
    vela_previa = num_velas_disponibles.iloc[-2] # Vela 2
    vela_antepenultima = num_velas_disponibles.iloc[-3] # Vela 1
    idx_actual = num_velas_disponibles.index[-1]
    
    vela3_valor_abrio, vela3_valor_maximo, vela3_valor_minimo, vela3_valor_cerro = float(vela_actual['Open']), float(vela_actual['High']), float(vela_actual['Low']), float(vela_actual['Close'])
    cuerpo3 = abs(vela3_valor_cerro - vela3_valor_abrio)
    es_roja3 = vela3_valor_cerro < vela3_valor_abrio
    es_verde3 = vela3_valor_cerro > vela3_valor_abrio
    
    vela2_valor_abrio, vela2_valor_cerro = float(vela_previa['Open']), float(vela_previa['Close'])
    cuerpo2 = abs(vela2_valor_cerro - vela2_valor_abrio)
    
    vela1_valor_abrio, vela2_valor_cerro = float(vela_antepenultima['Open']), float(vela_antepenultima['Close'])
    cuerpo1 = abs(vela2_valor_cerro - vela1_valor_abrio)
    es_verde1 = vela2_valor_cerro > vela1_valor_abrio
    es_roja1 = vela2_valor_cerro < vela1_valor_abrio
    
    tendencia_alcista = False
    tendencia_bajista = False
    nombre_patron = "Ninguno"

    # INDICADORES GENERALES DE VALIDACION
    es_tendencia_bajista = len(config.historico_macd) > 1 and config.historico_macd[-1] < 0
    macd_debil_alcista = len(config.historico_macd) > 1 and config.historico_macd[-1] < config.historico_macd[-2]
    macd_debil_bajista = len(config.historico_macd) > 1 and config.historico_macd[-1] > config.historico_macd[-2]

    picos_indices = []
    suelos_indices = []

    tendencia_alcista, tendencia_bajista, nombre_patron = patrones_complejos.analizar_patrones()

    if nombre_patron == "Ninguno":
        tendencia_alcista, tendencia_bajista, nombre_patron = patron_3_velas.analizar_patrones()

        if nombre_patron == "Ninguno":
            tendencia_alcista, tendencia_bajista, nombre_patron = patron_2_velas.analizar_patrones()
    
    # VALIDACIÓN FINAL
    if valor_adx >= config.ADX_TENDENCIA_FUERTE and len(num_velas_disponibles) >= 12:
        if tendencia_alcista:
            config.datos_compartidos["indice_senal"] = idx_actual
            config.datos_compartidos["tipo_senal"] = "COMPRA"
            config.datos_compartidos["senal_accion"] = f"🟢 COMPRA DETECTADA: {nombre_patron}"
            return f"COMPRA_{nombre_patron}"
        elif tendencia_bajista:
            config.datos_compartidos["indice_senal"] = idx_actual
            config.datos_compartidos["tipo_senal"] = "VENTA"
            config.datos_compartidos["senal_accion"] = f"🔴 VENTA DETECTADA: {nombre_patron}"
            return f"VENTA_{nombre_patron}"
    
    if nombre_patron != "Ninguno":
        if valor_adx >= config.ADX_TENDENCIA_FUERTE:
            config.datos_compartidos["senal_accion"] = f"🔴 SE PATRON {nombre_patron} IDENTIFICADO, PERO TENDENCIA NO COMPATIBLE"
        else:
            config.datos_compartidos["senal_accion"] = f"🔴 SE PATRON {nombre_patron} IDENTIFICADO, PERO ADX DEBIL"
    else:
        config.datos_compartidos["senal_accion"] = "🔎 MERCADO EN RANGO / NEUTRAL (Buscando patrones)"

    config.ultimo_patron = nombre_patron

    return "Analizando la acción del precio"
