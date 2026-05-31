import pandas as pd
import configuracion.parametros as parametros
from . import patron_1_vela
from . import patron_2_velas
from . import patron_3_velas
from . import patrones_complejos

def identificar_patrones(total_velas, valor_adx):
    global datos_compartidos,cuerpo3,vela3_valor_abrio,vela3_valor_maximo,vela3_valor_minimo,vela3_valor_cerro,es_roja3,es_verde3,cuerpo2,num_velas_disponibles
    global vela2_valor_abrio,vela2_valor_cerro,cuerpo1,vela1_valor_abrio,vela2_valor_cerro,es_verde1,es_roja1,tendencia_alcista,tendencia_bajista
    global nombre_patron,vela_actual,vela_previa,vela_antepenultima,hora_vela_actual,es_tendencia_bajista,macd_debil_bajista,macd_debil_alcista,picos_indices,suelos_indices
    
    parametros.datos_graficos["hora_vela"] = None
    parametros.datos_graficos["operacion"] = None
    
    num_velas_disponibles = total_velas
    if len(num_velas_disponibles) < 12:
        parametros.datos_graficos["patron"] = None
        return "Sin historial de barras"
    
    if valor_adx is None:
        parametros.datos_graficos["patron"] = None
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
    es_tendencia_bajista = len(parametros.historico_macd) > 1 and parametros.historico_macd[-1] < 0
    macd_debil_alcista = len(parametros.historico_macd) > 1 and parametros.historico_macd[-1] < parametros.historico_macd[-2]
    macd_debil_bajista = len(parametros.historico_macd) > 1 and parametros.historico_macd[-1] > parametros.historico_macd[-2]

    picos_indices = []
    suelos_indices = []

    if parametros.ENABLE_COMPLEX_CANDLES:
        tendencia_alcista, tendencia_bajista, nombre_patron = patrones_complejos.analizar_patrones()

    if nombre_patron == "Ninguno":
        tendencia_alcista, tendencia_bajista, nombre_patron = patron_3_velas.analizar_patrones()

        if nombre_patron == "Ninguno":
            tendencia_alcista, tendencia_bajista, nombre_patron = patron_2_velas.analizar_patrones()

            if nombre_patron == "Ninguno":
                tendencia_alcista, tendencia_bajista, nombre_patron = patron_1_vela.analizar_patrones()
    
    # VALIDACIÓN FINAL
    if valor_adx >= parametros.ADX_TENDENCIA_FUERTE and len(num_velas_disponibles) >= 12:
        if tendencia_alcista:
            parametros.datos_graficos["hora_vela"] = hora_vela_actual
            parametros.datos_graficos["operacion"] = "COMPRA"
            parametros.datos_graficos["patron"] = nombre_patron
            parametros.datos_graficos["log"] = f"\n ℹ️   Comprando - Patrón identificado: {nombre_patron}"
            parametros.log_operacion = parametros.datos_graficos["log"]
            parametros.datos_graficos["log"] = ""
            return f"COMPRA_{nombre_patron}"
        elif tendencia_bajista:
            parametros.datos_graficos["hora_vela"] = hora_vela_actual
            parametros.datos_graficos["operacion"] = "VENTA"
            parametros.datos_graficos["patron"] = nombre_patron
            parametros.datos_graficos["log"] = f"\n ℹ️   Vendiendo - Patrón identificado: {nombre_patron}"
            parametros.log_operacion = parametros.datos_graficos["log"]
            parametros.datos_graficos["log"] = ""
            return f"VENTA_{nombre_patron}"
    
    if nombre_patron != "Ninguno":
        if parametros.valor_adx >= parametros.ADX_TENDENCIA_FUERTE:
            parametros.datos_graficos["log"] = f"\n ❌  {nombre_patron} identifido pero ADX débil {parametros.valor_adx} - Requerido: {parametros.ADX_TENDENCIA_FUERTE}"
    else:
        parametros.datos_graficos["patron"] = "Ninguno"

    parametros.ultimo_patron = nombre_patron

    return "Analizando la acción del precio"
