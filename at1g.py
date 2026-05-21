from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import os
import re
import threading
import traceback
import pandas as pd
import numpy as np
# CONFIGURACIÓN OBLIGATORIA PARA ENTORNO MAC OS (MINICONDA)
import matplotlib
matplotlib.use('TkAgg') # Fuerza a tu Mac a abrir la ventana interactiva independiente
import mplfinance as mpf
import matplotlib.pyplot as plt
import config
from patrones.identificar_patrones import identificar_patrones
from extraction.extract import extraer_velas

# ===========================================================================
# 📊 AUXILIAR: EXTRACCIÓN DE DATOS FILTRADOS POR COLUMNA DESDE EL DOM
# ===========================================================================
def extraer_datos(lista_cruda):
    """
    Procesa la lista plana de strings reales de xStation eliminando espacios
    invisibles y aislando las cadenas puras para cada columna del bot.
    """
    # Si por desajuste del bucle principal pasara la matriz de detalles completa, extraemos la primera fila
    if len(lista_cruda) > 0 and isinstance(lista_cruda[0], list):
        lista_cruda = lista_cruda[0]

    filtrados = [str(d).replace('\xa0', ' ').strip() for d in lista_cruda if str(d).strip()]
    
    datos_mapeados = {
        "Activo": "N/D", "Tipo": "N/D", "Volumen": "N/D", 
        "Valor Contrato": "N/D", "Precio Actual": "N/D", 
        "Precio Apertura": "N/D", "Beneficio %": "N/D", "Beneficio Neto": "N/D"
    }
    
    # CORRECCIÓN EN EL INDEXADO: Extraemos el valor del string puro por posición exacta
    if len(filtrados) >= 2:
        datos_mapeados["Activo"] = filtrados[0]  # Cambiado para tomar solo 'US30'
        datos_mapeados["Tipo"] = filtrados[1]    # Cambiado para tomar solo 'CFD'
        
    for i in range(len(filtrados) - 1):
        texto_actual = filtrados[i].lower()
        siguiente_texto = filtrados[i+1]
        
        if "volumen" == texto_actual:
            datos_mapeados["Volumen"] = siguiente_texto
        elif "valor del contrato" in texto_actual:
            datos_mapeados["Valor Contrato"] = siguiente_texto
        elif "precio actual" in texto_actual:
            datos_mapeados["Precio Actual"] = siguiente_texto
        elif "precio medio de apertura" in texto_actual:
            datos_mapeados["Precio Apertura"] = siguiente_texto
        elif "beneficio neto %" in texto_actual:
            datos_mapeados["Beneficio %"] = siguiente_texto
        elif "beneficio neto" == texto_actual:
            datos_mapeados["Beneficio Neto"] = siguiente_texto
            
    # BÚSQUEDA EXHAUSTIVA DE RESPALDO SI EL MAPEO INDEPENDIENTE SE CORRE
    if datos_mapeados["Beneficio %"] == "N/D" or "%" not in str(datos_mapeados["Beneficio %"]):
        for elemento in filtrados:
            if "%" in elemento and ("-" in elemento or re.search(r'\d', elemento)):
                datos_mapeados["Beneficio %"] = elemento
                break

    return datos_mapeados

