from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import traceback
import time
import os
import re
import config
from indicadores.operaciones import ejecutar_operacion
from ui.interfaz import ui_adx, ui_macd, ui_rsi, ui_ema, ui_trailing, ui_stop_loss, ui_operacion_activa, ui_estadisticas, ui_volumen, ui_general
from files.tracking import guardar_estadistica, actualizar_ultima_operacion

# 📊 HISTORIAL GLOBAL PARA CONSTRUIR EL GRÁFICO ASCII NATIVO
historial_precios_recientes = []

hora_apertura_orden = None
operacion_ganada = None
maximo_rendimiento_alcanzado = 0.0  
trailing_activado = False
bloqueo_orden_vela = False
minuto_anterior = ""
minuto_ultima_orden = ""
motivo_cierre_stats = "N/D"
driver = None
comando_limpiar = None
boton_comprar = None
boton_vender = None

def actualizar_estadisticas_cierre(ganada=False):
    """Registra una operación ejecutada y actualiza si fue ganada o perdida."""
    global estadisticas_bot
    config.estadisticas_bot["total_ordenes"] += 1
    if ganada: config.estadisticas_bot["ganadas"] += 1
    else: config.estadisticas_bot["perdidas"] += 1

def extraer_datos_operacion(lista_cruda):
    """
    Procesa la lista plana de strings reales de xStation eliminando espacios
    invisibles y aislando las cadenas puras para cada columna del bot.
    """
    # Si por desajuste del bucle principal pasara la matriz de detalles completa, extraemos la primera fila
    if len(lista_cruda) > 0 and isinstance(lista_cruda[0], list):
        lista_cruda = lista_cruda[0]

    filtrados = [str(d).replace('\xa0', ' ').strip() for d in lista_cruda if str(d).strip()]
    
   
    if len(filtrados) >= 2:
        config.datos_mapeados["Activo"] = filtrados[0]  # Cambiado para tomar solo 'US30'
        config.datos_mapeados["Tipo"] = filtrados[1]    # Cambiado para tomar solo 'CFD'
        
    for i in range(len(filtrados) - 1):
        texto_actual = filtrados[i].lower()
        siguiente_texto = filtrados[i+1]
        
        if "volumen" == texto_actual:
            config.datos_mapeados["Volumen"] = siguiente_texto
        elif "valor del contrato" in texto_actual:
            config.datos_mapeados["Valor Contrato"] = siguiente_texto
        elif "precio actual" in texto_actual:
            config.datos_mapeados["Precio Actual"] = siguiente_texto
        elif "precio medio de apertura" in texto_actual:
            config.datos_mapeados["Precio Apertura"] = siguiente_texto
        elif "beneficio neto %" in texto_actual:
            config.datos_mapeados["Beneficio %"] = siguiente_texto
        elif "beneficio neto" == texto_actual:
            config.datos_mapeados["Beneficio Neto"] = siguiente_texto
            
    # BÚSQUEDA EXHAUSTIVA DE RESPALDO SI EL MAPEO INDEPENDIENTE SE CORRE
    if config.datos_mapeados["Beneficio %"] == "N/D" or "%" not in str(config.datos_mapeados["Beneficio %"]):
        for elemento in filtrados:
            if "%" in elemento and ("-" in elemento or re.search(r'\d', elemento)):
                config.datos_mapeados["Beneficio %"] = elemento
                break

def inicializar():
    global bloqueo_orden_vela, minuto_anterior, minuto_ultima_orden, motivo_cierre_stats, driver, comando_limpiar

    opciones = Options()
    opciones.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

    print("Intentando enlazar con Chrome en el puerto 9222...")
    driver = webdriver.Chrome(options=opciones)

    driver.set_page_load_timeout(3)
    driver.implicitly_wait(0.1)

    comando_limpiar = 'cls' if os.name == 'nt' else 'clear'

    bloqueo_orden_vela = False
    minuto_anterior = ""
    minuto_ultima_orden = ""
    motivo_cierre_stats = "N/D"

    os.system(comando_limpiar)
    print("=" * 75)
    print("¡Conectado con éxito a xStation!")
    print("=" * 75)
    time.sleep(1)

