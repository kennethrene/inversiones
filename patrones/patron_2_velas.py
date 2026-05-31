import pandas as pd
import configuracion.parametros as parametros
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
        velas_cuerpo_env = vela3_cuerpo > vela2_cuerpo * 1.5 and vela3_cuerpo > parametros.promedio_volumen * 1.3
        velas_ok_env_alc = es_vela3_verde and not es_vela2_verde            
        velas_cierre_env_alc = identificar_patrones.vela3_valor_cerro > identificar_patrones.vela2_valor_abrio

        velas_ok_env_baj = not es_vela3_verde and es_vela2_verde
        velas_cierre_env_baj = identificar_patrones.vela3_valor_cerro < identificar_patrones.vela2_valor_abrio

        volumen_velas_anteriores_ok = parametros.promedio_volumen_sin_actual != None and len(parametros.historico_volumen) > 0 \
            and parametros.historico_volumen[-1] > parametros.promedio_volumen_sin_actual * 1.3
        mechas_ok_martillo = mecha_inf >= (2 * vela3_cuerpo) and mecha_sup < (0.2 * vela3_cuerpo)
        mechas_ok_martillo_inv = mecha_sup >= (2 * vela3_cuerpo) and mecha_inf < (0.2 * vela3_cuerpo)

        mechas_ok_estrella_fugaz = mecha_sup >= (2 * vela3_cuerpo) and mecha_inf <= (0.2 * vela3_cuerpo)
        mechas_ok_hombre_colgado = mecha_inf >= (2 * vela3_cuerpo) and mecha_sup < (0.2 * vela3_cuerpo)
        
        # ENVOLVENTE
        if identificar_patrones.es_tendencia_bajista and identificar_patrones.macd_debil_bajista and velas_ok_env_alc and velas_cuerpo_env \
            and velas_cierre_env_alc:
                return True, False, "Envolvente Alcista"
        elif not identificar_patrones.es_tendencia_bajista and identificar_patrones.macd_debil_alcista and velas_ok_env_baj and velas_cuerpo_env \
            and velas_cierre_env_baj:
            return False, True, "Envolvente Bajista"
        
        log_envolvente(velas_ok_env_alc, velas_ok_env_baj, velas_cuerpo_env)

        # MARTILLO
        if identificar_patrones.es_tendencia_bajista and volumen_velas_anteriores_ok and identificar_patrones.macd_debil_bajista \
            and mechas_ok_martillo:
            return True, False, "Martillo (Hammer)"
        
        log_martillo(volumen_velas_anteriores_ok)
        
        # ESTRELLA FUGAZ
        if not identificar_patrones.es_tendencia_bajista and volumen_velas_anteriores_ok and identificar_patrones.macd_debil_alcista \
            and mechas_ok_estrella_fugaz:
            return False, True, "Estrella Fugaz"

        log_estrella_fugaz(volumen_velas_anteriores_ok)

        # MARTILLO INVERTIDO
        if identificar_patrones.es_tendencia_bajista and volumen_velas_anteriores_ok and identificar_patrones.macd_debil_bajista \
            and mechas_ok_martillo_inv:
            return True, False, "Martillo Invertido"

        log_martillo_invertido(volumen_velas_anteriores_ok)

        # HOMBRE COLGADO
        if not identificar_patrones.es_tendencia_bajista and volumen_velas_anteriores_ok and identificar_patrones.macd_debil_alcista \
            and mechas_ok_hombre_colgado:
            return False, True, "Hombre Colgado"
    
        log_hombre_colgado(volumen_velas_anteriores_ok)

    return tendencia_alcista, tendencia_bajista, nombre_patron

