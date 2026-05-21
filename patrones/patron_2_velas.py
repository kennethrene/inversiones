import pandas as pd
import config
import patrones.identificar_patrones as identificar_patrones

# PATRONES TRADICIONALES DE 1 Y 2 VELAS
def analizar_patrones():
    nombre_patron = "Ninguno"
    tendencia_alcista = False
    tendencia_bajista = False

    vela3_cuerpo = identificar_patrones.cuerpo3
    mecha_sup = identificar_patrones.vela3_valor_maximo - max(identificar_patrones.vela3_valor_abrio, identificar_patrones.vela3_valor_cerro)
    mecha_inf = min(identificar_patrones.vela3_valor_abrio, identificar_patrones.vela3_valor_cerro) - identificar_patrones.vela3_valor_minimo
    rango_total = identificar_patrones.vela3_valor_maximo - identificar_patrones.vela3_valor_minimo
    es_vela3_verde = identificar_patrones.es_verde3
    vela2_cuerpo = identificar_patrones.cuerpo2
    es_vela2_verde = identificar_patrones.vela2_valor_cerro > identificar_patrones.vela2_valor_abrio
    
    if rango_total > 0:
        velas_cuerpo_env = vela3_cuerpo > vela2_cuerpo * 1.5 and vela3_cuerpo > config.promedio_volumen * 1.3
        velas_ok_env_alc = es_vela3_verde and not es_vela2_verde            
        velas_cierre_env_alc = identificar_patrones.vela3_valor_cerro > identificar_patrones.vela2_valor_abrio

        velas_ok_env_baj = not es_vela3_verde and es_vela2_verde
        velas_cierre_env_baj = identificar_patrones.vela3_valor_cerro < identificar_patrones.vela2_valor_abrio

        volumen_velas_anteriores_ok = config.promedio_volumen_sin_actual != None and len(config.historico_volumen) > 0 and config.historico_volumen[-1] > config.promedio_volumen_sin_actual * 1.3
        mechas_ok_martillo = mecha_inf >= (2 * vela3_cuerpo) and mecha_sup < (0.2 * vela3_cuerpo)
        mechas_ok_martillo_rojo = (mecha_inf >= 2 * vela3_cuerpo) and (mecha_sup <= 0.2 * vela3_cuerpo)
        mechas_ok_martillo_inv = mecha_sup >= (2 * vela3_cuerpo) and mecha_inf < (0.2 * vela3_cuerpo)

        mechas_ok_estrella_fugaz = mecha_sup >= (2 * vela3_cuerpo) and mecha_inf <= (0.2 * vela3_cuerpo)
        mechas_ok_hombre_colgado = mecha_inf >= (2 * vela3_cuerpo) and mecha_sup < (0.2 * vela3_cuerpo)

        if identificar_patrones.es_tendencia_bajista and identificar_patrones.macd_debil_bajista and velas_ok_env_alc and velas_cuerpo_env and velas_cierre_env_alc:
                tendencia_alcista, nombre_patron = True, "Envolvente Alcista"
        elif not identificar_patrones.es_tendencia_bajista and identificar_patrones.macd_debil_alcista and velas_ok_env_baj and velas_cuerpo_env and velas_cierre_env_baj:
            tendencia_bajista, nombre_patron = True, "Envolvente Bajista"

        # MARTILLO
        elif identificar_patrones.es_tendencia_bajista and volumen_velas_anteriores_ok and identificar_patrones.macd_debil_bajista and mechas_ok_martillo:
            tendencia_alcista, nombre_patron = True, "Martillo (Hammer)"
        # ESTRELLA FUGAZ
        elif not identificar_patrones.es_tendencia_bajista and volumen_velas_anteriores_ok and identificar_patrones.macd_debil_alcista and mechas_ok_estrella_fugaz:
            tendencia_bajista, nombre_patron = True, "Estrella Fugaz"
        # MARTILLO INVERTIDO
        elif identificar_patrones.es_tendencia_bajista and volumen_velas_anteriores_ok and identificar_patrones.macd_debil_bajista and mechas_ok_martillo_inv:
            tendencia_alcista, nombre_patron = True, "Martillo Invertido"
        # HOMBRE COLGADO
        elif not identificar_patrones.es_tendencia_bajista and volumen_velas_anteriores_ok and identificar_patrones.macd_debil_alcista and mechas_ok_hombre_colgado:
            tendencia_bajista, nombre_patron = True, "Hombre Colgado"

    return tendencia_alcista, tendencia_bajista, nombre_patron