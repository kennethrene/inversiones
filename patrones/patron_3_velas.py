import pandas as pd
import config.config as config
import patrones.identificar_patrones as identificar_patrones

# PATRONES COMPUESTOS DE ESTRELLAS (3 VELAS)
def analizar_patrones():
    nombre_patron = "Ninguno"
    tendencia_alcista = False
    tendencia_bajista = False

    if not identificar_patrones.es_tendencia_bajista and identificar_patrones.macd_debil_alcista and identificar_patrones.es_verde1 \
        and identificar_patrones.es_roja3 and identificar_patrones.cuerpo2 <= identificar_patrones.cuerpo1 * 0.35 \
            and identificar_patrones.cuerpo3 > 0:
        mitad_cuerpo_vela1 = identificar_patrones.vela1_valor_abrio + (identificar_patrones.cuerpo1 / 2)
        
        if identificar_patrones.vela3_valor_cerro <= mitad_cuerpo_vela1:
            return False, True, "Estrella del Atardecer"
        
        log_estrella_del_atardecer(mitad_cuerpo_vela1)
    
    if identificar_patrones.es_tendencia_bajista and identificar_patrones.macd_debil_bajista and identificar_patrones.es_roja1 \
        and identificar_patrones.es_verde3 and identificar_patrones.cuerpo2 <= identificar_patrones.cuerpo1 * 0.35 \
            and identificar_patrones.cuerpo3 > 0:
        mitad_cuerpo_vela1 = identificar_patrones.vela2_valor_cerro + identificar_patrones.cuerpo1 / 2
        
        if identificar_patrones.vela3_valor_cerro >= mitad_cuerpo_vela1:
            return True, False, "Estrella del Amanecer"
    
        log_estrella_del_amanecer()
    
    return tendencia_alcista, tendencia_bajista, nombre_patron

def log_estrella_del_amanecer(mitad_cuerpo_vela1):
    if len(config.historico_macd) > 1:
        config.datos_graficos["log"] += "\n\n ℹ️  Evaluando ESTRELLA DEL AMANECER"

        if identificar_patrones.es_tendencia_bajista:
            if not identificar_patrones.macd_debil_bajista:
                config.datos_graficos["log"] += "\n    🚨 MACD débil bajista no detectado"
            if not identificar_patrones.es_roja1:
                config.datos_graficos["log"] += "\n    🚨 Vela 1 no es roja"
            if not identificar_patrones.es_verde3:
                config.datos_graficos["log"] += "\n    🚨 Vela 3 no es verde"
            if identificar_patrones.cuerpo2 > identificar_patrones.cuerpo1 * 0.35:
                config.datos_graficos["log"] += f"\n    🚨 Cuerpo de la vela 2 es mayor que el 35% del cuerpo de la vela 1 - {identificar_patrones.cuerpo2} > {identificar_patrones.cuerpo1 * 0.35}"
            if identificar_patrones.cuerpo3 <= 0:
                config.datos_graficos["log"] += f"\n    🚨 Cuerpo de la vela 3 menor o igual a cero - {identificar_patrones.cuerpo3}"
            if identificar_patrones.vela3_valor_cerro < mitad_cuerpo_vela1:
                config.datos_graficos["log"] += f"\n    🚨 Vela 3 no cerro con valor mayor o igual a la mitad del cuerpo de la vela 1 - {identificar_patrones.vela3_valor_cerro} < {mitad_cuerpo_vela1}"
        else:
            config.datos_graficos["log"] += "\n    🚨 Tendencia bajista no detectada"

def log_estrella_del_atardecer(mitad_cuerpo_vela1):
    if len(config.historico_macd) > 1:
        config.datos_graficos["log"] += "\n\n ℹ️  Evaluando ESTRELLA DEL ATARDECER"

        if not identificar_patrones.es_tendencia_bajista:
            if not identificar_patrones.macd_debil_alcista:
                config.datos_graficos["log"] += "\n    🚨 MACD débil alcista no detectado"
            if not identificar_patrones.es_verde1:
                config.datos_graficos["log"] += "\n    🚨 Vela 1 no es verde"
            if not identificar_patrones.es_roja3:
                config.datos_graficos["log"] += "\n    🚨 Vela 3 no es roja"
            if identificar_patrones.cuerpo2 > identificar_patrones.cuerpo1 * 0.35:
                config.datos_graficos["log"] += f"\n    🚨 Cuerpo de la vela 2 es mayor que el 35% del cuerpo de la vela 1 - {identificar_patrones.cuerpo2} > {identificar_patrones.cuerpo1 * 0.35}"
            if identificar_patrones.cuerpo3 <= 0:
                config.datos_graficos["log"] += f"\n    🚨 Cuerpo de la vela 3 menor o igual a cero - {identificar_patrones.cuerpo3}"
            if identificar_patrones.vela3_valor_cerro > mitad_cuerpo_vela1:
                config.datos_graficos["log"] += f"\n    🚨 Vela 3 no cerro con valor menor o igual a la mitad del cuerpo de la vela 1 - {identificar_patrones.vela3_valor_cerro} > {mitad_cuerpo_vela1}"
        else:
            config.datos_graficos["log"] += "\n    🚨 Tendencia alcista no detectada"