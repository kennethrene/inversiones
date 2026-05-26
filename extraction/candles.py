from tvDatafeed import TvDatafeed, Interval
import config

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

def extraer_velas():
    # 1. Inicializar la conexión con TradingView
    tv = TvDatafeed()

    # 2. Descargar las últimas 60 velas de FX:NAS100
    df = tv.get_hist(
        symbol=symbols.get(config.activo_actual),
        exchange='FX', 
        interval=Interval.in_1_minute,
        n_bars=61
    )

    # 3. Procesar, renombrar columnas y convertir al formato solicitado
    if df is not None and not df.empty:
        df = df[['open', 'high', 'low', 'close']]
        df.columns = ['Open', 'High', 'Low', 'Close']
        data = df.to_dict(orient='records')

        return data[:-1]
    else:
        config.error = "Error: No se recibieron datos de TradingView"