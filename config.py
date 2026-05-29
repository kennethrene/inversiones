import pandas as pd

# ===========================================================================
# ⚙ CONFIGURACIÓN DE PARÁMETROS GLOBALES DE TRADING (MACD + RSI + ADX)
# ===========================================================================
TEMPORALIDAD_MINUTOS = 5    # Intervalo de corte de la vela (ej: 1, 5, 15)
RSI_SOBRECOMPRA = 80.0      # Nivel estricto de sobrecompra para ventas
RSI_SOBREVENTA = 15.0       # Nivel estricto de sobreventa para compras
RSI_SOBRECOMPRA_MACD = 70.0 # Nivel de sobreventa para compras para validar con macd
RSI_SOBREVENTA_MACD = 30.0  # Nivel de sobreventa para compras para validar con macd
ADX_TENDENCIA_FUERTE = 25.0 # Filtro de fuerza obligatorio para operar
VOL_ADECUADO_OPERAR = 4000
CRITERIO_MACD_FUERTE = 1.5
PORCENTAJE_BOLLINGER_BANDA_MEDIA = 0.75 # Porcentaje (entre 0 y 1) del límite entre las bandas exteriores y la media para saber si el precio está cerca del extremo

# 💰 PARÁMETROS DE GESTIÓN DE RIESGO AVANZADA (MONEY MANAGEMENT)
PORCENTAJE_STOP_LOSS = -10.0            # Límite estricto de pérdida permitida (debe ser NEGATIVO)
PORCENTAJE_ACTIVACION_TRAILING = 15.0   # % mínimo de ganancia para activar la persecución inteligente
DISTANCIA_TRAILING_MAXIMA = 4.0         # % máximo que permites que el precio retroceda desde su pico
TAKE_PROFIT_MONETARIO = 5.0             # 🔥 Modifica este valor por la ganancia deseada
PORCENTAJE_STOP_LOSS  = -20.0           # 🔴 Límite estricto de pérdida permitida en % (Gatillo SL)

# PARÁMETROS DE INDICADORES DE DOBLE TECHO / SUELO Y HOMBRE CABEZA HOMBRO
ENABLE_COMPLEX_CANDLES = True
PORCENTAJE_TOLERANCIA_DOBLE_TS = 0.015  # 1.5% de tolerancia entre picos
PORCENTAJE_CAIDA_VALLE = 0.03           # Exige que el valle baje al menos un 3% desde el pico
PORCENTAJE_REBOTE_CRESTA = 0.03         # Exige que la cresta suba al menos un 3% desde el suelo
PORCENTAJE_TOLERANCIA_HOMBROS = 0.02    # 2% de diferencia máxima entre el hombro izquierdo y derecho
PORCENTAJE_FILTRO_CABEZA = 0.02         # La cabeza debe ser al menos un 2% más alta que los hombros

SEGUNDOS_ENFRIAMIENTO = float(TEMPORALIDAD_MINUTOS * 60) / 2  # 🔥 Tiempo mínimo en segundos para esperar entre operaciones
TIEMPO_ULTIMO_CIERRE = 0.0    # Rastreo del timestamp del último cierre

# ============================================================================
# CONFIGURACION DE ESTRATEGIAS HABILITADAS
# ============================================================================
CRITERIO1 = False
CRITERIO2 = False
CRITERIO3 = True
CRITERIO4 = False
CRITERIO5 = False
CRITERIO6 = True # Extremo

CRITERIO_INDICADORES = [    
    {},
    {
        # 1
        "MACD": False,
        "RSI": True,
        "BOLLINGER": False,
        "EMA": False
    },
    {
        # 2
        "MACD": False,
        "RSI": True,
        "BOLLINGER": False,
        "EMA": False
    },
    {
        # 3
        "MACD": True,
        "RSI": False,
        "BOLLINGER": True,
        "EMA": False
    },
    {
        # 4
        "MACD": False,
        "RSI": True,
        "BOLLINGER": False,
        "EMA": True
    },
    {
        # 5
        "MACD": False,
        "RSI": True,
        "BOLLINGER": False,
        "EMA": False
    },
    {
        # 6
        "MACD": False,
        "RSI": False,
        "BOLLINGER": False,
        "EMA": False
    }
]
# ============================================================================
# Preload de valores iniciales para no esperar que pase el tiempo y tener info
# ============================================================================
cargar_datos = True
preload_historico_volumen =  [5000, 5000, 5492, 3817, 5425, 2564]
preload_historico_macd =  [7.91, 7.64, 5.06]
preload_historico_rsi = [55, 31]
preload_promedio_volumen = 5000
preload_promedio_volumen_sin_actual = 5000
preload_valor_compra_abrio = 0
preload_valor_venta_abrio = 0