# ===========================================================================
# ⚡ ROBOT GRABADOR, EJECUTADOR Y GESTOR DE RIESGO
# ===========================================================================
def robot_grabador_ticks_xtb():
    global datos_compartidos, ticks_bloque_actual, lista_velas_acumuladas, estadisticas_bot, tiempo_ultimo_cierre, historico_volumen, promedio_volumen
    global promedio_volumen_sin_actual, motivo_cierre_stats, error
    opciones = Options()
    opciones.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    
    try:
        driver = webdriver.Chrome(options=opciones)
        comando_limpiar = 'cls' if os.name == 'nt' else 'clear'
        ultimo_sell, ultimo_buy = "", ""
        minuto_anterior = ""
        
        bloqueo_orden_vela = False
        minuto_ultima_orden = ""
        texto_macd = ""
        texto_volumen = ""
        
        # Variables persistentes fuera del bucle de mercado para evitar reinicios continuos
        maximo_rendimiento_alcanzado = -999.0
        trailing_activado = False
        resultado_confluencia = "Ninguno"
        
        print("Conexión exitosa con Chrome DevTools en el puerto 9222.")
        
        while True:
            try:
                todos_los_sell = driver.find_elements(By.ID, "sellButton")
                todos_los_buy = driver.find_elements(By.ID, "buyButton")
                todos_los_activos = driver.find_elements(By.CLASS_NAME, "chart-panel-symbol-title")
                todos_los_lotes = driver.find_elements(By.CSS_SELECTOR, "span.ui-spinner-amount-value, input[name='stepperInput'], [id='volumeInput']")
                
                precio_sell_visible, precio_buy_visible = "0.00", "0.00"
                boton_compra_real, boton_venta_real = None, None
                lote_visible = "No detectado"
                activo_detectado = None

                for activo in todos_los_activos:
                    if activo.is_displayed():
                        texto_bruto = activo.get_attribute("textContent")
                        if texto_bruto:
                            activo_detectado = texto_bruto.replace("CFD", "").strip()
                            break
     
                if activo_detectado != config.activo_actual:
                    config.activo_actual = activo_detectado
                    extraer_datos_velas()

                for boton in todos_los_sell:
                    if boton.is_displayed() and boton.is_enabled():
                        precio_sell_visible = boton.get_attribute("textContent").strip()
                        config.datos_compartidos["sell"] = precio_sell_visible
                        boton_venta_real = boton
                        break
                for boton in todos_los_buy:
                    if boton.is_displayed() and boton.is_enabled():
                        precio_buy_visible = boton.get_attribute("textContent").strip()
                        config.datos_compartidos["buy"] = precio_buy_visible
                        boton_compra_real = boton
                        break
                for vol in todos_los_lotes:
                    if vol.is_displayed():
                        texto_vol = vol.get_attribute("value") if vol.tag_name == "input" else vol.get_attribute("textContent").strip()
                        if texto_vol: lote_visible = texto_vol.replace("USD", "").strip(); break
                        
                if precio_buy_visible != "0.00":
                    try:
                        limpio = "".join(re.findall(r'[\d\.]', precio_buy_visible.replace(",", "")))
                        precio_numerico = float(limpio)
                        if precio_numerico > 0: 
                            config.ticks_bloque_actual.append(precio_numerico)
                    except Exception: 
                        config.error = traceback.format_exc()
                        pass
                    
                xpath_indicadores = "//*[contains(@class, 'indicator-value-label')] | //span[contains(@class, 'chart-indicator-value')]"
                elementos_indicadores = driver.find_elements(By.XPATH, xpath_indicadores)
                num_rsi_leido, num_adx_leido = None, None
                
                for elemento in elementos_indicadores:
                    if elemento.is_displayed():
                        try: texto_identificador = elemento.find_element(By.XPATH, "./..").get_attribute("textContent").upper()
                        except: texto_identificador = ""
                        contenido = elemento.get_attribute("title") or elemento.get_attribute("textContent")
                        if not contenido: continue
                        
                        contenido_limpio = contenido.replace(",", ".")

                        if "RSI" in texto_identificador:
                            decimales_rsi = re.findall(r'-?\d+\.\d+|-?\d+', contenido)
                            if decimales_rsi: num_rsi_leido = float(decimales_rsi[-1]); config.datos_compartidos["rsi_live"] = f"{num_rsi_leido:.2f}"
                        elif "ADX" in texto_identificador:
                            decimales_adx = re.findall(r'-?\d+\.\d+|-?\d+', contenido)
                            if decimales_adx: num_adx_leido = float(decimales_adx[0]); config.datos_compartidos["adx_live"] = f"{num_adx_leido:.2f}"
                        elif "MACD" in texto_identificador and "." in contenido_limpio:
                            partes_macd = [p.strip() for p in contenido_limpio.split(".")]
                            if len(partes_macd) >= 2:
                                decimales_macd = re.findall(r'-?\d+\.\d+|-?\d+', contenido_limpio)
                                num_linea = float(decimales_macd[0])
                                num_senal = float(decimales_macd[1])
                                valor_hist = num_linea - num_senal
                                macd_histograma = f"{valor_hist:.2f}"
                                texto_tendencia = "🔴 A LA BAJA" if valor_hist < 0 else "🟢 AL ALZA"

                                texto_macd = (
                                    f" 📉 HISTOGRAMA MACD\n"
                                    f"  ───────────────────────────────────\n"
                                    f"   Línea venta  : {num_senal}\n"
                                    f"   Línea compra : {num_linea}\n"
                                    f"   Diferencia   : {macd_histograma}\n"
                                    f"   Tendencia    : {texto_tendencia}" 
                                )
                        elif "VOL" in texto_identificador:
                            if contenido != "n/a":
                                valor_volumen = int(contenido)
                                texto_volumen = f" 🔋 HISTORICO DE VOLUMEN: {config.historico_volumen}"
                            
                if num_rsi_leido is None: num_rsi_leido = 50.0; config.datos_compartidos["rsi_live"] = "--- (Fijo/DOM Oculto)"
                if num_adx_leido is None: num_adx_leido = 35.0; config.datos_compartidos["adx_live"] = "--- (Fijo/DOM Oculto)"

                if num_adx_leido >= config.ADX_TENDENCIA_FUERTE:
                    adx_valor = f"{num_adx_leido:.2f} 🔥 (Tendencia Fuerte)"
                else:
                    adx_valor = f"{num_adx_leido:.2f} 💤 (Mercado Lateral)"
                
                if minuto_ultima_orden != time.strftime('%M'):
                    bloqueo_orden_vela = False
                minuto_actual = time.strftime('%M')
                
                if minuto_anterior == "": minuto_anterior = minuto_actual

                # Perforador Shadow DOM
                js_script_shadow = """
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
                
                resultado_shadow = driver.execute_script(js_script_shadow)
                total_posiciones = resultado_shadow["total"]
                operaciones_detalles = resultado_shadow["detalles"]
                
                config.datos_compartidos["lucro"] = "Sin operaciones abiertas"
                config.datos_compartidos["trailing_status"] = "Inactivo"
                ejecutar_cierre = False
                operacion_activa = total_posiciones > 0
                operacion_ganada = False
                reporte_stop_loss_consola = "\nNinguna posición abierta"

                if operacion_activa and len(operaciones_detalles) > 0:
                    global hora_apertura_orden
                    if config.hora_apertura_orden is None:
                        config.hora_apertura_orden = time.time()
                        maximo_rendimiento_alcanzado = -999.0  
                        trailing_activado = False

                    om = extraer_datos(operaciones_detalles)
                    
                    try:
                        texto_porcentaje = str(om["Beneficio %"]).replace("%", "").replace(" ", "").replace(",", ".")
                        match_pct = re.search(r'([-+]?\d+\.\d+|-?\d+)', texto_porcentaje)
                        rendimiento_actual = float(match_pct.group(1)) if match_pct else 0.0
                    except:
                        rendimiento_actual = 0.0

                    reporte_stop_loss_consola = (
                        f"🔴 FIJADO: {config.PORCENTAJE_STOP_LOSS:.1f}%\n"
                        f"🔴 ACTUAL: {rendimiento_actual:+.2f}%"
                    )

                    if rendimiento_actual <= config.PORCENTAJE_STOP_LOSS:
                        config.motivo_cierre_stats = f"Loss ({rendimiento_actual:+.2f}%)"
                        operacion_ganada = False
                        ejecutar_cierre = True
                    
                    if rendimiento_actual > maximo_rendimiento_alcanzado:
                        maximo_rendimiento_alcanzado = rendimiento_actual
                        
                    if maximo_rendimiento_alcanzado >= config.PORCENTAJE_ACTIVACION_TRAILING:
                        trailing_activado = True

                    if trailing_activado:                        
                        caida_desde_pico = maximo_rendimiento_alcanzado - rendimiento_actual
                        reporte_trailing_consola = (
                            f"🔥 ACTIVADO\n"
                            f"🔥 MAXIMO RENDIMIENTO ALCANZADO: +{maximo_rendimiento_alcanzado:.2f}%\n"
                            f"🔥 CAIDA DESDE EL ULTIMO PICO: {caida_desde_pico:.2f}%\n"
                            f"🔥 % ACTIVACION DE TRAILING: {config.PORCENTAJE_ACTIVACION_TRAILING}%\n"
                            f"🔥 TRAILING STOP: {config.DISTANCIA_TRAILING_MAXIMA}%"
                        )
                        config.datos_compartidos["trailing_status"] = f"Trailing Activo (Máx: +{maximo_rendimiento_alcanzado:.2f}%)"
                        
                        if caida_desde_pico >= config.DISTANCIA_TRAILING_MAXIMA:
                            config.motivo_cierre_stats = f"Win Trailing. Rendimiento actual: {rendimiento_actual:+.2f}%. Ultimo pico de rendimiento: {caida_desde_pico:+.2f}%."
                            ejecutar_cierre = True
                            operacion_ganada = True
                    else:
                        reporte_trailing_consola = f"💤 Inactivo (% Actual: {rendimiento_actual:+.2f}% / Requerido: {config.PORCENTAJE_ACTIVACION_TRAILING}%)"

                    icono_beneficio = "🟢" if rendimiento_actual >= 0 else "🔴"

                    lucro_flotante_visible = (
                        f"📌 [OPERACIÓN #1]\n"
                        f"  ───────────────────────────────────\n"
                        f"   💱 Instrumento:      {om['Activo']} ({om['Tipo']})\n"
                        f"   📦 Volumen (Lotes):  {om['Volumen']}\n"
                        f"   🚀 Precio Apertura:  {om['Precio Apertura']}\n"
                        f"   📊 Precio Actual:    {om['Precio Actual']}\n"
                        f"   {icono_beneficio} Beneficio Neto:   {om['Beneficio Neto']} ({om['Beneficio %']})"
                    )
                    config.datos_compartidos["lucro"] = f"{om['Beneficio Neto']} ({om['Beneficio %']})"

                    beneficio_neto = float(str(om['Beneficio Neto']).replace(",", ".").replace(" ", ""))

                    if beneficio_neto >= config.TAKE_PROFIT_MONETARIO:
                        ejecutar_cierre = True
                        operacion_ganada = True
                        config.motivo_cierre_stats = f"Take Profit Alcanzado (+${beneficio_neto:.2f})"
                else:
                    lucro_flotante_visible = "Sin operaciones abiertas"
                    reporte_trailing_consola = f"💤 Inactivo"
                    config.hora_apertura_orden = None

                if int(minuto_actual) % config.TEMPORALIDAD_MINUTOS == 0 and minuto_actual != minuto_anterior:
                    if time.time() - config.tiempo_ultimo_cierre < config.SEGUNDOS_ENFRIAMIENTO:
                        continue

                    if len(config.ticks_bloque_actual) > 0:
                        nueva_vela_ohlc = {
                            "Open": config.ticks_bloque_actual[0], 
                            "High": max(config.ticks_bloque_actual), 
                            "Low": min(config.ticks_bloque_actual), 
                            "Close": config.ticks_bloque_actual[-1]
                        }

                        config.lista_velas_acumuladas.append(nueva_vela_ohlc)
                        config.ticks_bloque_actual = []
                        minuto_anterior = minuto_actual
                        df_historial_total = pd.DataFrame(config.lista_velas_acumuladas)
                        df_historial_total.index = pd.date_range(start="2026-01-01 09:30", periods=len(df_historial_total), freq=f"{config.TEMPORALIDAD_MINUTOS}min")
                        
                        resultado_confluencia = identificar_patrones(df_historial_total, num_adx_leido)
                        config.datos_compartidos["status_patrones"] = resultado_confluencia
                        config.datos_compartidos["df_velas"] = df_historial_total
                        
                        try:
                            valor_numerico = float(macd_histograma)
                            config.historico_macd.append(valor_numerico)
                        except (ValueError, TypeError):
                            config.error = "⚠️ No se pudo guardar: el valor del MACD no es numérico."

                        if len(config.historico_macd) > 2:
                            config.historico_macd.pop(0)

                        config.historico_volumen.append(valor_volumen)                        
                        if len(config.historico_volumen) > 6:
                            config.historico_volumen.pop(0)
                            config.promedio_volumen = sum(config.historico_volumen)
                            config.promedio_volumen_sin_actual = sum(config.historico_volumen[-6:-1])

                # Ejecución automática de operaciones bajo confluencia estricta
                if not operacion_activa:    
                    if not bloqueo_orden_vela and num_adx_leido >= config.ADX_TENDENCIA_FUERTE:
                        if "COMPRA" in resultado_confluencia and boton_compra_real:
                            boton_compra_real.click()
                            os.system('say "Comprando" &')
                            bloqueo_orden_vela = True
                            minuto_ultima_orden = time.strftime('%M')
                            config.hora_apertura_orden = time.time()
                            config.estadisticas_bot["total_ordenes"] += 1
                            config.estadisticas_bot["ultimo_patron_operado"] = resultado_confluencia.split("_")[-1]
                        elif "VENTA" in resultado_confluencia and boton_venta_real:
                            boton_venta_real.click()
                            os.system('say "Vendiendo" &')
                            bloqueo_orden_vela = True
                            minuto_ultima_orden = time.strftime('%M')
                            config.hora_apertura_orden = time.time()
                            config.estadisticas_bot["total_ordenes"] += 1
                            config.estadisticas_bot["ultimo_patron_operado"] = resultado_confluencia.split("_")[-1]                        
                
                # MÓDULO DE ACCIÓN DE CIERRE
                if ejecutar_cierre and operacion_activa:
                    try:
                        driver.execute_script("if(window.ultimoBotonCierre) { window.ultimoBotonCierre.click(); }")
                        os.system(f'say "Posición cerrada por {config.motivo_cierre_stats}" &')
                        
                        if operacion_ganada:
                            config.estadisticas_bot["ganadas"] += 1
                        else:
                            config.estadisticas_bot["perdidas"] += 1
                            
                        config.historico_cuenta.append(beneficio_neto)
                        config.tiempo_ultimo_cierre = time.time()
                        config.hora_apertura_orden = None
                        trailing_activado = False
                        maximo_rendimiento_alcanzado = -999.0
                        lucro_flotante_visible = "Sin operaciones abiertas"
                        time.sleep(5)
                    except Exception as error_ejecucion:
                        config.error = traceback.format_exc()
                    
                win_rate = (config.estadisticas_bot["ganadas"] / config.estadisticas_bot["total_ordenes"] * 100) if config.estadisticas_bot["total_ordenes"] > 0 else 0.0
                
                if config.datos_compartidos["sell"] != ultimo_sell or config.datos_compartidos["buy"] != ultimo_buy:
                    ultimo_sell, ultimo_buy = config.datos_compartidos["sell"], config.datos_compartidos["buy"]
                    os.system(comando_limpiar)
                    print("=" * 75)
                    print(f" ROBOT OPERATIVO AUTOMATIZADO XTB | SISTEMA DE CONTROL TOTAL BLINDADO")
                    print(f" Servidor activo: {time.strftime('%H:%M:%S')} | Lote: {lote_visible} | Activo: {config.activo_actual}")
                    print("=" * 75)
                    print(f" 🔴 PRECIO ASK (SELL) : {config.datos_compartidos['sell']}")
                    print(f" 🟢 PPRECIO BID (BUY) : {config.datos_compartidos['buy']}")
                    print("-" * 75)
                    print(f"{texto_macd}")
                    print("-" * 75)
                    print(f"{texto_volumen}")
                    print("-" * 75)
                    print(f" ⚛️  OSCILADOR RSI : {config.datos_compartidos['rsi_live']}")
                    print("-" * 75)
                    print(f" 📊 IMPULSO ADX : {adx_valor}")                    
                    print("-" * 75)
                    print(f"{lucro_flotante_visible}")
                    print("-" * 75)
                    print(f" 🧭 TRAILING STOP : {reporte_trailing_consola}")
                    print("-" * 75)
                    print(f" 🧭 STOP LOSS ACTUAL")
                    print(f"{reporte_stop_loss_consola}")
                    print("-" * 75)
                    print(f" 💰 TAKE PROFIT : {config.TAKE_PROFIT_MONETARIO}")
                    print("-" * 75)
                    print(f" 🚦 FILTRO ENTRADAS : {'🔒 BLOQUEADO (Operación detectada)' if operacion_activa else '🔓 EN ESPERA DE SEÑAL'}")
                    print("=" * 75)
                    print(f" 🧭 GATILLO DE CONFLUENCIA CONFIRMADO")
                    print(f" {config.datos_compartidos['senal_accion']}")
                    print("-" * 75)
                    print(f" 📊 CUADRO DE ESTADÍSTICAS Y MÉTRICAS DE EFECTIVIDAD (HOY):")
                    print(f" ↳ Operaciones Ganadas  🟢 : {config.estadisticas_bot['ganadas']}")
                    print(f" ↳ Operaciones Perdidas 🔴 : {config.estadisticas_bot['perdidas']}")
                    print(f" ↳ Total Ejecutadas ⚡ : {config.estadisticas_bot['total_ordenes']}")
                    print(f" ↳ Porcentaje de Acierto🎯 : {win_rate:.1f}% Win Rate")
                    print(f" ↳ Histórico de la cuenta  : {config.historico_cuenta}")
                    print(f" ↳ Ultimo cierre           : {config.motivo_cierre_stats}")
                    print("=" * 75)
                    print(f"🔴 Ultimo error            : {config.error}")
                    
            except Exception as error_ejecucion:
                config.error = traceback.format_exc()
                pass
            time.sleep(0.1)
    except Exception as e: 
        config.error = traceback.format_exc()

# ===========================================================================
# 📈 MOTOR GRÁFICO REAL TIME PARA MAC OS (NATIVO ASÍNCRONO)
# ===========================================================================
from matplotlib.animation import FuncAnimation

def loop_render_grafico(frame, fig, ax):
    """Refresca la GUI de manera segura interactuando directamente con Matplotlib."""
    try:
        df_actual = config.datos_compartidos["df_velas"].copy()
        idx_senal = config.datos_compartidos["indice_senal"]
        tipo_sig = config.datos_compartidos["tipo_senal"]
        
        # Generar set de prueba inicial para que el gráfico no nazca vacío
        if df_actual.empty:
            return
            
        ax.clear() # Limpieza de primitivas viejas para evitar superposición
        apf = []
        
        if idx_senal is not None and idx_senal in df_actual.index:
            compra_lista = [np.nan] * len(df_actual)
            venta_lista = [np.nan] * len(df_actual)
            pos_idx = df_actual.index.get_loc(idx_senal)
            
            if "COMPRA" in tipo_sig:
                compra_lista[pos_idx] = df_actual.loc[idx_senal, 'Low'] - 2.0
                apf.append(mpf.make_addplot(compra_lista, type='scatter', markersize=150, marker='^', color='green', ax=ax))
            elif "VENTA" in tipo_sig:
                venta_lista[pos_idx] = df_actual.loc[idx_senal, 'High'] + 2.0
                apf.append(mpf.make_addplot(venta_lista, type='scatter', markersize=150, marker='v', color='red', ax=ax))
                
        # Corrección estructural: Pasar el eje explícito a mplfinance para evitar congelamientos en Mac
        if apf:
            mpf.plot(df_actual, type='candle', ax=ax, addplot=apf, style='charles', datetime_format='%H:%M')
        else:
            mpf.plot(df_actual, type='candle', ax=ax, style='charles', datetime_format='%H:%M')
            
        fig.canvas.draw_idle() # Redibujo eficiente optimizado para backend TkAgg
    except Exception as e:
        config.error = traceback.format_exc()
        pass

def extraer_datos_velas():
    config.lista_velas_acumuladas = extraer_velas(config.activo_actual)
    df_historial_total = pd.DataFrame(config.lista_velas_acumuladas)
    config.datos_compartidos["df_velas"] = df_historial_total
    df_historial_total.index = pd.date_range(start="2026-01-01 09:30", periods=len(df_historial_total), freq=f"{config.TEMPORALIDAD_MINUTOS}min")

def iniciar_renderizado_grafico_mac():
    # Inicialización de la figura y el eje nativo
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Lanzar subproceso del bot de forma segura y paralela
    hilo_grabador = threading.Thread(target=robot_grabador_ticks_xtb)
    hilo_grabador.daemon = True
    hilo_grabador.start()
    
    print("[+] Lanzando panel gráfico con auditoría estadística...")
    
    # Animación automática nativa que maneja el refresco asíncrono
    ani = FuncAnimation(fig, loop_render_grafico, fargs=(fig, ax), interval=1000, cache_frame_data=False)
    plt.show()

if __name__ == "__main__":
    try: 
        iniciar_renderizado_grafico_mac()
    except KeyboardInterrupt: 
        plt.close('all')
        print("\n\n[!] Finalizado con éxito.")
