import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch

# Importación segura del módulo de trading original
from patrones.identificar_patrones import identificar_patrones
from config.config import datos_graficos

# ===========================================================================
# ⚙️ FIXTURE BASE Y REINICIADOR DE ESTADO
# ===========================================================================
@pytest.fixture(autouse=True)
def reiniciar_variables_globales():
    """Limpia el diccionario global antes de cada test."""
    datos_graficos["indice_senal"] = None
    datos_graficos["tipo_senal"] = None
    datos_graficos["patron"] = "🔎 ESPERANDO CONFIGURACIÓN..."
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
    
    with patch('config.historico_macd', [-0.5, -0.2]):
        resultado = identificar_patrones(df, valor_adx=30.0)
    assert "COMPRA" in resultado
    assert "Estrella del Amanecer" in datos_graficos["patron"]


def test_estrella_del_atardecer():
    """Vela 1 Verde Grande, Vela 2 Cuerpo Pequeño, Vela 3 Roja Grande."""
    data = {
        'Open':  [106.8, 107.5, 106.3, 107.1, 108.3, 104.9, 101.4, 103.5, 100.2, 100.0, 109.0, 109.0],
        'High':  [108.2, 109.1, 108.0, 109.5, 109.0, 108.6, 104.8, 103.9, 102.1, 108.5, 110.0, 109.2],
        'Low':   [105.1, 106.0, 105.2, 106.4, 104.2, 101.1, 100.3, 99.4,  98.7,  99.5, 108.3, 101.8],
        'Close': [107.5, 106.3, 107.1, 108.3, 104.9, 101.4, 103.5, 100.2, 100.0, 108.0, 109.2, 102.5]
    }
    df = pd.DataFrame(data, index=pd.date_range("2026-01-01", periods=12, freq="1min"))
    
    with patch('config.historico_macd', [5, 2]):
        resultado = identificar_patrones(df, valor_adx=30.0)
    assert "VENTA" in resultado
    assert "Estrella del Atardecer" in datos_graficos["patron"]

# ===========================================================================
# 🧠 2. PATRONES TRADICIONALES DE 1 Y 2 VELAS (SEPARADOS)
# ===========================================================================
def test_envolvente_alcista():
    """Vela 2 Roja Pequeña, Vela 3 Verde Grande que cubre por completo a la previa."""
    data = {
        'Open':  [120.0, 118.5, 119.0, 116.5, 114.0, 113.8, 110.5, 111.0, 107.5, 106.0, 105.5, 101.5],
        'High':  [121.0, 119.5, 119.5, 117.0, 115.0, 114.5, 112.0, 111.5, 108.5, 106.5, 106.0, 108.0],
        'Low':   [118.0, 117.5, 116.0, 113.5, 113.0, 110.0, 109.5, 107.0, 105.0, 103.0, 101.8, 101.0],
        'Close': [118.5, 119.0, 116.5, 114.0, 113.8, 110.5, 111.0, 107.5, 106.0, 103.5, 102.0, 107.5]
    }
    df = pd.DataFrame(data, index=pd.date_range("2026-01-01", periods=12, freq="1min"))
    
    with patch('config.promedio_volumen', 2), patch('config.historico_macd', [-5, -2]):
        resultado = identificar_patrones(df, valor_adx=30.0)
    assert "COMPRA" in resultado
    assert "Envolvente Alcista" in datos_graficos["patron"]


def test_envolvente_bajista():
    """Vela 2 Verde Pequeña, Vela 3 Roja Grande que cubre por completo a la previa."""
    data = {
        'Open':  [100.0, 102.5, 102.0, 104.5, 107.0, 106.8, 109.5, 109.0, 112.5, 114.0, 114.5, 119.0],
        'High':  [103.0, 103.5, 105.0, 107.5, 108.0, 110.0, 110.5, 113.0, 114.5, 115.5, 118.0, 119.5],
        'Low':   [ 99.5, 101.5, 102.0, 104.0, 106.0, 106.5, 108.5, 109.0, 111.5, 113.5, 114.2, 111.0],
        'Close': [102.5, 102.0, 104.5, 107.0, 106.8, 109.5, 109.0, 112.5, 114.0, 115.0, 117.5, 111.5]
    }
    df = pd.DataFrame(data, index=pd.date_range("2026-01-01", periods=12, freq="1min"))
    
    with patch('config.promedio_volumen', 2), patch('config.historico_macd', [5, 4]):
        resultado = identificar_patrones(df, valor_adx=30.0)
    assert "VENTA" in resultado
    assert "Envolvente Bajista" in datos_graficos["patron"]


