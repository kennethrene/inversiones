import config
from selenium.webdriver.common.by import By
from ui.interfaz import ui_adx, ui_macd, ui_rsi, ui_ema, ui_volumen, ui_bollinger

texto_macd = ""
texto_rsi = ""
texto_adx = ""
texto_volumen = ""
texto_ema = ""
texto_bollinger = ""

def precargar_datos():
    if (config.cargar_datos):
        config.historico_macd = config.preload_historico_macd
        config.historico_rsi = config.preload_historico_rsi
        config.historico_volumen = config.preload_historico_volumen
        config.promedio_volumen_sin_actual = config.preload_promedio_volumen_sin_actual
        config.promedio_volumen = config.preload_promedio_volumen
        config.valor_compra_abrio = config.preload_valor_compra_abrio
        config.valor_venta_abrio = config.preload_valor_venta_abrio
        config.cargar_datos = False

def obtener_texto_indicadores(elementos_indicadores):
    for elemento in elementos_indicadores:
        try:
            if elemento.is_displayed():
                contenedor_padre = elemento.find_element(By.XPATH, "./..")
                parent_text_content = contenedor_padre.get_attribute("textContent").upper()
                child_text_content = elemento.get_attribute("title") or elemento.get_attribute("textContent")
                if not child_text_content: continue
                texto_componente = child_text_content.replace(",", ".")
                
                texto_macd = ui_macd(parent_text_content, texto_componente, config.historico_macd, texto_macd)
                texto_rsi = ui_rsi(parent_text_content, texto_componente, config.historico_rsi, texto_rsi)
                texto_adx = ui_adx(parent_text_content, texto_componente, texto_adx)
                texto_volumen = ui_volumen(parent_text_content, texto_componente, texto_volumen)
                texto_ema = ui_ema(parent_text_content, texto_componente, texto_ema)
                texto_bollinger = ui_bollinger(parent_text_content, texto_componente, texto_bollinger)

                return (
                    f"{texto_macd}\n"
                    f"{texto_rsi}\n"
                    f"{texto_adx}\n"
                    f"{texto_volumen}\n"
                    f"{texto_ema}\n"
                    f"{texto_bollinger}"
                )
        except: continue
    
    return ""

def actualizar_informacion():
    config.valor_compra_abrio = config.valor_compra
    config.valor_venta_abrio = config.valor_venta

    # Adicionar el valor de los indicadores
    try:
        valor_numerico = float(config.valor_macd)
        config.historico_macd.append(valor_numerico)
    except (ValueError, TypeError):
        config.error = f"⚠️ No se pudo guardar: el valor del MACD no es numérico: {config.valor_macd}"

    if len(config.historico_macd) > 3:
        config.historico_macd.pop(0)

    try:
        valor_numerico = float(config.valor_rsi)
        config.historico_rsi.append(valor_numerico)
    except (ValueError, TypeError):
        config.error = f"⚠️ No se pudo guardar: el valor del RSI no es numérico: {config.valor_rsi}"

    if len(config.historico_rsi) > 3:
        config.historico_rsi.pop(0)

    try:
        config.historico_volumen.append(config.ultimo_valor_volumen)
        config.penultimo_segundo_procesado = 0
        config.ultimo_valor_volumen = 0
        if len(config.historico_volumen) > 6:
            config.historico_volumen.pop(0)
            config.promedio_volumen = sum(config.historico_volumen) / 6
            config.promedio_volumen_sin_actual = sum(config.historico_volumen[-6:-1]) / 5
        elif len(config.historico_volumen) > 0:
            config.promedio_volumen = sum(config.historico_volumen) / len(config.historico_volumen)
            config.promedio_volumen_sin_actual = sum(config.historico_volumen[:-1]) / len(config.historico_volumen[:-1]) if len(config.historico_volumen) > 1 else 0
    except (ValueError, TypeError):
        config.error = f"⚠️ No se pudo guardar: el valor del Volumen no es numérico: {config.ultimo_valor_volumen}"