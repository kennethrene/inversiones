import pandas as pd

# ===========================================================================
# ⚙ CONFIGURACIÓN DE PARÁMETROS GLOBALES DE TRADING (MACD + RSI + ADX)
# ===========================================================================
TEMPORALIDAD_MINUTOS = 1 # Intervalo de corte de la vela (ej: 1, 5, 15)
RSI_SOBRECOMPRA = 80.0 # Nivel estricto de sobrecompra para ventas
RSI_SOBREVENTA = 15.0 # Nivel estricto de sobreventa para compras
ADX_TENDENCIA_FUERTE = 25.0 # Filtro de fuerza obligatorio para operar

# 💰 PARÁMETROS DE GESTIÓN DE RIESGO AVANZADA (MONEY MANAGEMENT)
PORCENTAJE_STOP_LOSS = -10.0 # Límite estricto de pérdida permitida (debe ser NEGATIVO)
PORCENTAJE_ACTIVACION_TRAILING = 5.0 # % mínimo de ganancia para activar la persecución inteligente
DISTANCIA_TRAILING_MAXIMA = 2.5 # % máximo que permites que el precio retroceda desde su pico
TAKE_PROFIT_MONETARIO = 3.0  # 🔥 Modifica este valor por la ganancia deseada
PORCENTAJE_STOP_LOSS  = -10.0  # 🔴 Límite estricto de pérdida permitida en % (Gatillo SL)

# PARÁMETROS DE INDICADORES DE DOBLE TECHO / SUELO Y HOMBRE CABEZA HOMBRO
PORCENTAJE_TOLERANCIA_DOBLE_TS = 0.015  # 1.5% de tolerancia entre picos
PORCENTAJE_CAIDA_VALLE = 0.03           # Exige que el valle baje al menos un 3% desde el pico
PORCENTAJE_REBOTE_CRESTA = 0.03         # Exige que la cresta suba al menos un 3% desde el suelo
PORCENTAJE_TOLERANCIA_HOMBROS = 0.02        # 2% de diferencia máxima entre el hombro izquierdo y derecho
PORCENTAJE_FILTRO_CABEZA = 0.02         # La cabeza debe ser al menos un 2% más alta que los hombros

SEGUNDOS_ENFRIAMIENTO = 60.0  # 🔥 Tiempo mínimo en segundos para esperar entre operaciones
tiempo_ultimo_cierre = 0.0     # Rastreo del timestamp del último cierre
# ===========================================================================
# Estructura global en memoria para compartir los datos entre hilos
# ===========================================================================
datos_compartidos = {
    "df_velas": pd.DataFrame(),
    "sell": "0.00",
    "buy": "0.00",
    "status_patrones": "Recolectando ticks de mercado...",
    "senal_accion": "🔎 ESPERANDO CONFIGURACIÓN...",
    "indice_senal": None, # Guarda la estampa de tiempo de la confluencia
    "tipo_senal": None, # COMPRA o VENTA
    "rsi_live": "Buscando...",
    "adx_live": "Buscando...",
    "lucro": "Sin operaciones abiertas",
    "trailing_status": "Inactivo"
}

# 🟢 CONTADORES DE ESTADÍSTICA EN VIVO
estadisticas_bot = {
    "ganadas": 0,
    "perdidas": 0,
    "total_ordenes": 0,
    "ultimo_patron_operado": "Ninguno"
}

activo_actual = None
motivo_cierre_stats = None
hora_apertura_orden = None
ticks_bloque_actual = []
lista_velas_acumuladas = []
historico_cuenta = []
historico_macd = []
historico_volumen = []
promedio_volumen = 0.0
promedio_volumen_sin_actual = None # Promedio de los volumenes anteriores al actual
error = None