def test_martillo_alcista():
    """Vela 3 Verde con mecha inferior muy larga y mecha superior casi nula."""
    data = {
        'Open':  [120.0, 118.5, 119.0, 116.5, 114.0, 113.8, 110.5, 111.0, 107.5, 106.0, 104.0, 101.5],
        'High':  [121.0, 119.5, 119.5, 117.0, 115.0, 114.5, 112.0, 111.5, 108.5, 106.5, 104.5, 102.2],
        'Low':   [118.0, 117.5, 116.0, 113.5, 113.0, 110.0, 109.5, 107.0, 105.0, 103.0, 101.0,  96.0],
        'Close': [118.5, 119.0, 116.5, 114.0, 113.8, 110.5, 111.0, 107.5, 106.0, 104.0, 101.5, 102.1]
    }
    df = pd.DataFrame(data, index=pd.date_range("2026-01-01", periods=12, freq="1min"))

    with patch('config.promedio_volumen_sin_actual', 2), patch('config.historico_macd', [-5, -4]), patch('config.historico_volumen', [10]):
        resultado = identificar_patrones(df, valor_adx=30.0)
    assert "COMPRA" in resultado
    assert "Martillo (Hammer)" in datos_graficos["patron"]

def test_martillo_alcista_rojo():
    """Valida un Martillo Rojo con RSI en sobreventa y ADX fuerte (Señal de COMPRA completa)."""
    data = {
        'Open':  [120.0, 118.5, 119.0, 116.5, 114.0, 113.8, 110.5, 111.0, 107.5, 106.0, 104.0, 102.0],
        'High':  [121.0, 119.5, 119.5, 117.0, 115.0, 114.5, 112.0, 111.5, 108.5, 106.5, 104.5, 102.1],
        'Low':   [118.0, 117.5, 116.0, 113.5, 113.0, 110.0, 109.5, 107.0, 105.0, 103.0, 101.0,  96.0],
        'Close': [118.5, 119.0, 116.5, 114.0, 113.8, 110.5, 111.0, 107.5, 106.0, 104.0, 101.5, 101.5]
    }

    df = pd.DataFrame(data, index=pd.date_range("2026-01-01", periods=12, freq="1min"))

    with patch('config.promedio_volumen_sin_actual', 2), patch('config.historico_macd', [-5, -4]), patch('config.historico_volumen', [10]):
        resultado = identificar_patrones(df, valor_adx=32.0)    
    assert "COMPRA" in resultado
    assert "Martillo (Hammer)" in datos_graficos["patron"]

def test_martillo_invertido_alcista():
    """Vela 3 Verde con mecha superior muy larga y mecha inferior casi nula, precedida de tendencia bajista."""
    data = {
        'Open':  [120.0, 118.5, 119.0, 116.5, 114.0, 113.8, 110.5, 111.0, 107.5, 106.0, 104.0, 97.0],
        'High':  [121.0, 119.5, 119.5, 117.0, 115.0, 114.5, 112.0, 111.5, 108.5, 106.5, 104.5, 102.5],
        'Low':   [118.0, 117.5, 116.0, 113.5, 113.0, 110.0, 109.5, 107.0, 105.0, 103.0, 101.0,  96.9],
        'Close': [118.5, 119.0, 116.5, 114.0, 113.8, 110.5, 111.0, 107.5, 106.0, 104.0, 101.5,  97.5]
    }

    df = pd.DataFrame(data, index=pd.date_range("2026-01-01", periods=12, freq="1min"))

    with patch('config.promedio_volumen_sin_actual', 2), patch('config.historico_macd', [-5, -4]), patch('config.historico_volumen', [10]):
        resultado = identificar_patrones(df, valor_adx=30.0)
    
    assert "COMPRA" in resultado
    assert "Martillo Invertido" in datos_graficos["patron"]