def log_hombre_colgado(volumen_velas_anteriores_ok):
    if len(parametros.historico_macd) > 1:
        parametros.datos_graficos["log"] += "\n\n ℹ️  Evaluando HOMBRE COLGADO"

        if not identificar_patrones.es_tendencia_bajista:
            if not volumen_velas_anteriores_ok:
                parametros.datos_graficos["log"] += "\n    🚨 Volumen de velas anteriores no cumple"
            if not identificar_patrones.macd_debil_alcista:
                parametros.datos_graficos["log"] += "\n    🚨 MACD débil alcista no detectado"
        else:
            parametros.datos_graficos["log"] += "\n    🚨 Tendencia alcista no detectada"

def log_martillo_invertido(volumen_velas_anteriores_ok):
    if len(parametros.historico_macd) > 1:
        parametros.datos_graficos["log"] += "\n\n ℹ️  Evaluando MARTILLO INVERTIDO"

        if identificar_patrones.es_tendencia_bajista:
            if not volumen_velas_anteriores_ok:
                parametros.datos_graficos["log"] += "\n    🚨 Volumen de velas anteriores no cumple"
            if not identificar_patrones.macd_debil_bajista:
                parametros.datos_graficos["log"] += "\n    🚨 MACD débil bajista no detectado"
        else:
            parametros.datos_graficos["log"] += "\n    🚨 Tendencia bajista no detectada"

def log_estrella_fugaz(volumen_velas_anteriores_ok):
    if len(parametros.historico_macd) > 1:
        parametros.datos_graficos["log"] += "\n\n ℹ️  Evaluando ESTRELLA FUGAZ"

        if not identificar_patrones.es_tendencia_bajista:
            if not volumen_velas_anteriores_ok:
                parametros.datos_graficos["log"] += "\n    🚨 Volumen de velas anteriores no cumple"
            if not identificar_patrones.macd_debil_alcista:
                parametros.datos_graficos["log"] += "\n    🚨 MACD débil alcista no detectado"
        else:
            parametros.datos_graficos["log"] += "\n    🚨 Tendencia alcista no detectada"

def log_martillo(volumen_velas_anteriores_ok):
    if len(parametros.historico_macd) > 1:
        parametros.datos_graficos["log"] += "\n\n ℹ️  Evaluando MARTILLO"

        if identificar_patrones.es_tendencia_bajista:
            if not volumen_velas_anteriores_ok:
                parametros.datos_graficos["log"] += "\n    🚨 Volumen de velas anteriores no cumple"
            if not identificar_patrones.macd_debil_bajista:
                parametros.datos_graficos["log"] += "\n    🚨 MACD débil bajista no detectado"
        else:
            parametros.datos_graficos["log"] += "\n    🚨 Tendencia bajista no detectada"

            
def log_envolvente(velas_ok_env_alc, velas_ok_env_baj, velas_cuerpo_env):
    if len(parametros.historico_macd) > 1:
        parametros.datos_graficos["log"] += "\n\n ℹ️  Evaluando ENVOLVENTE"
        
        if identificar_patrones.es_tendencia_bajista:
            if not identificar_patrones.macd_debil_bajista:
                parametros.datos_graficos["log"] += "\n    🚨 Tendencia bajista, pero MACD debil bajista no detectado"
            if not velas_ok_env_alc:
                parametros.datos_graficos["log"] += "\n    🚨 Tendencia bajista, pero vela envolvente alcista no cumple"
            if not velas_cuerpo_env:
                parametros.datos_graficos["log"] += "\n    🚨 Tendencia bajista, pero cuerpo de vela no cumple"
        if not identificar_patrones.es_tendencia_bajista:
            if not identificar_patrones.macd_debil_alcista:
                parametros.datos_graficos["log"] += "\n    🚨 Tendencia alcista, pero MACD debil alcista no detectado"
            if not velas_ok_env_baj:
                parametros.datos_graficos["log"] += "\n    🚨 Tendencia alcista, pero vela envolvente bajista no cumple"
            if not velas_cuerpo_env:
                parametros.datos_graficos["log"] += "\n    🚨 Tendencia alcista, pero cuerpo de vela no cumple"

