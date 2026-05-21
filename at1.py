from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import os
import re

# ===========================================================================
# ⚙️ CONFIGURACIÓN DE SCALPING INTELIGENTE CON GESTIÓN DE RIESGO TOTAL
# ===========================================================================
RSI_SOBRECOMPRA       = 80.0  # Límite estricto de sobrecompra
RSI_SOBREVENTA        = 15.0  # Límite estricto de sobreventa
ADX_TENDENCIA_FUERTE  = 25.0  # Filtro obligatorio de fuerza en el mercado

# PARÁMETROS DE GESTIÓN DE RIESGO ACTUALIZADOS
PORCENTAJE_ACTIVACION_TRAILING = 5.0   # 🔥 % mínimo de ganancia para activar el Trailing
DISTANCIA_TRAILING_MAXIMA    = 2.5   # % máximo que permites que retroceda desde su pico
PORCENTAJE_STOP_LOSS  = -10.0  # 🔴 Límite estricto de pérdida permitida en % (Gatillo SL)
TAKE_PROFIT_MONETARIO = 3.0  # 🔥 Modifica este valor por la ganancia deseada

SEGUNDOS_ENFRIAMIENTO = 60.0  # 🔥 Tiempo mínimo en segundos para esperar entre operaciones
tiempo_ultimo_cierre = 0.0     # Rastreo del timestamp del último cierre
# ===========================================================================
historico_cuenta = []

# 📊 HISTORIAL GLOBAL PARA CONSTRUIR EL GRÁFICO ASCII NATIVO
historial_precios_recientes = []

# 📈 VARIABLES GLOBALES DE ESTADÍSTICAS SOLICITADAS
stats = {
    "totales": 0,
    "ganadas": 0,
    "perdidas": 0
}

# Variables de rastreo de posición y Trailing Stop
hora_apertura_orden = None
operacion_ganada = None
maximo_rendimiento_alcanzado = 0.0  
trailing_activado = False

def dibujar_velas_ascii(precio_actual):
    """Genera un gráfico de barras dinámico en texto basado en los últimos
    movimientos del US30 directo en la terminal."""
    global historial_precios_recientes
    historial_precios_recientes.append(precio_actual)
    if len(historial_precios_recientes) > 15:
        historial_precios_recientes.pop(0)
    if len(historial_precios_recientes) < 2:
        return " [📊] Recolectando cotizaciones para el gráfico de barras..."
    max_p = max(historial_precios_recientes)
    min_p = min(historial_precios_recientes)
    rango = max_p - min_p if max_p != min_p else 1.0
    lineas_grafico = []
    for i in range(5, -1, -1):
        nivel_precio = min_p + (rango / 5) * i
        linea = f" {nivel_precio:>.2f} | "
        for p in historial_precios_recientes:
            if p >= nivel_precio: linea += " █ "
            else: linea += "   "
        lineas_grafico.append(linea)
    return "\n".join(lineas_grafico)

def actualizar_estadisticas_cierre(ganada=False):
    """Registra una operación ejecutada y actualiza si fue ganada o perdida."""
    global stats
    stats["totales"] += 1
    if ganada: stats["ganadas"] += 1
    else: stats["perdidas"] += 1

def extraer_diccionario_datos_corregido(lista_cruda):
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