def test_estrella_fugaz_bajista():
    """Vela 3 Roja tipo Estrella Fugaz. Vela 2 muy grande para evitar Estrella del Atardecer y Envolvente."""
    data = {
        'Open':  [100.0, 102.5, 102.0, 104.5, 107.0, 106.8, 109.5, 109.0, 112.5, 114.0, 114.5, 118.0],
        'High':  [103.0, 103.5, 105.0, 107.5, 108.0, 110.0, 110.5, 113.0, 114.5, 115.5, 117.5, 123.5],
        'Low':   [ 99.5, 101.5, 102.0, 104.0, 106.0, 106.5, 108.5, 109.0, 111.5, 113.5, 114.2, 117.4],
        'Close': [102.5, 102.0, 104.5, 107.0, 106.8, 109.5, 109.0, 112.5, 114.0, 115.0, 117.5, 117.5]
    }
    df = pd.DataFrame(data, index=pd.date_range("2026-01-01", periods=12, freq="1min"))

    with patch('config.promedio_volumen_sin_actual', 2), patch('config.historico_macd', [5, 4]), patch('config.historico_volumen', [10]):
        resultado = identificar_patrones(df, valor_adx=30.0)
    
    assert "VENTA" in resultado
    assert "Estrella Fugaz" in datos_graficos["patron"]

def test_hombre_colgado_bajista():
    """Vela 3 Roja tipo Estrella Fugaz invertida"""
    data = {
        'Open':  [100.0, 102.5, 102.0, 104.5, 107.0, 106.8, 109.5, 109.0, 112.5, 114.0, 114.5, 117.5],
        'High':  [103.0, 103.5, 105.0, 107.5, 108.0, 110.0, 110.5, 113.0, 114.5, 115.5, 117.5, 117.6],
        'Low':   [ 99.5, 101.5, 102.0, 104.0, 106.0, 106.5, 108.5, 109.0, 111.5, 113.5, 114.2, 112.0],
        'Close': [102.5, 102.0, 104.5, 107.0, 106.8, 109.5, 109.0, 112.5, 114.0, 115.0, 117.5, 117.0]
    }

    df = pd.DataFrame(data, index=pd.date_range("2026-01-01", periods=12, freq="1min"))

    with patch('config.promedio_volumen_sin_actual', 2), patch('config.historico_macd', [5, 4]), patch('config.historico_volumen', [10]):
        resultado = identificar_patrones(df, valor_adx=30.0)
    
    assert "VENTA" in resultado
    assert "Hombre Colgado" in datos_graficos["patron"]

# ===========================================================================
# 🧠 3. ESTRUCTURAS COMPLEJAS (12 VELAS)
# ===========================================================================

def test_doble_techo():
    """Genera dos picos idénticos de precio en los últimos 12 periodos."""
    data = {
        'Open': [
            100.0, 102.5, 101.8, 104.0, 106.5, 105.0, 108.5, 111.0, 110.2, 113.5,
            115.0, 118.5, 117.0, 121.5, 125.0, 123.8, 128.0, 131.5, 130.0, 133.5,
            135.0, 138.5, 139.0, 134.5, 131.0, 128.5, 126.0, 125.5, 124.5, 124.0,
            126.5, 129.0, 132.5, 135.0, 134.2, 137.5, 138.0, 139.2, 138.5, 134.0,
            131.5, 129.0, 128.5, 127.0, 125.5, 126.0, 125.0, 124.5, 123.5, 124.5
        ],
        'High': [
            103.5, 104.0, 104.5, 107.0, 107.5, 109.0, 112.0, 112.5, 114.5, 116.0,
            119.5, 120.0, 122.5, 126.0, 126.5, 129.0, 132.5, 133.0, 135.0, 136.5,
            139.5, 140.0, 140.0, 137.0, 133.5, 130.0, 128.0, 127.5, 126.0, 126.5,
            129.5, 133.0, 136.0, 136.5, 138.5, 139.5, 140.0, 139.8, 139.0, 135.5,
            132.5, 130.5, 129.5, 128.5, 127.5, 127.0, 126.5, 125.5, 125.0, 125.0
        ],
        'Low': [
            99.5,  101.0, 100.5, 103.0, 104.0, 104.5, 107.5, 110.0, 109.5, 112.5,
            114.0, 116.5, 116.0, 120.5, 123.5, 122.0, 126.5, 130.0, 129.0, 132.5,
            134.0, 137.5, 133.5, 130.0, 127.5, 125.0, 124.5, 123.5, 123.8, 123.0,
            125.5, 128.0, 131.5, 133.5, 133.0, 136.0, 137.0, 137.5, 133.5, 130.5,
            128.0, 127.5, 126.5, 125.0, 124.5, 124.0, 123.5, 122.5, 121.5, 120.5
        ],
        'Close': [
            102.5, 101.8, 104.0, 106.5, 105.0, 108.5, 111.0, 110.2, 113.5, 115.0,
            118.5, 117.0, 121.5, 125.0, 123.8, 128.0, 131.5, 130.0, 133.5, 135.0,
            138.5, 139.0, 134.5, 131.0, 128.5, 126.0, 125.5, 124.5, 124.0, 126.5,
            129.0, 132.5, 135.0, 134.2, 137.5, 138.0, 139.2, 138.5, 134.0, 131.5,
            129.0, 128.5, 127.0, 125.5, 126.0, 125.0, 124.5, 123.5, 124.5, 121.0
        ]
    }

    df = pd.DataFrame(data, index=pd.date_range("2026-01-01", periods=50, freq="1min"))
    
    with patch('config.promedio_volumen', 2), patch('config.promedio_volumen_sin_actual', 2), patch('config.historico_macd', [5, 4]), patch('config.historico_volumen', [10]):
        resultado = identificar_patrones(df, valor_adx=35.0)
    assert "VENTA" in resultado
    assert "Doble Techo" in datos_graficos["patron"]