# ===========================================================================
# Estructura global en memoria para compartir los datos entre hilos
# ===========================================================================
datos_graficos = {
    "hora_vela": None, # Guarda la estampa de tiempo del momento que el patrón gráfico fue detectado
    "datos_velas": pd.DataFrame(),
    "operacion": None, # COMPRA o VENTA
    "patron": "Ninguno",
    "log": ""
}

datos_mapeados = {
    "Activo": "N/D", 
    "Tipo": "N/D", 
    "Volumen": "N/D", 
    "Valor Contrato": "N/D", 
    "Precio Actual": "N/D", 
    "Precio Apertura": "N/D", 
    "Beneficio %": "N/D", 
    "Beneficio Neto": "N/D",
    "Operacion": "N/D",
    "Criterio Apertura": "N/D"
}

# 🟢 CONTADORES DE ESTADÍSTICA EN VIVO
estadisticas_bot = {
    "ganadas": 0,
    "perdidas": 0,
    "total_ordenes": 0,
    "ultimo_patron_operado": ""
}

activo_actual = None
valor_lote = None
spread = None
motivo_cierre_stats = None
hora_apertura_orden = None
lista_velas_acumuladas = []
historico_cuenta = []
historico_macd = []
historico_rsi = []
historico_volumen = []
promedio_volumen = 0.0
promedio_volumen_sin_actual = 0.0 # Promedio de los volumenes anteriores al actual
historico_velas = None
ultimo_patron = "Ninguno"
valor_rsi = 0.0
valor_adx = 0
valor_adx_compra = 0
valor_adx_venta = 0
valor_macd = 0
valor_volumen = 0
valor_ema_35 = 0
valor_ema_50 = 0
valor_bollinger_superior = 0
valor_bollinger_media = 0
valor_bollinger_inferior = 0
ultimo_valor_rsi = 0
log_operacion = None
valor_compra = None
valor_venta = None
ultimo_valor_compra = None
ultimo_valor_venta = None
valor_compra_abrio = 0.0
valor_venta_abrio = 0.0
ultimo_segundo_procesado = 0
penultimo_segundo_procesado = 0
ultimo_valor_volumen = 0
boton_comprar = None
boton_vender = None
trailing_activado = False
error = None

movimiento_abrupto = {
    "US100": 20.0,       # 6 puntos en 1 segundo es una aceleración violenta
    "US30": 15.0,       # 15 puntos en 1 segundo
    "US500": 2.5,       # 2.5 puntos en 1 segundo
    "US2000": 1.2,      # 1.2 puntos en 1 segundo
    "DE40": 5.0,        # 5 puntos en 1 segundo
    "FRA40": 3.0,       # 3 puntos en 1 segundo
    "UK100": 3.5,       # 3.5 puntos en 1 segundo
    "HK.CASH": 10.0,    # 10 puntos en 1 segundo
    "GOLD": 2.0,        # 2 dólares de salto en 1 segundo
    "COCOA": 25.0,      # 25 dólares en 1 segundo debido a su alta volatilidad
    "COFFEE": 1.5,      # 1.5 centavos en 1 segundo
    "OIL": 0.15,        # 0.15 dólares en 1 segundo
    "USDJPY": 0.08,     # 8 pips de salto en 1 segundo
    "JP225": 25.0,      # 25 yenes en 1 segundo
    "EURUSD": 0.0002    # 2 pips de salto en 1 segundo
}

porcentaje_bollinger_estrecho = {
    # ACTIVO:   % Máximo para considerar Bandas Pegadas (M5)
    "US100":     0.50,  # Comprimido si el rango total es menor al 0.50%
    "US30":      0.14,  # Comprimido si el rango total es menor al 0.15%
    "US500":     0.45,
    "US2000":    0.60,
    "DE40":      0.40,
    "FRA40":     0.45,
    "UK100":     0.50,
    "HK.CASH":   0.80,
    "GOLD":      0.60,
    "COCOA":     3.50,  # Rango más amplio por su alta volatilidad natural
    "COFFEE":    2.50,
    "OIL":       1.20,
    "USDJPY":    0.25,  # Las divisas requieren límites más ajustados
    "JP225":     0.65,
    "EURUSD":    0.15
}
