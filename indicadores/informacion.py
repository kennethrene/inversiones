import configuracion.parametros as parametros
from selenium.webdriver.common.by import By
import traceback
import time
from ui.interfaz import ui_adx, ui_macd, ui_rsi, ui_ema, ui_volumen, ui_bollinger

texto_macd = ""
texto_rsi = ""
texto_adx = ""
texto_volumen = ""
texto_ema = ""
texto_bollinger = ""

def precargar_datos():
    global texto_adx, texto_ema, texto_rsi, texto_bollinger, texto_volumen, texto_macd

    if parametros.CARGAR_DATOS:
        parametros.historico_macd = parametros.PRELOAD_HISTORICO_MACD
        parametros.historico_rsi = parametros.PRELOAD_HISTORICO_RSI
        parametros.historico_volumen = parametros.PRELOAD_HISTORICO_VOLUMEN
        parametros.promedio_volumen_sin_actual = parametros.PRELOAD_PROMEDIO_VOLUMEN_SIN_ACTUAL
        parametros.promedio_volumen = parametros.PRELOAD_PROMEDIO_VOLUMEN
        parametros.valor_compra_abrio = parametros.PRELOAD_VALOR_COMPRA_ABRIO
        parametros.valor_venta_abrio = parametros.PRELOAD_VALOR_VENTA_ABRIO
    
    if parametros.CARGAR_DATOS_OPERACION:
        parametros.activo_actual = parametros.PRELOAD_ACTIVO_ACTUAL
        parametros.datos_mapeados['Operacion'] = parametros.PRELOAD_OPERACION
        parametros.datos_mapeados['Precio Apertura'] = parametros.PRELOAD_PRECIO_APERTURA
        parametros.TAKE_PROFIT = parametros.PRELOAD_TAKE_PROFIT
        parametros.STOP_LOSS = parametros.PRELOAD_STOP_LOSS
        parametros.TRAILING_STOP = parametros.PRELOAD_TRAILING_STOP
        parametros.diferencia_precio = parametros.PRELOAD_DIFERENCIA_PRECIO
        parametros.datos_mapeados["Patron"] = parametros.PRELOAD_PATRON
        parametros.datos_mapeados['Beneficio Neto'] = parametros.PRELOAD_BENEFICIO_NETO
        parametros.CARGAR_DATOS = False

def obtener_texto_indicadores(elementos_indicadores):
    global texto_adx, texto_ema, texto_rsi, texto_bollinger, texto_volumen, texto_macd

    for elemento in elementos_indicadores:
        try:
            if elemento.is_displayed():
                contenedor_padre = elemento.find_element(By.XPATH, "./..")
                parent_text_content = contenedor_padre.get_attribute("textContent").upper()
                child_text_content = elemento.get_attribute("title") or elemento.get_attribute("textContent")
                if not child_text_content: continue
                texto_componente = child_text_content.replace(",", ".")
                
                texto_macd = ui_macd(parent_text_content, texto_componente, parametros.historico_macd, texto_macd)
                texto_rsi = ui_rsi(parent_text_content, texto_componente, parametros.historico_rsi, texto_rsi)
                texto_adx = ui_adx(parent_text_content, texto_componente, texto_adx)
                texto_volumen = ui_volumen(parent_text_content, texto_componente, texto_volumen)
                texto_ema = ui_ema(parent_text_content, texto_componente, texto_ema)
                texto_bollinger = ui_bollinger(parent_text_content, texto_componente, texto_bollinger)
        except Exception as e_bucle:
                    parametros.error = traceback.format_exc()
                    time.sleep(0.1)
    
    if len(texto_macd) > 0:
        texto_macd += '\n'
    if len(texto_rsi) > 0:
        texto_rsi += '\n'
    if len(texto_volumen) > 0:
        texto_volumen += '\n'
    if len(texto_ema) > 0:
        texto_ema += '\n'

    return (
        f"{texto_macd}"
        f"{texto_rsi}"
        f"{texto_adx}"
        f"{texto_volumen}"
        f"{texto_ema}"
        f"{texto_bollinger}"
    )

def actualizar_informacion():
    parametros.valor_compra_abrio = parametros.valor_compra
    parametros.valor_venta_abrio = parametros.valor_venta

    # Adicionar el valor de los indicadores
    try:
        valor_numerico = float(parametros.valor_macd)
        parametros.historico_macd.append(valor_numerico)
    except (ValueError, TypeError):
        parametros.error = f"⚠️ No se pudo guardar: el valor del MACD no es numérico: {parametros.valor_macd}"

    if len(parametros.historico_macd) > 3:
        parametros.historico_macd.pop(0)

    try:
        valor_numerico = float(parametros.valor_rsi)
        parametros.historico_rsi.append(valor_numerico)
    except (ValueError, TypeError):
        parametros.error = f"⚠️ No se pudo guardar: el valor del RSI no es numérico: {parametros.valor_rsi}"

    if len(parametros.historico_rsi) > 3:
        parametros.historico_rsi.pop(0)

    try:
        parametros.historico_volumen.append(parametros.ultimo_valor_volumen)
        parametros.penultimo_segundo_procesado = 0
        parametros.ultimo_valor_volumen = 0
        if len(parametros.historico_volumen) > 6:
            parametros.historico_volumen.pop(0)
            parametros.promedio_volumen = sum(parametros.historico_volumen) / 6
            parametros.promedio_volumen_sin_actual = sum(parametros.historico_volumen[-6:-1]) / 5
        elif len(parametros.historico_volumen) > 0:
            parametros.promedio_volumen = sum(parametros.historico_volumen) / len(parametros.historico_volumen)
            parametros.promedio_volumen_sin_actual = sum(parametros.historico_volumen[:-1]) / len(parametros.historico_volumen[:-1]) if len(parametros.historico_volumen) > 1 else 0
    except (ValueError, TypeError):
        parametros.error = f"⚠️ No se pudo guardar: el valor del Volumen no es numérico: {parametros.ultimo_valor_volumen}"