def obtener_datos_operaciones():
    return """
        let botonesValidos = [];
        let todosLosBotones = document.querySelectorAll("button[data-testid='close-button']");
        
        todosLosBotones.forEach(btn => {
            if (btn.offsetWidth > 0 || btn.offsetHeight > 0) { botonesValidos.push(btn); }
        });
        
        if (botonesValidos.length === 0) {
            let elementosGlobales = document.querySelectorAll("*");
            elementosGlobales.forEach(el => {
                if (el.shadowRoot) {
                    let btnShadow = el.shadowRoot.querySelector("button[data-testid='close-button']");
                    if (btnShadow && (btnShadow.offsetWidth > 0 || btnShadow.offsetHeight > 0)) {
                        botonesValidos.push(btnShadow);
                    }
                }
            });
        }
        
        let datosOperaciones = [];
        botonesValidos.forEach(btn => {
            let fila = btn.closest("tr") || btn.closest("[role='row']") || btn.parentElement.parentElement;
            if (fila) {
                let textos = fila.innerText.split('\\n').map(t => t.trim()).filter(t => t.length > 0);
                datosOperaciones.push(textos);
            }
        });
        
        if (botonesValidos.length > 0) { window.ultimoBotonCierre = botonesValidos[0]; }
        return { "total": botonesValidos.length, "detalles": datosOperaciones };
        """

# ===========================================================================
# ESCANEO CON PERFORADOR SHADOW DOM Y GESTIÓN DE MATRICES
# ===========================================================================
def obtener_datos_compra_venta(segundo_actual):
    global boton_comprar, boton_vender

    # Capturar los datos de compra, venta y lote (proporcion a comprar) de la pestaña actual
    botones_vender = driver.find_elements(By.CSS_SELECTOR, "#sellButton, [id='sellButton']")
    botones_comprar = driver.find_elements(By.CSS_SELECTOR, "#buyButton, [id='buyButton']")
    botones_lote = driver.find_elements(By.CSS_SELECTOR, "span.ui-spinner-amount-value, input[name='stepperInput'], [id='volumeInput']")
    activos = driver.find_elements(By.CLASS_NAME, "chart-panel-symbol-title")
    
    boton_comprar = None
    boton_vender = None

    for boton in botones_vender:
        if boton.is_displayed() and boton.is_enabled():
            if (segundo_actual != config.ultimo_segundo_procesado):
                config.ultimo_valor_venta = config.valor_venta
            config.valor_venta = boton.get_attribute("textContent").strip()
            boton_vender = boton
            break
    for boton in botones_comprar:
        if boton.is_displayed() and boton.is_enabled():
            if (segundo_actual != config.ultimo_segundo_procesado):
                config.ultimo_valor_compra = config.valor_compra
            config.valor_compra = boton.get_attribute("textContent").strip()
            boton_comprar = boton
            break
    for vol in botones_lote:
        if vol.is_displayed():
            texto_vol = vol.get_attribute("value") if vol.tag_name == "input" else vol.get_attribute("textContent").strip()
            if texto_vol:
                config.valor_lote = texto_vol.replace("USD", "").strip()
                break
    for activo in activos:
        if activo.is_displayed():
            texto_bruto = activo.get_attribute("textContent")
            if texto_bruto:
                activo_detectado = texto_bruto.replace("CFD", "").strip()
                break
    
    if activo_detectado != config.activo_actual:
        config.activo_actual = activo_detectado
        config.promedio_volumen = 0
        config.promedio_volumen_sin_actual = 0.0
        config.historico_macd = []
        config.historico_rsi = []