def test_doble_suelo():
    """Genera dos valles idénticos de precio en los últimos 12 periodos."""
    data = {
        'Open': [
            140.0, 137.5, 138.2, 136.0, 133.5, 135.0, 131.5, 129.0, 129.8, 126.5,
            125.0, 121.5, 123.0, 118.5, 115.0, 116.2, 112.0, 108.5, 110.0, 106.5,
            105.0, 101.5, 101.0, 105.5, 109.0, 111.5, 114.0, 114.5, 115.5, 116.0,
            113.5, 111.0, 107.5, 105.0, 105.8, 102.5, 102.0, 100.8, 101.5, 106.0,
            108.5, 111.0, 111.5, 113.0, 114.5, 114.0, 115.0, 115.5, 116.5, 115.5
        ],
        'High': [
            140.5, 139.0, 139.5, 137.0, 136.0, 135.5, 132.5, 130.0, 130.5, 127.5,
            126.0, 123.5, 124.0, 119.5, 116.0, 118.0, 113.5, 110.0, 111.0, 107.5,
            106.0, 103.5, 101.5, 107.0, 110.0, 113.0, 115.0, 115.5, 116.5, 116.5,
            114.0, 112.0, 108.5, 106.5, 107.0, 104.0, 103.0, 102.5, 106.5, 109.5,
            111.5, 112.5, 113.5, 115.0, 115.5, 116.0, 116.5, 117.5, 118.5, 119.5
        ],
        'Low': [
            136.5, 136.0, 135.5, 133.0, 132.5, 131.0, 128.0, 127.5, 125.5, 124.0,
            120.5, 120.0, 117.5, 114.0, 113.5, 111.0, 107.5, 107.0, 105.0, 103.5,
            100.5, 100.0, 100.0, 103.0, 106.5, 110.0, 112.0, 112.5, 114.0, 113.5,
            110.5, 107.0, 104.0, 103.5, 101.5, 100.5, 100.5, 100.2, 101.0, 104.5,
            107.5, 109.5, 110.5, 111.5, 112.5, 113.0, 113.5, 114.5, 115.0, 115.0
        ],
        'Close': [
            137.5, 138.2, 136.0, 133.5, 135.0, 131.5, 129.0, 129.8, 126.5, 125.0,
            121.5, 123.0, 118.5, 115.0, 116.2, 112.0, 108.5, 110.0, 106.5, 105.0,
            101.5, 101.0, 105.5, 109.0, 111.5, 114.0, 114.5, 115.5, 116.0, 113.5,
            111.0, 107.5, 105.0, 105.8, 102.5, 102.0, 100.8, 101.5, 106.0, 108.5,
            111.0, 111.5, 113.0, 114.5, 114.0, 115.0, 115.5, 116.5, 115.5, 119.0
        ]
    }

    df = pd.DataFrame(data, index=pd.date_range("2026-01-01", periods=50, freq="1min"))
    
    with patch('config.promedio_volumen', 2), patch('config.promedio_volumen_sin_actual', 2), patch('config.historico_macd', [-5, -4]), patch('config.historico_volumen', [10]):
        resultado = identificar_patrones(df, valor_adx=35.0)
    assert "COMPRA" in resultado
    assert "Doble Suelo" in datos_graficos["patron"]

