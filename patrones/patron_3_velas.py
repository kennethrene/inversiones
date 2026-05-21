import pandas as pd
import config
import patrones.identificar_patrones as identificar_patrones

# PATRONES COMPUESTOS DE ESTRELLAS (3 VELAS)
def analizar_patrones():
    nombre_patron = "Ninguno"
    tendencia_alcista = False
    tendencia_bajista = False

    if not identificar_patrones.es_tendencia_bajista and identificar_patrones.macd_debil_alcista and identificar_patrones.es_verde1 and identificar_patrones.es_roja3 and (identificar_patrones.cuerpo2 <= (identificar_patrones.cuerpo1 * 0.35)) and identificar_patrones.cuerpo3 > 0:
        mitad_cuerpo_vela1 = identificar_patrones.vela1_valor_abrio + (identificar_patrones.cuerpo1 / 2)
        if identificar_patrones.vela3_valor_cerro <= mitad_cuerpo_vela1:
            tendencia_bajista, nombre_patron = True, "Estrella del Atardecer"
    elif identificar_patrones.es_tendencia_bajista and identificar_patrones.macd_debil_bajista and identificar_patrones.es_roja1 and identificar_patrones.es_verde3 and (identificar_patrones.cuerpo2 <= (identificar_patrones.cuerpo1 * 0.35)) and identificar_patrones.cuerpo3 > 0:
        mitad_cuerpo_vela1 = identificar_patrones.vela2_valor_cerro + (identificar_patrones.cuerpo1 / 2)
        if identificar_patrones.vela3_valor_cerro >= mitad_cuerpo_vela1:
            tendencia_alcista, nombre_patron = True, "Estrella del Amanecer"
    
    return tendencia_alcista, tendencia_bajista, nombre_patron