def bot_scalping():
    global estadisticas_bot, hora_apertura_orden, operacion_ganada
    global maximo_rendimiento_alcanzado, trailing_activado, tiempo_ultimo_cierre
    global bloqueo_orden_vela, minuto_anterior, minuto_ultima_orden, motivo_cierre_stats, driver, comando_limpiar
    global boton_comprar, boton_vender
    
    try:
        inicializar()

        while True:
            try:
                if minuto_ultima_orden != time.strftime('%M'):
                    bloqueo_orden_vela = False
                
                minuto_actual = time.strftime('%M')                
                if minuto_anterior == "": minuto_anterior = minuto_actual

                segundo_actual = time.strftime('%H:%M:%S')
                segundo_actual_int = time.strftime('%S')
                obtener_datos_compra_venta(segundo_actual)

                if segundo_actual != config.ultimo_segundo_procesado:
                    config.ultimo_segundo_procesado = segundo_actual
                
                if int(segundo_actual_int) - 2 >= int(config.penultimo_segundo_procesado):
                    config.ultimo_valor_volumen = config.valor_volumen
                    config.penultimo_segundo_procesado = segundo_actual_int

                config.valor_macd = "No detectado"
                config.valor_rsi = None
                config.valor_adx = None
                texto_macd = ""
                texto_rsi = ""
                texto_adx = ""
                texto_volumen = ""
                texto_ema = ""

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
                            texto_separador = "-" * 75
                            texto_final = "=" * 75

                            texto_indicadores = (
                                f"{texto_separador}\n"
                                f"{texto_macd}\n"
                                f"{texto_separador}\n"
                                f"{texto_rsi}\n"
                                f"{texto_separador}\n"
                                f"{texto_adx}\n"
                                f"{texto_separador}\n"
                                f"{texto_volumen}\n"
                                f"{texto_separador}\n"
                                f"{texto_ema}\n"
                                f"{texto_final}"
                            )
                    except: continue

                if minuto_ultima_orden != time.strftime('%M'):
                    bloqueo_orden_vela = False

                js_script_shadow = obtener_datos_operaciones()
                
                resultado_shadow = driver.execute_script(js_script_shadow)
                total_posiciones = resultado_shadow["total"]
                operaciones_detalles = resultado_shadow["detalles"]
                
                operacion_activa = total_posiciones > 0
                ejecutar_cierre = False
                beneficio_neto = None
                
                texto_trailing = ui_trailing(False, False, None, None)

                texto_stop_loss = ui_stop_loss(False, None)

                if operacion_activa and len(operaciones_detalles) > 0:
                    if hora_apertura_orden is None:
                        hora_apertura_orden = time.time()
                        maximo_rendimiento_alcanzado = -999.0  
                        trailing_activado = False
                    
                    # Llamamos a la extracción con la matriz limpia
                    extraer_datos_operacion(operaciones_detalles)
                    
                    # --- FILTRADO DE SEGURIDAD EXTREMA DEL % ---
                    try:
                        texto_porcentaje = str(config.datos_mapeados["Beneficio %"]).replace("%", "").replace(" ", "").replace(",", ".")
                        match_pct = re.search(r'([-+]?\d+\.\d+|-?\d+)', texto_porcentaje)
                        rendimiento_actual = float(match_pct.group(1)) if match_pct else 0.0
                    except:
                        rendimiento_actual = 0.0
                    
                    # ─── LÓGICA DE CONTROL POR % NATIVO: STOP LOSS DIRECTO ───
                    texto_stop_loss = ui_stop_loss(True, rendimiento_actual)
                    
                    if rendimiento_actual <= config.PORCENTAJE_STOP_LOSS:
                        motivo_cierre_stats = f"Loss ({rendimiento_actual:+.2f}%)"
                        operacion_ganada = False
                        ejecutar_cierre = True
                    
                    # ─── LÓGICA DE CONTROL POR % NATIVO: TRAILING STOP ───
                    if rendimiento_actual > maximo_rendimiento_alcanzado:
                        maximo_rendimiento_alcanzado = rendimiento_actual
                        
                    if maximo_rendimiento_alcanzado >= config.PORCENTAJE_ACTIVACION_TRAILING:
                        trailing_activado = True
                        
                    if trailing_activado:                        
                        caida_desde_pico = maximo_rendimiento_alcanzado - rendimiento_actual
                        texto_trailing = ui_trailing(True, True, maximo_rendimiento_alcanzado, caida_desde_pico)
                        
                        if caida_desde_pico >= config.DISTANCIA_TRAILING_MAXIMA:
                            motivo_cierre_stats = f"Win Trailing. Rendimiento actual: {rendimiento_actual:+.2f}%. Ultimo pico de rendimiento: {caida_desde_pico:+.2f}%."
                            ejecutar_cierre = True
                            operacion_ganada = True
                    else:
                        texto_trailing = ui_trailing(True, False, rendimiento_actual, None)

                    texto_operacion_activa = ui_operacion_activa(True, rendimiento_actual)
                    beneficio_neto =  float(config.datos_mapeados['Beneficio Neto'])

                    if beneficio_neto >= config.TAKE_PROFIT_MONETARIO:
                        ejecutar_cierre = True
                        operacion_ganada = True
                        motivo_cierre_stats = f"Take Profit Alcanzado (+${beneficio_neto:.2f})"
                    
                    if beneficio_neto > 0 and float(config.valor_rsi) < config.RSI_SOBREVENTA_MACD and config.datos_mapeados["Operacion"] == "Venta":
                        ejecutar_cierre = True
                        operacion_ganada = True
                        motivo_cierre_stats = f"Venta alcanzó el RSI de sobreventa - Se espera retroceso (+${beneficio_neto:.2f})"
                    
                    if beneficio_neto > 0 and float(config.valor_rsi) > config.RSI_SOBRECOMPRA_MACD and config.datos_mapeados["Operacion"] == "Compra":
                        ejecutar_cierre = True
                        operacion_ganada = True
                        motivo_cierre_stats = f"Venta alcanzó el RSI de sobrecompra - Se espera retroceso (+${beneficio_neto:.2f})"
                else:
                    texto_operacion_activa = ui_operacion_activa(False, None)
                    hora_apertura_orden = None

                if int(minuto_actual) % config.TEMPORALIDAD_MINUTOS == 0 and minuto_actual != minuto_anterior:
                    if time.time() - config.tiempo_ultimo_cierre < config.SEGUNDOS_ENFRIAMIENTO:
                        continue
                    
                    minuto_anterior = minuto_actual

                    # Adicionar el valor de los indicadores
                    try:
                        valor_numerico = float(config.valor_macd)
                        config.historico_macd.append(valor_numerico)
                    except (ValueError, TypeError):
                        config.error = f"⚠️ No se pudo guardar: el valor del MACD no es numérico: {config.valor_macd}"

                    if len(config.historico_macd) > 2:
                        config.historico_macd.pop(0)

                    try:
                        valor_numerico = float(config.valor_rsi)
                        config.historico_rsi.append(valor_numerico)
                    except (ValueError, TypeError):
                        config.error = f"⚠️ No se pudo guardar: el valor del RSI no es numérico: {config.valor_rsi}"

                    if len(config.historico_rsi) > 2:
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
                if not bloqueo_orden_vela and not operacion_activa:
                    # 🔥 CONTROL DE ENFRIAMIENTO TRAS CIERRE
                    if time.time() - config.tiempo_ultimo_cierre < config.SEGUNDOS_ENFRIAMIENTO:
                        continue # Salta la iteración si no ha pasado el tiempo mínimo

                    operacion = ejecutar_operacion()
    
                    if boton_comprar and operacion == "Comprar":                            
                            boton_comprar.click()
                            os.system('say "Comprando" &')
                            bloqueo_orden_vela = True
                            minuto_ultima_orden = time.strftime('%M')
                            hora_apertura_orden = time.time()                            
                            config.datos_mapeados['Operacion'] = "Compra"
                            guardar_estadistica("Compra")
                    elif boton_vender and operacion == "Vender":                            
                            boton_vender.click()
                            os.system('say "Vendiendo" &')
                            bloqueo_orden_vela = True
                            minuto_ultima_orden = time.strftime('%M')
                            hora_apertura_orden = time.time()                            
                            config.datos_mapeados['Operacion'] = "Venta"
                            guardar_estadistica("Venta")

                # ===========================================================================
                # MÓDULO DE GATILLADO Y ACCIÓN DE CIERRE DIRECTO
                # ===========================================================================
                if ejecutar_cierre and operacion_activa:
                    try:
                        driver.execute_script("if(window.ultimoBotonCierre) { window.ultimoBotonCierre.click(); }")
                        os.system(f'say "Posición cerrada por {motivo_cierre_stats}" &')
                        config.historico_cuenta.append(beneficio_neto)

                        # 🔥 REGISTRAR EL TIEMPO EXACTO DEL CIERRE
                        config.tiempo_ultimo_cierre = time.time()

                        hora_apertura_orden = None
                        trailing_activado = False
                        maximo_rendimiento_alcanzado = 0.0
                        operacion_ganada = None

                        # Sincronizador de estadísticas con lectura de resultados reales
                        if beneficio_neto > 0:
                            actualizar_ultima_operacion(config.datos_mapeados, "Si", motivo_cierre_stats)
                            actualizar_estadisticas_cierre(True)
                        else:
                            actualizar_ultima_operacion(config.datos_mapeados, "No", motivo_cierre_stats)
                            actualizar_estadisticas_cierre(False)

                        time.sleep(5)
                    except Exception as error_ejecucion:
                        config.error = traceback.format_exc()

                # IMPRESIÓN ACTUALIZADA EN LA CONSOLA
                os.system(comando_limpiar)
                print("=" * 75)
                print(f" ROBOT OPERATIVO AUTOMÁTICO XTB | MONITOR DE RIESGO % NATIVO FIXED")
                print(f" Servidor activo: {time.strftime('%H:%M:%S')}")
                print("=" * 75)
                print(f"{ui_general()}")
                print(f"{texto_indicadores}")
                print(f"{texto_operacion_activa}")
                print("-" * 75)
                print(f"{texto_trailing}")
                print("-" * 75)
                print(f"{texto_stop_loss}")
                print("-" * 75)
                print(f" 💰 TAKE PROFIT : {config.TAKE_PROFIT_MONETARIO}")
                print("-" * 75)
                print(f" 🚦 FILTRO ENTRADAS : {'🔒 BLOQUEADO (Operación detectada)' if operacion_activa else '🔓 EN ESPERA DE SEÑAL'}")
                print("=" * 75)
                print(f"{ui_estadisticas(motivo_cierre_stats)}")
                print("=" * 75)
                print(f" 🔴 Ultimo error              : {config.error}")
                print("=" * 75)
                        
            except Exception as e_bucle:
                config.error = traceback.format_exc()
                time.sleep(0.1)
                
            #time.sleep(0.1)
            
    except Exception as e:
        config.error = traceback.format_exc()

if __name__ == "__main__":
    try:
        bot_scalping()
    except KeyboardInterrupt:
        print("\n\nSistema apagado de forma segura")
