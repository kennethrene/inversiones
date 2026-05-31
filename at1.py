from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import traceback
import time
import os
import re
import config
from indicadores.operaciones import ejecutar_operacion
from ui.interfaz import ui_adx, ui_macd, ui_rsi, ui_ema, ui_trailing, ui_stop_loss, ui_operacion_activa, ui_estadisticas, ui_volumen, ui_general, ui_bollinger
from files.tracking import guardar_estadistica, actualizar_ultima_operacion, actualizar_estadisticas_cierre
from extraction.xtb_data import extraer_datos_operacion, obtener_datos_operaciones, obtener_datos_compra_venta
from indicadores.cierre import ejecutar_cierre

# 📊 HISTORIAL GLOBAL PARA CONSTRUIR EL GRÁFICO ASCII NATIVO
historial_precios_recientes = []

hora_apertura_orden = None
operacion_ganada = None
maximo_rendimiento_alcanzado = 0.0  
bloqueo_ejecutar_orden = False
minuto_anterior = ""
minuto_ultima_orden = ""
motivo_cierre = "N/D"
driver = None
comando_limpiar = None

def inicializar():
    global bloqueo_ejecutar_orden, minuto_anterior, minuto_ultima_orden, motivo_cierre, driver, comando_limpiar

    opciones = Options()
    opciones.add_argument("--headless=new")
    opciones.add_argument("--window-size=1920,1080")
    opciones.add_argument("--disable-gpu")
    opciones.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

    print("Intentando enlazar con Chrome en el puerto 9222...")
    driver = webdriver.Chrome(options=opciones)

    driver.set_page_load_timeout(3)
    driver.implicitly_wait(0.1)

    comando_limpiar = 'cls' if os.name == 'nt' else 'clear'

    bloqueo_ejecutar_orden = False
    minuto_anterior = ""
    minuto_ultima_orden = ""
    motivo_cierre = "N/D"

    os.system(comando_limpiar)
    print("=" * 75)
    print("¡Conectado con éxito a xStation!")
    print("=" * 75)
    time.sleep(1)

