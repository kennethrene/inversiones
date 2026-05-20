import pytest
import pandas as pd
import numpy as np

# Importación segura del módulo de trading original
import at1g
from at1g import analizar_triple_confluencia, datos_compartidos

# ===========================================================================
# ⚙️ FIXTURE BASE Y REINICIADOR DE ESTADO
# ===========================================================================

@pytest.fixture(autouse=True)
def reiniciar_variables_globales():
    """Limpia el diccionario global antes de cada test."""
    datos_compartidos["indice_senal"] = None
    datos_compartidos["tipo_senal"] = None
    datos_compartidos["senal_accion"] = "🔎 ESPERANDO CONFIGURACIÓN..."
    yield

def generar_base_12_velas():
    """Genera un DataFrame base de 12 velas con valores planos para modificar."""
    data = {
        'Open':  [100.0] * 12,
        'High':  [100.0] * 12,
        'Low':   [100.0] * 12,
        'Close': [100.0] * 12
    }
    return pd.DataFrame(data, index=pd.date_range("2026-01-01", periods=12, freq="1min"))


# ===========================================================================
# 🧠 1. PATRONES COMPUESTOS DE ESTRELLAS (3 VELAS)
# ===========================================================================

def test_estrella_del_amanecer():
    """Vela 1 Roja Grande, Vela 2 Cuerpo Pequeño, Vela 3 Verde Grande."""
    data = {
        'Open':  [135.0, 132.0, 133.0, 128.0, 125.0, 121.0, 118.0, 115.0, 116.0, 110.0, 102.0, 100.0],
        'High':  [136.0, 134.0, 134.0, 129.0, 126.0, 122.0, 119.0, 117.0, 117.0, 111.0, 103.0, 107.0],
        'Low':   [131.0, 129.0, 127.0, 124.0, 120.0, 117.0, 113.0, 111.0, 109.0, 101.0,  99.0,  99.0],
        'Close': [132.0, 133.0, 128.0, 125.0, 121.0, 118.0, 115.0, 112.0, 110.0, 102.0, 101.0, 106.0]
    }
    df = pd.DataFrame(data, index=pd.date_range("2026-01-01", periods=12, freq="1min"))
    
    resultado = analizar_triple_confluencia(df, rsi_puro=10.0, adx_puro=30.0)
    assert "COMPRA" in resultado
    assert "Estrella del Amanecer" in datos_compartidos["senal_accion"]

