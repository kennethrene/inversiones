import pandas as pd
import config.config as config
import patrones.identificar_patrones as identificar_patrones

# PATRONES TRADICIONALES DE 1 VELA
def analizar_patrones():
    nombre_patron = "Ninguno"
    tendencia_alcista = False
    tendencia_bajista = False

    vela3_cuerpo = identificar_patrones.cuerpo3
    rango_total = identificar_patrones.vela3_valor_maximo - identificar_patrones.vela3_valor_minimo
    es_vela3_verde = identificar_patrones.es_verde3
    
    if rango_total == 0:
        return tendencia_alcista, tendencia_bajista, nombre_patron
    
    umbral_marubozu = 0.75
    proporcion_cuerpo = vela3_cuerpo / rango_total

    if proporcion_cuerpo >= umbral_marubozu:
        if es_vela3_verde and float(config.valor_macd) > 0 and float(config.valor_rsi) <= float(config.RSI_SOBRECOMPRA_MACD):
            return True, False, "Marubozu Alcista"
        elif not es_vela3_verde and float(config.valor_macd) < 0 and float(config.valor_rsi) >= float(config.RSI_SOBREVENTA_MACD):
            return False, True, "Marubozu Bajista"
        
        log_marubozu(proporcion_cuerpo, umbral_marubozu, es_vela3_verde)
    else:
        log_marubozu(proporcion_cuerpo, umbral_marubozu, None)

    return tendencia_alcista, tendencia_bajista, nombre_patron

def log_marubozu(proporcion_cuerpo, umbral, es_vela3_verde):
    config.datos_graficos["log"] += "\n\n ℹ️  Evaluando MARUBOZU"

    if proporcion_cuerpo >= umbral:
        if es_vela3_verde != None and es_vela3_verde and float(config.valor_macd) <= 0:
            config.datos_graficos["log"] += f"\n    🚨 Vela 3 verde, pero MACD debe ser mayor que cero: {config.valor_macd}"
        if es_vela3_verde != None and es_vela3_verde and float(config.valor_rsi) > config.RSI_SOBRECOMPRA_MACD:
            config.datos_graficos["log"] += f"\n    🚨 Vela 3 verde, pero RSI no cumple: {float(config.valor_rsi)} > {config.RSI_SOBRECOMPRA_MACD}"
        if es_vela3_verde != None and not es_vela3_verde and float(config.valor_macd) >= 0:
            config.datos_graficos["log"] += f"\n    🚨 Vela 3 roja, pero MACD debe ser menor que cero: {config.valor_macd}"
        if es_vela3_verde != None and not es_vela3_verde and float(config.valor_rsi) < config.RSI_SOBREVENTA_MACD:
            config.datos_graficos["log"] += f"\n    🚨 Vela 3 roja, pero RSI no cumple: {float(config.valor_rsi)} < {config.RSI_SOBREVENTA_MACD}"
    else:
        config.datos_graficos["log"] += f"\n    🚨 Marubozu no cumple - Proporción del cuerpo: {proporcion_cuerpo:.2f} - Requerido: {umbral}"