def test_hombro_cabeza_hombro():
    """Genera un patrón HCH: Pico izquierdo, Cabeza alta, Pico derecho similar al izquierdo."""
    data = {
        'Open': [
            100.0, 102.5, 101.8, 105.0, 107.5, 106.2, 110.0, 113.5, 112.0, 116.5,
            118.0, 121.5, 120.0, 124.5, 128.0, 126.8, 131.0, 134.5, 133.0, 137.5,
            140.0, 143.5, 142.0, 145.5, 148.0, 149.5, 148.5, 144.0, 141.5, 138.0,
            136.5, 135.5, 137.0, 141.5, 145.0, 149.5, 153.0, 157.5, 161.0, 160.5,
            155.0, 151.5, 147.0, 142.5, 138.0, 137.5, 139.0, 142.5, 145.0, 148.5,
            149.0, 147.5, 144.0, 141.5, 139.0, 137.5, 136.0, 135.5, 134.0, 134.5
        ],
        'High': [
            103.5, 104.0, 105.5, 108.0, 108.5, 111.0, 114.0, 114.5, 117.5, 119.0,
            122.5, 123.0, 125.5, 129.0, 129.5, 132.0, 135.5, 136.0, 138.5, 141.0,
            144.5, 145.0, 147.5, 150.0, 150.0, 150.5, 149.5, 146.0, 143.0, 139.5,
            138.0, 137.0, 142.5, 146.0, 150.5, 154.0, 158.5, 162.0, 162.0, 161.5,
            157.0, 153.0, 149.5, 144.0, 139.5, 139.0, 143.5, 146.5, 150.0, 150.5,
            150.5, 148.5, 145.5, 142.5, 140.0, 138.5, 137.0, 136.0, 135.0, 135.0
        ],
        'Low': [
            99.5,  101.0, 100.5, 103.5, 105.0, 105.5, 108.5, 111.0, 110.5, 114.5,
            116.0, 119.5, 118.5, 122.5, 125.5, 124.0, 129.5, 132.0, 131.0, 135.5,
            138.0, 141.5, 140.0, 143.5, 146.5, 147.0, 143.5, 140.5, 137.0, 135.5,
            135.0, 134.5, 135.5, 140.0, 143.5, 148.0, 151.5, 156.0, 159.5, 154.0,
            151.5, 146.0, 141.5, 137.0, 136.0, 135.5, 137.5, 141.0, 143.5, 147.0,
            146.5, 143.5, 140.5, 138.0, 136.5, 135.0, 134.0, 133.0, 131.5, 129.5
        ],
        'Close': [
            102.5, 101.8, 105.0, 107.5, 106.2, 110.0, 113.5, 112.0, 116.5, 118.0,
            121.5, 120.0, 124.5, 128.0, 126.8, 131.0, 134.5, 133.0, 137.5, 140.0,
            143.5, 142.0, 145.5, 148.0, 149.5, 148.5, 144.0, 141.5, 138.0, 136.5,
            135.5, 137.0, 141.5, 145.0, 149.5, 153.0, 157.5, 161.0, 160.5, 155.0,
            151.5, 147.0, 142.5, 138.0, 137.5, 139.0, 142.5, 145.0, 148.5, 149.0,
            147.5, 144.0, 141.5, 139.0, 137.5, 136.0, 135.5, 134.0, 134.5, 130.0
        ]
    }

    df = pd.DataFrame(data, index=pd.date_range("2026-01-01", periods=60, freq="1min"))
    with patch('config.promedio_volumen', 2), patch('config.promedio_volumen_sin_actual', 2), patch('config.historico_macd', [5, 4]), patch('config.historico_volumen', [10]):
        resultado = identificar_patrones(df, valor_adx=40.0)
    assert "VENTA" in resultado
    assert "Hombro Cabeza Hombro" in datos_graficos["patron"]