def robot_scalping_autosuficiente_xtb():
    global stats, hora_apertura_orden, operacion_ganada
    global maximo_rendimiento_alcanzado, trailing_activado, tiempo_ultimo_cierre
    
    opciones = Options()
    opciones.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    
    try:
        print(" [ALGO] Intentando enlazar con Chrome en el puerto 9222...")
        driver = webdriver.Chrome(options=opciones)
        
        driver.set_page_load_timeout(3)
        driver.implicitly_wait(0.1)
        
        comando_limpiar = 'cls' if os.name == 'nt' else 'clear'
        
        bloqueo_orden_vela = False
        minuto_ultima_orden = ""
        motivo_cierre_stats = "N/D"

        os.system(comando_limpiar)
        print("=" * 75)
        print(" [ALGO] ¡Conectado con éxito a xStation!")
        print(" FIXED MAPEO: Solucionado error de matriz anidada en la impresión de Instrumento.")
        print("=" * 75)
        time.sleep(1)
        
        while True:
            try:
                # 1. Capturar componentes comerciales de la pestaña visible
                todos_los_sell = driver.find_elements(By.CSS_SELECTOR, "#sellButton, [id='sellButton']")
                todos_los_buy = driver.find_elements(By.CSS_SELECTOR, "#buyButton, [id='buyButton']")
                todos_los_lotes = driver.find_elements(By.CSS_SELECTOR, "span.ui-spinner-amount-value, input[name='stepperInput'], [id='volumeInput']")
                
                precio_sell_visible = "0.00"
                precio_buy_visible = "0.00"
                lote_visible = "No detectado"
                
                macd_histograma = "No detectado"
                texto_tendencia = "Esperando datos..."
                rsi_valor = "No detectado"
                num_rsi_puro = None
                adx_valor = "No detectado"
                num_adx_puro = None
                
                boton_compra_real, boton_venta_real = None, None

                for boton in todos_los_sell:
                    if boton.is_displayed() and boton.is_enabled():
                        precio_sell_visible = boton.get_attribute("textContent").strip()
                        boton_venta_real = boton
                        break
                for boton in todos_los_buy:
                    if boton.is_displayed() and boton.is_enabled():
                        precio_buy_visible = boton.get_attribute("textContent").strip()
                        boton_compra_real = boton
                        break
                for vol in todos_los_lotes:
                    if vol.is_displayed():
                        texto_vol = vol.get_attribute("value") if vol.tag_name == "input" else vol.get_attribute("textContent").strip()
                        if texto_vol:
                            lote_visible = texto_vol.replace("USD", "").strip()
                            break

                # 2. Escaneo de los indicadores técnicos
                xpath_indicadores = "//*[contains(@class, 'indicator-value-label')]"
                elementos_indicadores = driver.find_elements(By.XPATH, xpath_indicadores)

                for elemento in elementos_indicadores:
                    try:
                        if elemento.is_displayed():
                            contenedor_padre = elemento.find_element(By.XPATH, "./..")
                            texto_identificador = contenedor_padre.get_attribute("textContent").upper()
                            contenido = elemento.get_attribute("title") or elemento.get_attribute("textContent")
                            if not contenido: continue
                            
                            contenido_limpio = contenido.replace(",", ".")
                                
                            if "MACD" in texto_identificador and "." in contenido_limpio:
                                partes_macd = [p.strip() for p in contenido_limpio.split(".")]
                                if len(partes_macd) >= 2:
                                    decimales_macd = re.findall(r'-?\d+\.\d+|-?\d+', contenido_limpio)
                                    num_linea = float(decimales_macd[0])
                                    num_senal = float(decimales_macd[1])
                                    valor_hist = num_linea - num_senal
                                    macd_histograma = f"{valor_hist:.2f}"
                                    texto_tendencia = "🔴 A LA BAJA" if valor_hist < 0 else "🟢 AL ALZA"

                                    texto_macd = (
                                        f"📉 HISTOGRAMA MACD\n"
                                        f"  ───────────────────────────────────\n"
                                        f"   Línea venta  : {num_senal}\n"
                                        f"   Línea compra : {num_linea}\n"
                                        f"   Diferencia   : {macd_histograma}\n"
                                        f"   Tendencia    : {texto_tendencia}"                                        
                                    )
                            elif "RSI" in texto_identificador:
                                decimales_rsi = re.findall(r'-?\d+\.\d+|-?\d+', contenido_limpio)
                                if decimales_rsi:
                                    num_rsi_puro = float(decimales_rsi[-1])
                                    if num_rsi_puro >= RSI_SOBRECOMPRA: rsi_valor = f"{num_rsi_puro:.2f} ⚠️"
                                    elif num_rsi_puro <= RSI_SOBREVENTA: rsi_valor = f"{num_rsi_puro:.2f} ⚠️"
                                    else: rsi_valor = f"{num_rsi_puro:.2f}"
                            elif "ADX" in texto_identificador:
                                decimales_adx = re.findall(r'-?\d+\.\d+|-?\d+', contenido_limpio)
                                if decimales_adx:
                                    num_adx_puro = float(decimales_adx[0])
                                    if num_adx_puro >= ADX_TENDENCIA_FUERTE: 
                                        adx_valor = f"{num_adx_puro:.2f} 🔥 (Tendencia Fuerte)"
                                    else: 
                                        adx_valor = f"{num_adx_puro:.2f} 💤 (Mercado Lateral)"
                    except: continue

                if minuto_ultima_orden != time.strftime('%M'):
                    bloqueo_orden_vela = False

                # ===========================================================================
                # 3 y 4. ESCANEO CON PERFORADOR SHADOW DOM Y GESTIÓN DE MATRICES
                # ===========================================================================
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
                
                operacion_activa = total_posiciones > 0
                ejecutar_cierre = False
                beneficio_neto = None
                reporte_trailing_consola = "Esperando activación (% mínimo no alcanzado)"
                reporte_stop_loss_consola = "\nNinguna posición abierta"

                if operacion_activa and len(operaciones_detalles) > 0:
                    if hora_apertura_orden is None:
                        hora_apertura_orden = time.time()
                        maximo_rendimiento_alcanzado = -999.0  
                        trailing_activado = False
                    
                    # Llamamos a la extracción con la matriz limpia
                    om = extraer_diccionario_datos_corregido(operaciones_detalles)
                    
                    # --- FILTRADO DE SEGURIDAD EXTREMA DEL % ---
                    try:
                        texto_porcentaje = str(om["Beneficio %"]).replace("%", "").replace(" ", "").replace(",", ".")
                        match_pct = re.search(r'([-+]?\d+\.\d+|-?\d+)', texto_porcentaje)
                        rendimiento_actual = float(match_pct.group(1)) if match_pct else 0.0
                    except:
                        rendimiento_actual = 0.0
                    
                    # ─── LÓGICA DE CONTROL POR % NATIVO: STOP LOSS DIRECTO ───
                    reporte_stop_loss_consola = (
                        f"🔴 FIJADO: {PORCENTAJE_STOP_LOSS:.1f}%\n"
                        f"🔴 ACTUAL: {rendimiento_actual:+.2f}%"
                    )
                    
                    if rendimiento_actual <= PORCENTAJE_STOP_LOSS:
                        motivo_cierre_stats = f"Loss ({rendimiento_actual:+.2f}%)"
                        operacion_ganada = False
                        ejecutar_cierre = True
                    
                    # ─── LÓGICA DE CONTROL POR % NATIVO: TRAILING STOP ───
                    if rendimiento_actual > maximo_rendimiento_alcanzado:
                        maximo_rendimiento_alcanzado = rendimiento_actual
                        
                    if maximo_rendimiento_alcanzado >= PORCENTAJE_ACTIVACION_TRAILING:
                        trailing_activado = True
                        
                    if trailing_activado:                        
                        caida_desde_pico = maximo_rendimiento_alcanzado - rendimiento_actual
                        reporte_trailing_consola = (
                            f"🔥 ACTIVADO\n"
                            f"🔥 MAXIMO RENDIMIENTO ALCANZADO: +{maximo_rendimiento_alcanzado:.2f}%\n"
                            f"🔥 CAIDA DESDE EL ULTIMO PICO: {caida_desde_pico:.2f}%\n"
                            f"🔥 % ACTIVACION DE TRAILING: {PORCENTAJE_ACTIVACION_TRAILING}%\n"
                            f"🔥 % TRAILING STOP: {DISTANCIA_TRAILING_MAXIMA}%"
                        )
                        
                        if caida_desde_pico >= DISTANCIA_TRAILING_MAXIMA:
                            motivo_cierre_stats = f"Win Trailing. Rendimiento actual: {rendimiento_actual:+.2f}%. Ultimo pico de rendimiento: {caida_desde_pico:+.2f}%."
                            ejecutar_cierre = True
                            operacion_ganada = True
                    else:
                        reporte_trailing_consola = f"💤 Inactivo (% Actual: {rendimiento_actual:+.2f}% / Requerido: {PORCENTAJE_ACTIVACION_TRAILING}%)"

                    icono_beneficio = "🟢" if rendimiento_actual >= 0 else "🔴"
                    
                    lucro_flotante_visible = (
                        f"📌 [OPERACIÓN #1]\n"
                        f"  ───────────────────────────────────\n"
                        f"   💱 Instrumento:      {om['Activo']} ({om['Tipo']})\n"
                        f"   📦 Volumen (Lotes):  {om['Volumen']}\n"
                        f"   💼 Valor Contrato:   {om['Valor Contrato']}\n"
                        f"   🚀 Precio Apertura:  {om['Precio Apertura']}\n"
                        f"   📊 Precio Actual:    {om['Precio Actual']}\n"
                        f"   {icono_beneficio} Beneficio Neto:   {om['Beneficio Neto']} ({om['Beneficio %']})"
                    )

                    beneficio_neto =  float(om['Beneficio Neto'])

                    if beneficio_neto >= TAKE_PROFIT_MONETARIO:
                        ejecutar_cierre = True
                        operacion_ganada = True
                        motivo_cierre_stats = f"Take Profit Alcanzado (+${beneficio_neto:.2f})"
                else:
                    lucro_flotante_visible = "Sin operaciones abiertas"
                    hora_apertura_orden = None

                # 5. Ejecución automática de operaciones bajo confluencia estricta
                if num_rsi_puro is not None and num_adx_puro is not None and not bloqueo_orden_vela and not operacion_activa:
                    # 🔥 CONTROL DE ENFRIAMIENTO TRAS CIERRE
                    if time.time() - tiempo_ultimo_cierre < SEGUNDOS_ENFRIAMIENTO:
                        continue # Salta la iteración si no ha pasado el tiempo mínimo
    
                    if num_adx_puro >= ADX_TENDENCIA_FUERTE:
                        if num_rsi_puro <= RSI_SOBREVENTA and boton_compra_real:
                            boton_compra_real.click()
                            os.system('say "Comprando" &')
                            bloqueo_orden_vela = True
                            minuto_ultima_orden = time.strftime('%M')
                            hora_apertura_orden = time.time()
                        elif num_rsi_puro >= RSI_SOBRECOMPRA and boton_venta_real:
                            boton_venta_real.click()
                            os.system('say "Vendiendo" &')
                            bloqueo_orden_vela = True
                            minuto_ultima_orden = time.strftime('%M')
                            hora_apertura_orden = time.time()

                # ===========================================================================
                # 6. MÓDULO DE GATILLADO Y ACCIÓN DE CIERRE DIRECTO
                # ===========================================================================
                if ejecutar_cierre and operacion_activa:
                    try:
                        driver.execute_script("if(window.ultimoBotonCierre) { window.ultimoBotonCierre.click(); }")
                        os.system(f'say "Posición cerrada por {motivo_cierre_stats}" &')
                        historico_cuenta.append(beneficio_neto)

                        # 🔥 REGISTRAR EL TIEMPO EXACTO DEL CIERRE
                        tiempo_ultimo_cierre = time.time()

                        hora_apertura_orden = None
                        trailing_activado = False
                        maximo_rendimiento_alcanzado = 0.0
                        operacion_ganada = None

                        # Sincronizador de estadísticas con lectura de resultados reales
                        if beneficio_neto > 0:
                            actualizar_estadisticas_cierre(True)
                        else:
                            actualizar_estadisticas_cierre(False)

                        time.sleep(5)
                    except Exception as error_ejecucion:
                        print(f" [-] Error crítico enviando el comando de click: {error_ejecucion}")

                # 7. CÁLCULO EXCLUSIVO DEL WIN RATE
                win_rate = (stats["ganadas"] / stats["totales"] * 100) if stats["totales"] > 0 else 0.0

                # 8. IMPRESIÓN ACTUALIZADA EN CONSOLA
                os.system(comando_limpiar)
                print("=" * 75)
                print(f" ROBOT OPERATIVO AUTOMÁTICO XTB | MONITOR DE RIESGO % NATIVO FIXED")
                print(f" Servidor activo: {time.strftime('%H:%M:%S')} | Lote: {lote_visible}")
                print("=" * 75)
                print(f" 🔴 PRECIO ASK (SELL) : {precio_sell_visible}")
                print(f" 🟢 PRECIO BID (BUY)  : {precio_buy_visible}")
                print("-" * 75)
                print(f"{texto_macd}")
                print("-" * 75)
                print(f" ⚛️  OSCILADOR RSI      : {rsi_valor}")
                print("-" * 75)
                print(f" 📊 IMPULSO ADX : {adx_valor}")
                print("-" * 75)
                print(f"{lucro_flotante_visible}")
                print("-" * 75)
                print(f"🧭 TRAILING STOP : {reporte_trailing_consola}")
                print("-" * 75)
                print(f"🧭 STOP LOSS ACTUAL")
                print(f"{reporte_stop_loss_consola}")
                print("-" * 75)
                print(f"💰 TAKE PROFIT : {TAKE_PROFIT_MONETARIO}")
                print("-" * 75)
                print(f"🚦 FILTRO ENTRADAS : {'🔒 BLOQUEADO (Operación detectada)' if operacion_activa else '🔓 EN ESPERA DE SEÑAL'}")
                print("=" * 75)
                print(" 📊 CUADRO DE ESTADÍSTICAS Y MÉTRICAS DE EFECTIVIDAD (HOY):")
                print(f"    └ Operaciones Ganadas  🟢 : {stats['ganadas']}")
                print(f"    └ Operaciones Perdidas 🔴 : {stats['perdidas']}")
                print(f"    └ Total Ejecutadas     ⚡ : {stats['totales']}")
                print(f"    └ Porcentaje de Acierto🎯 : {win_rate:.1f}% Win Rate")
                print(f"    └ Histórico de la cuenta  : {historico_cuenta}")
                print(f"    └ Ultimo cierre           : {motivo_cierre_stats}")
                print("=" * 75)
                print(" Presiona CTRL + C en la terminal para apagar el monitor.")
                        
            except Exception as e_bucle:
                time.sleep(0.1)
                
            time.sleep(0.1)
            
    except Exception as e:
        print(f"[-] Error crítico de enlace inicial: {e}")

if __name__ == "__main__":
    try:
        robot_scalping_autosuficiente_xtb()
    except KeyboardInterrupt:
        print("\n\n[!] Sistema apagado de forma segura.")
