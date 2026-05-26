import pandas as pd
import config
from . import patron_1_vela
from . import patron_2_velas
from . import patron_3_velas
from . import patrones_complejos

def identificar_patrones(total_velas, valor_adx):
    global datos_compartidos,cuerpo3,vela3_valor_abrio,vela3_valor_maximo,vela3_valor_minimo,vela3_valor_cerro,es_roja3,es_verde3,cuerpo2,num_velas_disponibles
    global vela2_valor_abrio,vela2_valor_cerro,cuerpo1,vela1_valor_abrio,vela2_valor_cerro,es_verde1,es_roja1,tendencia_alcista,tendencia_bajista
    global nombre_patron,vela_actual,vela_previa,vela_antepenultima,hora_vela_actual,es_tendencia_bajista,macd_debil_bajista,macd_debil_alcista,picos_indices,suelos_indices
    
    config.datos_graficos["hora_vela"] = None
    config.datos_graficos["operacion"] = None
    
    num_velas_disponibles = total_velas
    if len(num_velas_disponibles) < 12:
        config.datos_graficos["patron"] = None
        return "Sin historial de barras"
    
    if valor_adx is None:
        config.datos_graficos["patron"] = None
        return "Faltan osciladores de apoyo en el DOM"

    # PARAMETROS GENERALES PARA IDENTIFICAR TODOS LOS PATRONES
    vela_actual = num_velas_disponibles.iloc[-1] # Vela 3
    vela_previa = num_velas_disponibles.iloc[-2] # Vela 2
    vela_antepenultima = num_velas_disponibles.iloc[-3] # Vela 1
    hora_vela_actual = num_velas_disponibles.index[-1]
    
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

    if config.ENABLE_COMPLEX_CANDLES:
        tendencia_alcista, tendencia_bajista, nombre_patron = patrones_complejos.analizar_patrones()

    if nombre_patron == "Ninguno":
        tendencia_alcista, tendencia_bajista, nombre_patron = patron_3_velas.analizar_patrones()

        if nombre_patron == "Ninguno":
            tendencia_alcista, tendencia_bajista, nombre_patron = patron_2_velas.analizar_patrones()

            if nombre_patron == "Ninguno":
                tendencia_alcista, tendencia_bajista, nombre_patron = patron_1_vela.analizar_patrones()
    
    # VALIDACIÓN FINAL
    if valor_adx >= config.ADX_TENDENCIA_FUERTE and len(num_velas_disponibles) >= 12:
        if tendencia_alcista:
            config.datos_graficos["hora_vela"] = hora_vela_actual
            config.datos_graficos["operacion"] = "COMPRA"
            config.datos_graficos["patron"] = nombre_patron
            config.datos_graficos["log"] = f"\n ℹ️   Comprando - Patrón identificado: {nombre_patron}"
            config.log_operacion = config.datos_graficos["log"]
            config.datos_graficos["log"] = ""
            return f"COMPRA_{nombre_patron}"
        elif tendencia_bajista:
            config.datos_graficos["hora_vela"] = hora_vela_actual
            config.datos_graficos["operacion"] = "VENTA"
            config.datos_graficos["patron"] = nombre_patron
            config.datos_graficos["log"] = f"\n ℹ️   Vendiendo - Patrón identificado: {nombre_patron}"
            config.log_operacion = config.datos_graficos["log"]
            config.datos_graficos["log"] = ""
            return f"VENTA_{nombre_patron}"
    
    if nombre_patron != "Ninguno":
        if config.valor_adx >= config.ADX_TENDENCIA_FUERTE:
            config.datos_graficos["log"] = f"\n ❌  {nombre_patron} identifido pero ADX débil {config.valor_adx} - Requerido: {config.ADX_TENDENCIA_FUERTE}"
    else:
        config.datos_graficos["patron"] = "Ninguno"

    config.ultimo_patron = nombre_patron

    return "Analizando la acción del precio"
