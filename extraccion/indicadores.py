def calcular_valor_vp(velas):
    """
    Calcula el promedio simple del tamaño (High - Low) de las últimas 20 velas.
    velas_m5: Lista de diccionarios o filas del CSV con las 60 velas.
    """
    # Tomamos estrictamente las últimas 20 velas de la serie
    ultimas_20_velas = velas[-20:]
    
    suma_tamaños = 0.0
    for vela in ultimas_20_velas:
        # Restamos High - Low de cada vela
        tamaño_vela = float(vela['High']) - float(vela['Low'])
        suma_tamaños += tamaño_vela
        
    # Calculamos el promedio simple y redondeamos a 2 decimales
    promedio_vp = suma_tamaños / 20
    return round(promedio_vp, 2)

def calcular_metricas_vela_actual(ultima_vela, b_inferior, b_media, b_superior):
    """
    Calcula los valores aritméticos exactos de la Vela 0.
    vela_0: Diccionario con los datos puros { 'Open', 'High', 'Low', 'Close' } de la última fila.
    b_inferior, b_media, b_superior: Valores flotantes de Bollinger provistos por tu sistema.
    """
    # 1. Extracción de precios flotantes de la Vela 0
    open  = float(ultima_vela['Open'])
    high  = float(ultima_vela['High'])
    low   = float(ultima_vela['Low'])
    close = float(ultima_vela['Close'])
    
    # 2. Cálculo de la anatomía exacta de la Vela 0
    cuerpo0    = abs(open - close)
    mecha_inf0 = min(open, close) - low
    mecha_sup0 = high - max(open, close)
    
    # 3. Mediciones de Clímax (Banda vs Extremos del precio)
    diferencia_bol_inf_low = b_inferior - low
    diferencia_bol_sup_high = high - b_superior
    
    # 4. Restas de Validación de Gatillos (Mecha real menos exigencia del 1.5x Cuerpo)
    diferencia_mecha_inf_cuerpo = mecha_inf0 - (cuerpo0 * 1.5)
    diferencia_mecha_sup_cuerpo = mecha_sup0 - (cuerpo0 * 1.5)

    diferencia_media_low = b_media - low
    diferencia_media_hig = high - b_media

    if close >= b_media:
        zona_actual = "Techo"
    else:
        zona_actual = "Suelo"
    
    # 5. Retornamos el diccionario mapeado con redondeo a 2 decimales
    return {
        "close_M5": round(close, 2),
        "diferencia_bol_inf_low": round(diferencia_bol_inf_low, 2),
        "diferencia_bol_sup_high": round(diferencia_bol_sup_high, 2),
        "diferencia_mecha_inf_cuerpo": round(diferencia_mecha_inf_cuerpo, 2),
        "diferencia_mecha_sup_cuerpo": round(diferencia_mecha_sup_cuerpo, 2),
        "zona_actual": zona_actual,
        "diferencia_media_low": diferencia_media_low,
        "diferencia_media_high": diferencia_media_hig
    }

def determinar_tendencia(velas):
    """
    Determina la macro-tendencia midiendo la pendiente y dirección de la BolMid.
    velas_h1: Lista con exactamente las últimas 30 velas cerradas de 1 hora.
    """
    # Tomamos los valores de la línea amarilla (BolMid) en las 4 estaciones del día:
    mid_presente = float(velas[-1]['Middle'])  # Hora 0
    mid_hace_6h   = float(velas[-7]['Middle'])  # Hora -6
    mid_hace_12h  = float(velas[-13]['Middle']) # Hora -12
    mid_hace_24h  = float(velas[-25]['Middle']) # Hora -24
    
    # Precios de cierre extremos del ciclo diario para confirmar el desplazamiento
    close_presente = float(velas[-1]['Close'])
    close_hace_24h = float(velas[-25]['Close'])
    
    # 1. EVALUACIÓN DE INCLINACIÓN ALCISTA (La línea amarilla sube escalonadamente):
    # Tolera que una intermedia sea plana, pero exige que la estructura suba en el tiempo.
    if mid_presente > mid_hace_12h and mid_hace_12h > mid_hace_24h and close_presente > close_hace_24h:
        return "Alcista_Estructural"
        
    # 2. EVALUACIÓN DE INCLINACIÓN BAJISTA (La línea amarilla cae escalonadamente):
    elif mid_presente < mid_hace_12h and mid_hace_12h < mid_hace_24h and close_presente < close_hace_24h:
        return "Bajista_Estructural"
        
    # 3. MERCADO PLANO O EN ZIGZAG EN EL DÍA:
    else:
        return "Neutral_Rango"