'''
def test_estrella_del_atardecer():
    """Vela 1 Verde Grande, Vela 2 Cuerpo Pequeño, Vela 3 Roja Grande."""
    data = {
        'Open':  [100.0, 108.0, 110.0],
        'High':  [109.0, 111.0, 111.0],
        'Low':   [99.0,  107.0, 101.0],
        'Close': [108.0, 109.0, 103.0]
    }
    df = pd.DataFrame(data, index=pd.date_range("2026-01-01", periods=3, freq="1min"))
    
    resultado = analizar_triple_confluencia(df, rsi_puro=90.0, adx_puro=30.0)
    assert "VENTA" in resultado
    assert "Estrella del Atardecer" in datos_compartidos["senal_accion"]


# ===========================================================================
# 🧠 2. PATRONES TRADICIONALES DE 1 Y 2 VELAS (SEPARADOS)
# ===========================================================================
def test_envolvente_alcista():
    """Vela 2 Roja Pequeña, Vela 3 Verde Grande que cubre por completo a la previa."""
    data = {
        'Open':  [100.0, 104.0, 101.0],
        'High':  [101.0, 105.0, 106.0],
        'Low':   [99.0,  102.0, 100.0],
        'Close': [100.5, 103.0, 105.0]
    }
    df = pd.DataFrame(data, index=pd.date_range("2026-01-01", periods=3, freq="1min"))
    
    resultado = analizar_triple_confluencia(df, rsi_puro=10.0, adx_puro=30.0)
    assert "COMPRA" in resultado
    assert "Envolvente Alcista" in datos_compartidos["senal_accion"]


def test_envolvente_bajista():
    """Vela 2 Verde Pequeña, Vela 3 Roja Grande que cubre por completo a la previa."""
    data = {
        'Open':  [100.0, 102.0, 105.0],
        'High':  [101.0, 104.0, 106.0],
        'Low':   [99.0,  101.0, 100.0],
        'Close': [100.5, 103.0, 101.0]
    }
    df = pd.DataFrame(data, index=pd.date_range("2026-01-01", periods=3, freq="1min"))
    
    resultado = analizar_triple_confluencia(df, rsi_puro=90.0, adx_puro=30.0)
    assert "VENTA" in resultado
    assert "Envolvente Bajista" in datos_compartidos["senal_accion"]


def test_martillo_alcista():
    """Vela 3 Verde con mecha inferior muy larga y mecha superior casi nula."""
    data_martillo = {
        'Open':  [108.0, 105.0, 104.0], 
        'High':  [108.5, 105.5, 104.05],
        'Low':   [104.5, 102.5, 97.0], 
        'Close': [105.0, 103.0, 103.0]
    }
    df = pd.DataFrame(data_martillo, index=pd.date_range("2026-01-01", periods=3, freq="1min"))
    resultado = analizar_triple_confluencia(df, rsi_puro=10.0, adx_puro=30.0)
    assert "COMPRA" in resultado
    assert "Martillo (Hammer)" in datos_compartidos["senal_accion"]


def test_martillo_invertido_alcista():
    """Vela 3 Verde con mecha superior muy larga y mecha inferior casi nula, precedida de tendencia bajista."""
    data_martillo_inv = {
        'Open':  [108.0, 105.0, 100.0], 
        'High':  [108.5, 105.5, 104.0],
        'Low':   [104.5, 102.5, 99.95], 
        'Close': [105.0, 103.0, 101.0]
    }
    df = pd.DataFrame(data_martillo_inv, index=pd.date_range("2026-01-01", periods=3, freq="1min"))
    resultado = analizar_triple_confluencia(df, rsi_puro=10.0, adx_puro=30.0)
    
    assert "COMPRA" in resultado
    assert "Martillo Invertido" in datos_compartidos["senal_accion"]

def test_estrella_fugaz_bajista():
    """Vela 3 Roja tipo Estrella Fugaz. Vela 2 muy grande para evitar Estrella del Atardecer y Envolvente."""
    data_estrella = {
        'Open':  [85.0, 88.0,  101.0], 
        'High':  [88.5, 98.5,  104.0], 
        'Low':   [84.5, 87.5,  100.95], 
        'Close': [88.0, 98.0,  102.0]
    }
    df = pd.DataFrame(data_estrella, index=pd.date_range("2026-01-01", periods=3, freq="1min"))
    resultado = analizar_triple_confluencia(df, rsi_puro=90.0, adx_puro=30.0)
    
    assert "VENTA" in resultado
    assert "Estrella Fugaz" in datos_compartidos["senal_accion"]


# ===========================================================================
# 🧠 3. ESTRUCTURAS COMPLEJAS (12 VELAS)
# ===========================================================================

def test_doble_techo():
    """Genera dos picos idénticos de precio en los últimos 12 periodos."""
    df = generar_base_12_velas()
    df['High'] = [100, 105.0, 100, 100, 105.5, 100, 100, 100, 100, 100, 100, 100]
    
    resultado = analizar_triple_confluencia(df, rsi_puro=90.0, adx_puro=35.0)
    assert "VENTA" in resultado
    assert "Doble Techo" in datos_compartidos["senal_accion"]


def test_doble_suelo():
    """Genera dos valles idénticos de precio en los últimos 12 periodos."""
    df = generar_base_12_velas()
    df['Low'] = [100, 95.0, 100, 100, 95.0, 100, 100, 100, 100, 100, 100, 100]
    
    resultado = analizar_triple_confluencia(df, rsi_puro=10.0, adx_puro=35.0)
    assert "COMPRA" in resultado
    assert "Doble Suelo" in datos_compartidos["senal_accion"]


def test_hombro_cabeza_hombro():
    """Genera un patrón HCH: Pico izquierdo, Cabeza alta, Pico derecho similar al izquierdo."""
    df = generar_base_12_velas()
    df['High'] = [100, 105.0, 100, 100, 110.0, 100, 100, 105.02, 100, 100, 100, 100]
    
    resultado = analizar_triple_confluencia(df, rsi_puro=95.0, adx_puro=40.0)
    assert "VENTA" in resultado
    assert "Hombro-Cabeza-Hombro" in datos_compartidos["senal_accion"]


def test_hch_invertido():
    """Genera un patrón HCH Invertido en los soportes mínimos."""
    df = generar_base_12_velas()
    df['Low'] = [100, 95.0, 100, 100, 85.0, 100, 100, 95.01, 100, 100, 100, 100]
    
    resultado = analizar_triple_confluencia(df, rsi_puro=5.0, adx_puro=40.0)
    assert "COMPRA" in resultado
    assert "HCH Invertido" in datos_compartidos["senal_accion"]


def test_martillo_rojo_con_triple_confluencia():
    """Valida un Martillo Rojo con RSI en sobreventa y ADX fuerte (Señal de COMPRA completa)."""
    # 1. Creamos la estructura de 3 velas en tendencia bajista con un Martillo Rojo al final
    data_martillo_completo = {
        # Vela 1: Roja (Abre en 108.0, cierra en 105.0)
        # Vela 2: Roja (Abre en 105.0, cierra en 103.0) -> Mantiene la escalera bajista
        # Vela 3: Martillo Rojo (Open 104.0, Close 103.0 -> Cuerpo = 1.0)
        #         High 104.05 (Mecha Sup = 0.05, cumple <= 0.2 * cuerpo)
        #         Low 97.0    (Mecha Inf = 6.0, cumple >= 2 * cuerpo)
        'Open':  [108.0, 105.0, 104.0], 
        'High':  [108.5, 105.5, 104.05],
        'Low':   [104.5, 102.5, 97.0], 
        'Close': [105.0, 103.0, 103.0]
    }
    df = pd.DataFrame(data_martillo_completo, index=pd.date_range("2026-01-01", periods=3, freq="1min"))
    idx_esperado = df.index[-1]

    # 2. Inyectamos los indicadores que aprueban el filtro estricto de tu bot
    # RSI_SOBREVENTA = 15.0 -> Ponemos 12.0 (Sobreventa extrema)
    # ADX_TENDENCIA_FUERTE = 25.0 -> Ponemos 32.0 (Tendencia con fuerza)
    resultado = analizar_triple_confluencia(df, rsi_puro=12.0, adx_puro=32.0)
    
    # 3. Verificamos que el sistema apruebe la operación comercial
    assert "COMPRA" in resultado
    assert datos_compartidos["tipo_senal"] == "COMPRA"
    assert datos_compartidos["indice_senal"] == idx_esperado
    assert "RSI LOW + ADX FUERTE" in datos_compartidos["senal_accion"]


def test_martillo_descartado_por_indicadores():
    """Detecta el Martillo pero lo rechaza porque el RSI es neutral o el ADX es débil."""
    # 1. Creamos la misma estructura perfecta del Martillo Rojo en tendencia bajista
    data_martillo_falso = {
        'Open':  [108.0, 105.0, 104.0], 
        'High':  [108.5, 105.5, 104.05],
        'Low':   [104.5, 102.5, 97.0], 
        'Close': [105.0, 103.0, 103.0]
    }
    df = pd.DataFrame(data_martillo_falso, index=pd.date_range("2026-01-01", periods=3, freq="1min"))

    # 2. Inyectamos indicadores fuera de rango (Mercado en rango / consolidación débil):
    # - RSI = 45.0 (Zona neutral, el precio no está lo suficientemente barato/sobrevendido)
    # - ADX = 14.0 (ADX < 25 significa mercado muerto, sin fuerza institucional)
    resultado = analizar_triple_confluencia(df, rsi_puro=45.0, adx_puro=14.0)
    
    # 3. VERIFICACIONES CRÍTICAS DE SEGURIDAD:
    # El retorno del script debe avisar que la estructura fue descartada por los filtros
    assert "descartada" in resultado.lower() or "filtro" in resultado.lower()
    
    # No se debe generar ninguna orden comercial en el diccionario compartido
    assert datos_compartidos["tipo_senal"] is None
    assert datos_compartidos["indice_senal"] is None
    assert "Filtro activo" in datos_compartidos["senal_accion"]
'''