from tvDatafeed import TvDatafeed
import configuracion.parametros as parametros
from datetime import datetime
import pandas_ta_classic as ta
import pandas as pd

symbols = {
    "US100": "NAS100",
    "US30": "US30",
    "US500": "SPX500",
    "US2000": "US2000",
    "DE40": "GER30",
    "FRA40": "FRA40",
    "UK100": "UK100",
    "HK.cash": "HKG33",
    "GOLD": "XAUUSD",
    "COCOA": "COCOA",
    "COFFEE": "COFFEE",
    "OIL": "USOIL",
    "USDJPY": "USDJPY",
    "JP225": "JPN225",
    "EURUSD": "EURUSD"
}

reintentos = 0
max_reintentos = 3

def extraer_velas(intervalo):
    # 1. Inicializar la conexión con TradingView
    tv = TvDatafeed()

    # 2. Descargar las últimas 60 velas de FX
    df = tv.get_hist(
        symbol=symbols.get(parametros.activo_actual),
        exchange='FX', 
        interval=intervalo,
        n_bars=61
    )

    # 3. Procesar, renombrar columnas y convertir al formato solicitado
    if df is not None and not df.empty:
        df = df[['open', 'high', 'low', 'close']]
        df.columns = ['Open', 'High', 'Low', 'Close']
        data = df.to_dict(orient='records')

        return data[:-1]
    else:
        hora = datetime.now()
        parametros.error = f"Error: No se recibieron datos de TradingView ({hora.strftime('%H:%M')})\n"

def extraer_velas_para_IA(activo_actual, intervalo, num_velas, indicador):
    if indicador is not None and indicador == "Bollinger":
        return extraer_velas_con_bollinger(activo_actual, intervalo, num_velas)
    elif indicador is not None and indicador == "Bollinger-MACD":
        return extraer_velas_con_bollinger_macd(activo_actual, intervalo, num_velas)

    global reintentos, max_reintentos
    reintentos = 0

    # 1. Inicializar la conexión con TradingView
    tv = TvDatafeed()

    # 2. Descargar las últimas X velas de FX
    while reintentos < max_reintentos:
        try:
            df = tv.get_hist(
                symbol=symbols.get(activo_actual),
                exchange='FX', 
                interval=intervalo,
                n_bars=num_velas + 1
            )
            if df is not None and not df.empty:
                break
        except Exception as e:
            pass

        reintentos += 1
        hora = datetime.now()
        parametros.error = f"Error: No se recibieron datos de TradingView ({hora.strftime('%H:%M')}) (Reintento {reintentos})\n"

    # 3. Procesar, renombrar columnas y convertir al formato solicitado
    if df is not None and not df.empty:
        df = df[['open', 'high', 'low', 'close']]
        df.columns = ['Open', 'High', 'Low', 'Close']
        data = df.to_dict(orient='records')

        parametros.lista_velas_acumuladas = data
        return data
    else:
        hora = datetime.now()
        parametros.error = f"Error: No se recibieron datos de TradingView ({hora.strftime('%H:%M')})\n"
    
    # Forzar la lectura de todas las velas en la próxima lectura
    parametros.lista_velas_acumuladas = []
    return None

def extraer_velas_para_indicadores(activo_actual, intervalo, num_velas):
    global reintentos, max_reintentos
    reintentos = 0

    # 1. Inicializar la conexión con TradingView
    tv = TvDatafeed()

    # 2. Descargar las últimas X velas de FX
    while reintentos < max_reintentos:
        try:
            df = tv.get_hist(
                symbol=symbols.get(activo_actual),
                exchange='FX', 
                interval=intervalo,
                n_bars=num_velas + 1
            )
            if df is not None and not df.empty:
                break
        except Exception as e:
            pass

        reintentos += 1
        hora = datetime.now()
        parametros.error = f"Error: No se recibieron datos de TradingView ({hora.strftime('%H:%M')}) (Reintento {reintentos})\n"

    # 3. Procesar, renombrar columnas y convertir al formato solicitado
    if df is not None and not df.empty:
        df = df[['open', 'high', 'low', 'close']]
        df.columns = ['Open', 'High', 'Low', 'Close']
        data = df.to_dict(orient='records')

        parametros.lista_velas_acumuladas = data
        return data
    else:
        hora = datetime.now()
        parametros.error = f"Error: No se recibieron datos de TradingView ({hora.strftime('%H:%M')})\n"
    
    # Forzar la lectura de todas las velas en la próxima lectura
    parametros.lista_velas_acumuladas = []
    return None

