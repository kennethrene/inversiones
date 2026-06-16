from tvDatafeed import TvDatafeed
import configuracion.parametros as parametros
from datetime import datetime

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

def extraer_velas_para_IA(activo_actual, intervalo, num_velas):
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
                n_bars=num_velas
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

        if num_velas == 61:
            parametros.lista_velas_acumuladas = data[:-1]
            return data[:-1]

        # --- ACTUALIZACIÓN DINÁMICA DE 'N' VELAS ---
        # Verificamos que tengamos un historial base cargado previamente
        if len(parametros.lista_velas_acumuladas) >= num_velas:
            # Slices de Python: Reemplaza exactamente desde el índice [-num_velas] hasta el final
            parametros.lista_velas_acumuladas[-num_velas:] = data
            return parametros.lista_velas_acumuladas
        else:
            # Caso de contingencia si la lista acumulada está vacía o es menor que num_velas
            parametros.lista_velas_acumuladas = data
            return parametros.lista_velas_acumuladas
    else:
        hora = datetime.now()
        parametros.error = f"Error: No se recibieron datos de TradingView ({hora.strftime('%H:%M')})\n"
    
    # Forzar la lectura de todas las velas en la próxima lectura
    parametros.lista_velas_acumuladas = []
    return None