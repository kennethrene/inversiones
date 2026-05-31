from tvDatafeed import TvDatafeed
import configuracion.parametros as parametros

symbols = {
    "US100": "NAS100",
    "US30": "US30",
    "US500": "SPX500",
    "US2000": "US2000",
    "DE40": "GER30",
    "FRA40": "FRA40",
    "UK100": "UK100",
    "HK.CASH": "HKG33",
    "GOLD": "XAUUSD",
    "COCOA": "COCOA",
    "COFFEE": "COFFEE",
    "OIL": "USOIL",
    "USDJPY": "USDJPY",
    "JP225": "JPN225",
    "EURUSD": "EURUSD"
}

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
        parametros.error = "Error: No se recibieron datos de TradingView"

def extraer_velas_para_IA(activo_actual, intervalo):
    # 1. Inicializar la conexión con TradingView
    tv = TvDatafeed()

    # 2. Descargar las últimas 60 velas de FX
    df = tv.get_hist(
        symbol=symbols.get(activo_actual),
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
        error = "Error: No se recibieron datos de TradingView"