def test_hombro_cabeza_hombro_invertido():
    """Genera un patrón HCH Invertido en los soportes mínimos."""
    data = {
        'Open': [
            160.0, 157.0, 158.5, 155.0, 151.5, 153.0, 149.0, 145.5, 146.5, 142.5,
            139.0, 140.5, 136.5, 133.0, 134.0, 129.5, 126.0, 127.2, 123.0, 119.5,
            120.5, 117.0, 113.5, 114.5, 110.5, 113.5, 117.5, 121.0, 123.0, 125.0,
            122.5, 118.5, 114.0, 109.5, 105.0, 101.5, 103.5, 108.0, 112.5, 117.0,
            121.5, 124.5, 122.0, 118.5, 114.5, 111.0, 113.5, 117.5, 121.0, 123.5,
            125.0, 126.5, 128.0, 129.5, 131.0, 132.5, 134.0, 135.5, 137.0, 134.5
        ],
        'High': [
            161.0, 158.5, 159.5, 156.5, 153.0, 154.5, 150.5, 147.5, 148.0, 144.5,
            141.0, 142.0, 138.0, 134.5, 135.5, 131.0, 127.5, 128.5, 124.5, 121.0,
            122.0, 118.5, 115.0, 116.0, 112.5, 115.5, 119.0, 122.5, 125.0, 125.5,
            124.0, 120.0, 115.5, 111.0, 106.5, 103.0, 105.0, 109.5, 114.0, 118.5,
            122.5, 125.0, 123.5, 120.0, 116.0, 112.5, 115.5, 119.0, 122.5, 124.5,
            126.5, 128.0, 129.5, 131.0, 132.5, 134.0, 135.5, 137.0, 138.5, 139.5
        ],
        'Low': [
            156.5, 155.5, 154.0, 151.0, 149.5, 148.0, 144.5, 142.0, 141.5, 138.5,
            135.5, 136.0, 132.0, 129.5, 130.0, 125.5, 122.5, 123.0, 119.0, 115.5,
            116.5, 113.0, 109.5, 110.5, 107.0, 110.0, 113.5, 117.0, 120.5, 122.0,
            118.0, 113.5, 109.0, 104.5, 101.0, 100.0, 101.5, 103.0, 107.5, 111.5,
            116.0, 120.5, 118.0, 114.0, 110.5, 109.0, 111.0, 114.5, 118.0, 121.5,
            123.0, 124.5, 126.0, 127.5, 129.0, 130.5, 132.0, 133.5, 135.0, 133.0
        ],
        'Close': [
            157.0, 158.5, 155.0, 151.5, 153.0, 149.0, 145.5, 146.5, 142.5, 139.0,
            140.5, 136.5, 133.0, 134.0, 129.5, 126.0, 127.2, 123.0, 119.5, 120.5,
            117.0, 113.5, 114.5, 110.5, 112.0, 115.5, 119.0, 122.5, 124.5, 123.0,
            118.5, 114.0, 109.5, 105.0, 101.5, 103.5, 108.0, 112.5, 117.0, 121.5,
            124.5, 123.0, 118.5, 114.5, 111.0, 113.5, 117.5, 121.0, 123.5, 125.0,
            126.5, 128.0, 129.5, 131.0, 132.5, 134.0, 135.5, 137.0, 134.5, 138.0
        ]
    }

    df = pd.DataFrame(data, index=pd.date_range("2026-01-01", periods=60, freq="1min"))
    with patch('config.promedio_volumen', 2), patch('config.promedio_volumen_sin_actual', 2), patch('config.historico_macd', [-5, -4]), patch('config.historico_volumen', [10]):
        resultado = identificar_patrones(df, valor_adx=40.0)
    assert "COMPRA" in resultado
    assert "Hombro Cabeza Hombro Invertido" in datos_graficos["patron"]

# ===========================================================================
# 🧠 4. PATRONES COMPUESTOS DE 1 VELA
# ===========================================================================

def test_marubozu_alcista_con_macd_positivo():
    """Valida que un Marubozu Alcista con MACD > 0 devuelva tendencia alcista."""
    
    data = {
        'Open':  [135.0, 132.0, 133.0, 128.0, 125.0, 121.0, 118.0, 115.0, 116.0, 110.0, 102.0, 100.0],
        'High':  [136.0, 134.0, 134.0, 129.0, 126.0, 122.0, 119.0, 117.0, 117.0, 111.0, 103.0, 106.0],
        'Low':   [131.0, 129.0, 127.0, 124.0, 120.0, 117.0, 113.0, 111.0, 109.0, 101.0,  99.0, 100.0],
        'Close': [132.0, 133.0, 128.0, 125.0, 121.0, 118.0, 115.0, 112.0, 110.0, 102.0, 101.0, 106.0]
    }
    df = pd.DataFrame(data, index=pd.date_range("2026-01-01", periods=12, freq="1min"))
    
   
    with patch('config.valor_macd', 0.85):
        resultado = identificar_patrones(df, valor_adx=40.0)
    
    assert "COMPRA" in resultado
    assert "Marubozu Alcista" in datos_graficos["patron"]