def extraer_velas_con_bollinger(activo_actual, intervalo, num_velas):
    global reintentos, max_reintentos
    reintentos = 0

    # 1. Inicializar la conexión con TradingView
    tv = TvDatafeed()
    df = None

    # 2. Descargar las últimas X velas de FX
    while reintentos < max_reintentos:
        try:
            raw_data = tv.get_hist(
                symbol=symbols.get(activo_actual),
                exchange='FX', 
                interval=intervalo,
                n_bars=num_velas + 1
            )
            
            # BLINDAJE: Validamos que la respuesta sea un DataFrame y que no esté vacío
            quitar_velas = 1
            if parametros.DEBUG:
                quitar_velas = parametros.DEBUG_QUITAR_VELAS

            if isinstance(raw_data, pd.DataFrame) and not raw_data.empty:
                df = raw_data.iloc[:-quitar_velas].copy()
                break
        except Exception as e:
            hora = datetime.now()
            parametros.error = f"Error al extraer datos de TradingView ({hora.strftime('%H:%M')}): {str(e)}\n"
            parametros.lista_velas_acumuladas = []
            return None

        reintentos += 1
        hora = datetime.now()
        parametros.error = f"Error: No se recibieron datos de TradingView ({hora.strftime('%H:%M')}) (Reintento {reintentos})\n"

    # 3. Procesar, calcular indicadores, renombrar columnas y convertir al formato solicitado
    if df is not None:  # Ya sabemos con certeza que es un DataFrame válido con datos
        try:
            # Cálculo directo y seguro de Bandas de Bollinger sin depender del .ta accessor
            bbands = ta.bbands(df['close'], length=30, std=2)
            df = pd.concat([df, bbands], axis=1)
            
            # Filtro y renombre de columnas
            df = df[['open', 'high', 'low', 'close', 'BBL_30_2.0', 'BBM_30_2.0', 'BBU_30_2.0']]
            df.columns = ['Open', 'High', 'Low', 'Close', 'Lower', 'Middle', 'Upper']
           
        except Exception as e:
            hora = datetime.now()
            parametros.error += f"Error al calcular Bandas de Bollinger ({hora.strftime('%H:%M')}): {str(e)}\n"
            parametros.lista_velas_acumuladas = []
            return None

        # Convertir el DataFrame a una lista de diccionarios
        data = df.to_dict(orient='records')

        parametros.lista_velas_acumuladas = data
        return data
    else:
        hora = datetime.now()
        parametros.error = f"Error: No se recibieron datos de TradingView ({hora.strftime('%H:%M')})\n"
    
    parametros.lista_velas_acumuladas = []
    return None

def extraer_velas_con_bollinger_macd(activo_actual, intervalo, num_velas):
    global reintentos, max_reintentos
    reintentos = 0

    # 1. Inicializar la conexión con TradingView
    tv = TvDatafeed()
    df = None

    # 2. Descargar las últimas X velas de FX
    while reintentos < max_reintentos:
        try:
            raw_data = tv.get_hist(
                symbol=symbols.get(activo_actual),
                exchange='FX', 
                interval=intervalo,
                n_bars=num_velas + 1
            )
            
            # BLINDAJE: Validamos que la respuesta sea un DataFrame y que no esté vacío
            quitar_velas = 1
            if parametros.DEBUG:
                quitar_velas = parametros.DEBUG_QUITAR_VELAS

            if isinstance(raw_data, pd.DataFrame) and not raw_data.empty:
                df = raw_data.iloc[:-quitar_velas].copy()
                break
        except Exception as e:
            hora = datetime.now()
            parametros.error = f"Error al extraer datos de TradingView ({hora.strftime('%H:%M')}): {str(e)}\n"
            parametros.lista_velas_acumuladas = []
            return None

        reintentos += 1
        hora = datetime.now()
        parametros.error = f"Error: No se recibieron datos de TradingView ({hora.strftime('%H:%M')}) (Reintento {reintentos})\n"

    # 3. Procesar, calcular indicadores, renombrar columnas y convertir al formato solicitado
    if df is not None:  # Ya sabemos con certeza que es un DataFrame válido con datos
        try:
            # Cálculo directo y seguro de Bandas de Bollinger sin depender del .ta accessor
            bbands = ta.bbands(df['close'], length=30, std=2)
            
            # Cálculo de MACD (Parámetros estándar 12, 26, 9)
            macd = ta.macd(df['close'], fast=12, slow=26, signal=9)

            df = pd.concat([df, bbands, macd], axis=1)
            
            # Filtro y renombre de columnas
            df = df[['open', 'high', 'low', 'close', 'BBL_30_2.0', 'BBM_30_2.0', 'BBU_30_2.0', 'MACD_12_26_9', 'MACDh_12_26_9', 'MACDs_12_26_9']]
            df.columns = ['Open', 'High', 'Low', 'Close', 'Lower', 'Middle', 'Upper', 'MACD', 'MACD_Hist', 'MACD_Signal']
           
        except Exception as e:
            hora = datetime.now()
            parametros.error += f"Error al calcular Bandas de Bollinger y/o MACD ({hora.strftime('%H:%M')}): {str(e)}\n"
            parametros.lista_velas_acumuladas = []
            return None

        # Convertir el DataFrame a una lista de diccionarios
        data = df.to_dict(orient='records')

        parametros.lista_velas_acumuladas = data
        return data
    else:
        hora = datetime.now()
        parametros.error = f"Error: No se recibieron datos de TradingView ({hora.strftime('%H:%M')})\n"
    
    parametros.lista_velas_acumuladas = []
    return None