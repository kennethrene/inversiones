import numpy as np
import pandas as pd
import pandas_ta_classic as ta
from tvDatafeed import Interval

def obtener_datos_indicadores(lista_diccionarios_raw):
    """
    Recibe la lista de diccionarios del broker.
    Calcula de forma nativa RSI_4, MACD, Bandas de Bollinger completas (Sup, Mid, Inf) y Volatilidad.
    Devuelve la matriz formateada en texto plano y la volatilidad de la Vela 0.
    """
    df = pd.DataFrame(lista_diccionarios_raw)
    
    columnas_base = ['Open', 'High', 'Low', 'Close']
    df[columnas_base] = df[columnas_base].astype(float)
    
    # -------------------------------------------------------------------------
    # 1. CÁLCULO DEL RSI ULTRA-REACTIVO DE 4 PERÍODOS (RSI_4)
    # -------------------------------------------------------------------------
    periodo_rsi = 4
    delta = df['Close'].diff()
    
    gain = (delta.where(delta > 0, 0)).rolling(window=periodo_rsi).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=periodo_rsi).mean()
    
    for i in range(periodo_rsi, len(df)):
        gain.iloc[i] = (gain.iloc[i-1] * (periodo_rsi - 1) + (delta.iloc[i] if delta.iloc[i] > 0 else 0)) / periodo_rsi
        loss.iloc[i] = (loss.iloc[i-1] * (periodo_rsi - 1) + (-delta.iloc[i] if delta.iloc[i] < 0 else 0)) / periodo_rsi
    
    rs = gain / loss
    df['RSI_4'] = 100 - (100 / (1 + rs))
    
    # -------------------------------------------------------------------------
    # 2. OTROS INDICADORES (MACD, BOLLINGER COMPLETO, VP)
    # -------------------------------------------------------------------------
    # MACD Histograma (12, 26, 9)
    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = macd_line - signal_line
    
    # Bandas de Bollinger (20, 2) - INCLUYENDO BANDA MEDIA (Bollinger_Mid)
    df['Bollinger_Mid'] = df['Close'].rolling(window=20).mean() # SMA de 20 períodos
    std20 = df['Close'].rolling(window=20).std()
    df['Bollinger_Sup'] = df['Bollinger_Mid'] + (std20 * 2)
    df['Bollinger_Inf'] = df['Bollinger_Mid'] - (std20 * 2)
    
    # Volatilidad Promedio (VP_actual - Últimas 20 velas)
    df['rango_vela'] = df['High'] - df['Low']
    df['VP_actual'] = df['rango_vela'].rolling(window=20).mean()
    
    # -------------------------------------------------------------------------
    # 3. LIMPIEZA Y RECORTE PARA EL PROMPT
    # -------------------------------------------------------------------------
    df.dropna(subset=['RSI_4', 'MACD_Hist', 'Bollinger_Sup', 'Bollinger_Mid', 'VP_actual'], inplace=True)
    
    df_ia = df.tail(60).copy()
    total_filas = len(df_ia)
    
    # Formatear el índice retrospectivo hasta 0
    df_ia['Vela'] = range(-total_filas + 1, 1)
    
    # Redondear precios e indicadores para optimizar el consumo de tokens en la API
    columnas_precio = ['Open', 'High', 'Low', 'Close', 'Bollinger_Sup', 'Bollinger_Mid', 'Bollinger_Inf']
    df_ia[columnas_precio] = df_ia[columnas_precio].round(2)
    df_ia['RSI_4'] = df_ia['RSI_4'].round(2)
    df_ia['MACD_Hist'] = df_ia['MACD_Hist'].round(2)
    df_ia['VP_actual'] = df_ia['VP_actual'].round(2)
    
    # Seleccionar las columnas finales con la Banda Media integrada en su posición técnica correcta
    columnas_finales = ['Vela', 'Open', 'High', 'Low', 'Close', 'RSI_4', 'MACD_Hist', 'Bollinger_Sup', 'Bollinger_Mid', 'Bollinger_Inf', 'VP_actual']
    df_resultado = df_ia[columnas_finales].reset_index(drop=True)
    
    vp_actual_global = df_resultado.iloc[-1]['VP_actual']
    
    return df_resultado, vp_actual_global