def bot_scalping():
    global estadisticas_bot, hora_apertura_orden, operacion_ganada
    global maximo_rendimiento_alcanzado, trailing_activado, tiempo_ultimo_cierre
    global bloqueo_ejecutar_orden, minuto_anterior, minuto_ultima_orden, motivo_cierre, driver, comando_limpiar
    
    try:
        inicializar()

        while True:
            try:
                if minuto_ultima_orden != time.strftime('%M'):
                    bloqueo_ejecutar_orden = False
                
                minuto_actual = time.strftime('%M')                
                if minuto_anterior == "": minuto_anterior = minuto_actual

                segundo_actual = time.strftime('%H:%M:%S')
                obtener_datos_compra_venta(segundo_actual, False, driver)

                if (config.cargar_datos):
                    config.historico_macd = config.preload_historico_macd
                    config.historico_rsi = config.preload_historico_rsi
                    config.historico_volumen = config.preload_historico_volumen
                    config.promedio_volumen_sin_actual = config.preload_promedio_volumen_sin_actual
                    config.promedio_volumen = config.preload_promedio_volumen
                    config.valor_compra_abrio = config.preload_valor_compra_abrio
                    config.valor_venta_abrio = config.preload_valor_venta_abrio
                    config.cargar_datos = False

                if segundo_actual != config.ultimo_segundo_procesado:
                    config.ultimo_segundo_procesado = segundo_actual

                segundo_hace_dos_segs = time.time() - 2
                if segundo_hace_dos_segs >= config.penultimo_segundo_procesado:
                    config.ultimo_valor_volumen = config.valor_volumen
                    config.penultimo_segundo_procesado = segundo_hace_dos_segs

                texto_macd = ""
                texto_rsi = ""
                texto_adx = ""
                texto_volumen = ""
                texto_ema = ""
                texto_bollinger = ""
                texto_indicadores = ""

                # Escaneo de los indicadores técnicos
                xpath_indicadores = "//*[contains(@class, 'indicator-value-label')]"
                elementos_indicadores = driver.find_elements(By.XPATH, xpath_indicadores)

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
                            texto_separador = "-" * 75

                            texto_indicadores = (
                                f"{texto_macd}\n"
                                f"{texto_rsi}\n"
                                f"{texto_adx}\n"
                                f"{texto_volumen}\n"
                                f"{texto_ema}\n"
                                f"{texto_bollinger}"
                            )
                    except: continue

                if minuto_ultima_orden != time.strftime('%M'):
                    bloqueo_ejecutar_orden = False

                js_script_shadow = obtener_datos_operaciones()
                
                resultado_shadow = driver.execute_script(js_script_shadow)
                total_posiciones = resultado_shadow["total"]
                operaciones_detalles = resultado_shadow["detalles"]
                
                operacion_activa = total_posiciones > 0
                ejecutar_cierre_operacion = False
                beneficio_neto = None
                
                texto_trailing = ui_trailing(False, False, None, None)
                texto_stop_loss = ui_stop_loss(False, None)

                if operacion_activa and len(operaciones_detalles) > 0:
                    if hora_apertura_orden is None:
                        hora_apertura_orden = time.time()
                        maximo_rendimiento_alcanzado = -999.0  
                    
                    # Llamamos a la extracción con la matriz limpia
                    extraer_datos_operacion(operaciones_detalles)
                    
                    try:
                        texto_porcentaje = str(config.datos_mapeados["Beneficio %"]).replace("%", "").replace(" ", "").replace(",", ".")
                        match_pct = re.search(r'([-+]?\d+\.\d+|-?\d+)', texto_porcentaje)
                        rendimiento_actual = float(match_pct.group(1)) if match_pct else 0.0
                    except:
                        rendimiento_actual = 0.0
                    
                    texto_stop_loss = ui_stop_loss(True, rendimiento_actual)                    
                   
                    # ─── PARAMETROS DE TRAILING STOP ───
                    if rendimiento_actual > maximo_rendimiento_alcanzado:
                        maximo_rendimiento_alcanzado = rendimiento_actual
                        
                    if not config.USAR_IA and maximo_rendimiento_alcanzado >= config.TRAILING_STOP:
                        config.trailing_activado = True
                    elif config.USAR_IA:
                        if config.datos_mapeados['Operacion'] == "Compra" and float(config.valor_compra) >= float(config.TRAILING_STOP):
                            config.trailing_activado = True
                        if config.datos_mapeados['Operacion'] == "Venta" and float(config.valor_venta) <= float(config.TRAILING_STOP):
                            config.trailing_activado = True

                        
                    if not config.USAR_IA:
                        if config.trailing_activado:
                            caida_desde_pico = maximo_rendimiento_alcanzado - rendimiento_actual
                            texto_trailing = ui_trailing(True, True, maximo_rendimiento_alcanzado, caida_desde_pico)
                        else:
                            texto_trailing = ui_trailing(True, False, rendimiento_actual, None)
                    elif config.USAR_IA:
                        if config.trailing_activado:
                            if config.datos_mapeados['Operacion'] == "Compra" and float(config.valor_compra) > float(config.TRAILING_STOP):
                                config.STOP_LOSS = float(config.valor_compra) - float(config.DISTANCIA_TRAILING_MAXIMA)
                            if config.datos_mapeados['Operacion'] == "Venta" and float(config.valor_venta) < float(config.TRAILING_STOP):
                                config.STOP_LOSS = float(config.valor_venta) + float(config.DISTANCIA_TRAILING_MAXIMA)

                    texto_operacion_activa = ui_operacion_activa(True, rendimiento_actual)
                    beneficio_neto =  float(config.datos_mapeados['Beneficio Neto'])

                    ejecutar_cierre_operacion, operacion_ganada, motivo_cierre = ejecutar_cierre(maximo_rendimiento_alcanzado, rendimiento_actual)
                else:
                    texto_operacion_activa = ui_operacion_activa(False, None)
                    hora_apertura_orden = None

                if int(minuto_actual) % config.TEMPORALIDAD_MINUTOS == 0 and minuto_actual != minuto_anterior:
                    if time.time() - config.TIEMPO_ULTIMO_CIERRE < config.SEGUNDOS_ENFRIAMIENTO:
                        continue
                    
                    minuto_anterior = minuto_actual
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

                # Ejecución automática de operaciones bajo confluencia estricta
                if not bloqueo_ejecutar_orden and not operacion_activa:
                    # 🔥 CONTROL DE ENFRIAMIENTO TRAS CIERRE
                    if time.time() - config.TIEMPO_ULTIMO_CIERRE < config.SEGUNDOS_ENFRIAMIENTO:
                        continue # Salta la iteración si no ha pasado el tiempo mínimo

                    operacion = ejecutar_operacion()
    
                    if config.boton_comprar and operacion == "Comprar":                            
                            config.boton_comprar.click()
                            #os.system('say "Comprando" &')
                            bloqueo_ejecutar_orden = True
                            minuto_ultima_orden = time.strftime('%M')
                            hora_apertura_orden = time.time()                            
                            config.datos_mapeados['Operacion'] = "Compra"
                            guardar_estadistica("Compra")
                    elif config.boton_vender and operacion == "Vender":                            
                            config.boton_vender.click()
                            #os.system('say "Vendiendo" &')
                            bloqueo_ejecutar_orden = True
                            minuto_ultima_orden = time.strftime('%M')
                            hora_apertura_orden = time.time()                            
                            config.datos_mapeados['Operacion'] = "Venta"
                            guardar_estadistica("Venta")

                # ===========================================================================
                # MODULO DE GATILLADO Y ACCIÓN DE CIERRE DIRECTO
                # ===========================================================================
                if ejecutar_cierre_operacion and operacion_activa:
                    try:
                        driver.execute_script("if(window.ultimoBotonCierre) { window.ultimoBotonCierre.click(); }")
                        #os.system(f'say "Posición cerrada por {motivo_cierre_stats}" &')
                        config.historico_cuenta.append(beneficio_neto)

                        # 🔥 REGISTRAR EL TIEMPO EXACTO DEL CIERRE
                        config.TIEMPO_ULTIMO_CIERRE = time.time()

                        hora_apertura_orden = None
                        trailing_activado = False
                        maximo_rendimiento_alcanzado = 0.0
                        operacion_ganada = None
                        config.TRAILING_STOP = 15.0
                        config.DISTANCIA_TRAILING_MAXIMA = 4.0
                        config.TAKE_PROFIT = 5.0
                        config.STOP_LOSS  = -10.0
                        config.trailing_activado = False

                        # Sincronizador de estadísticas con lectura de resultados reales
                        if beneficio_neto > 0:
                            actualizar_ultima_operacion(config.datos_mapeados, "Ganada", motivo_cierre)
                            actualizar_estadisticas_cierre(True)
                        else:
                            actualizar_ultima_operacion(config.datos_mapeados, "Perdida", motivo_cierre)
                            actualizar_estadisticas_cierre(False)

                        time.sleep(5)
                    except Exception as error_ejecucion:
                        config.error = traceback.format_exc()

                # IMPRESIÓN ACTUALIZADA EN LA CONSOLA
                os.system(comando_limpiar)
                print("-" * 75)
                print(f" ROBOT OPERATIVO AUTOMÁTICO XTB | MONITOR DE RIESGO % NATIVO FIXED")
                print(f" Servidor activo: {time.strftime('%H:%M:%S')}")
                print(f"{ui_general()}")
                print(f"{texto_indicadores}")
                print(f"{texto_operacion_activa}")
                print(f"{texto_trailing}")
                print(f"{texto_stop_loss}")
                print("-" * 75)
                print(f" 💰 TAKE PROFIT : {config.TAKE_PROFIT}")
                print("-" * 75)
                print(f" 🚦 FILTRO ENTRADAS : {'🔒 BLOQUEADO (Operación detectada)' if operacion_activa else '🔓 EN ESPERA DE SEÑAL'}")
                print(f"{ui_estadisticas(motivo_cierre)}")
                print("=" * 75)
                print(f" 🔴 Ultimo error              : {config.error}")
                print("=" * 75)
                        
            except Exception as e_bucle:
                config.error = traceback.format_exc()
                time.sleep(0.1)
            
    except Exception as e:
        config.error = traceback.format_exc()

if __name__ == "__main__":
    try:
        bot_scalping()
    except KeyboardInterrupt:
        print("\n\nSistema apagado de forma segura")

