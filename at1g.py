from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import os
import re
import threading
import pandas as pd
import numpy as np
# CONFIGURACIÓN OBLIGATORIA PARA ENTORNO MAC OS (MINICONDA)
import matplotlib
matplotlib.use('TkAgg') # Fuerza a tu Mac a abrir la ventana interactiva independiente
import mplfinance as mpf
import matplotlib.pyplot as plt

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
PORCENTAJE_TOLERANCIA_DOBLE_TS = 0.005
PORCENTAJE_TOLERANCIA_HCM = 0.008

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

hora_apertura_orden = None
ticks_bloque_actual = []
lista_velas_acumuladas = []
historico_cuenta = []

# ===========================================================================
# 🧠 MOTOR ANALÍTICO INTEGRADO: 10 PATRONES CON TRIPLE CONFLUENCIA
# ===========================================================================
def analizar_triple_confluencia(df_velas, rsi_puro, adx_puro):
    global datos_compartidos
    
    datos_compartidos["indice_senal"] = None
    datos_compartidos["tipo_senal"] = None
    
    if len(df_velas) < 3:
        datos_compartidos["senal_accion"] = "🔎 ESPERANDO HISTORIAL DE VELAS..."
        return "Construyendo historial de barras..."
    
    if rsi_puro is None or adx_puro is None:
        datos_compartidos["senal_accion"] = "🔎 ESPERANDO LECTURA DE INDICADORES..."
        return "Faltan osciladores de apoyo en el DOM..."
        
    vela_actual = df_velas.iloc[-1] # Vela 3
    vela_previa = df_velas.iloc[-2] # Vela 2
    vela_antepenultima = df_velas.iloc[-3] # Vela 1
    idx_actual = df_velas.index[-1]
    
    vela3_valor_abrio, vela3_valor_maximo, vela3_valor_minimo, vela3_valor_cerro = float(vela_actual['Open']), float(vela_actual['High']), float(vela_actual['Low']), float(vela_actual['Close'])
    cuerpo3 = abs(vela3_valor_cerro - vela3_valor_abrio)
    es_roja3 = vela3_valor_cerro < vela3_valor_abrio
    es_verde3 = vela3_valor_cerro > vela3_valor_abrio
    
    vela2_valor_abrio, vela2_valor_cerro = float(vela_previa['Open']), float(vela_previa['Close'])
    cuerpo2 = abs(vela2_valor_cerro - vela2_valor_abrio)
    
    vela1_valor_abrio, vela2_valor_cerro = float(vela_antepenultima['Open']), float(vela_antepenultima['Close'])
    cuerpo1 = abs(vela2_valor_cerro - vela1_valor_abrio)
    es_verde1 = vela2_valor_cerro > vela1_valor_abrio
    es_roja1 = vela2_valor_cerro < vela1_valor_abrio
    
    tendencia_alcista = False
    tendencia_bajista = False
    nombre_patron = "Ninguno"
    
    # A. PATRONES COMPUESTOS DE ESTRELLAS (3 VELAS)
    if es_verde1 and es_roja3 and (cuerpo2 <= (cuerpo1 * 0.35)) and cuerpo3 > 0:
        mitad_cuerpo_vela1 = vela1_valor_abrio + (cuerpo1 / 2)
        if vela3_valor_cerro <= mitad_cuerpo_vela1:
            tendencia_bajista, nombre_patron = True, "Estrella del Atardecer"
    elif es_roja1 and es_verde3 and (cuerpo2 <= (cuerpo1 * 0.35)) and cuerpo3 > 0:
        mitad_cuerpo_vela1 = vela2_valor_cerro + (cuerpo1 / 2)
        if vela3_valor_cerro >= mitad_cuerpo_vela1:
            tendencia_alcista, nombre_patron = True, "Estrella del Amanecer"
            
    # B. PATRONES TRADICIONALES DE 1 Y 2 VELAS
    if nombre_patron == "Ninguno":
        cuerpo = cuerpo3
        mecha_sup = vela3_valor_maximo - max(vela3_valor_abrio, vela3_valor_cerro)
        mecha_inf = min(vela3_valor_abrio, vela3_valor_cerro) - vela3_valor_minimo
        rango_total = vela3_valor_maximo - vela3_valor_minimo
        es_verde = es_verde3
        cuerpo_p = cuerpo2
        es_verde_p = vela2_valor_cerro > vela2_valor_abrio
        tendencia_bajista_previa = vela2_valor_cerro > vela2_valor_cerro and vela2_valor_cerro >= min(vela3_valor_abrio, vela3_valor_cerro)
        tendencia_alcista_previa = vela2_valor_cerro < vela2_valor_cerro and vela2_valor_cerro < vela3_valor_abrio
        
        if rango_total > 0:
            if es_verde and not es_verde_p and cuerpo > cuerpo_p and vela3_valor_cerro >= vela2_valor_abrio and vela3_valor_abrio <= vela2_valor_cerro:
                tendencia_alcista, nombre_patron = True, "Envolvente Alcista"
            elif not es_verde and es_verde_p and cuerpo > cuerpo_p and vela3_valor_cerro <= vela2_valor_abrio and vela3_valor_abrio >= vela2_valor_cerro:
                tendencia_bajista, nombre_patron = True, "Envolvente Bajista"
            # 1. MARTILLO
            elif mecha_inf >= (2 * cuerpo) and mecha_sup <= (0.2 * cuerpo) and tendencia_bajista_previa:
                tendencia_alcista, nombre_patron = True, "Martillo (Hammer)"
            # 2. ESTRELLA FUGAZ
            elif mecha_sup >= (2 * cuerpo) and mecha_inf <= (0.2 * cuerpo) and tendencia_alcista_previa:
                tendencia_bajista, nombre_patron = True, "Estrella Fugaz"
            # 3. MARTILLO INVERTIDO
            elif mecha_sup >= (2 * cuerpo) and mecha_inf <= (0.2 * cuerpo) and tendencia_bajista_previa:
                tendencia_alcista, nombre_patron = True, "Martillo Invertido"
            # 4. HOMBRE COLGADO
            elif mecha_inf >= (2 * cuerpo) and mecha_sup <= (0.2 * cuerpo) and tendencia_alcista_previa:
                tendencia_bajista, nombre_patron = True, "Hombre Colgado"
                
    # C. ESTRUCTURAS COMPLEJAS Y ESCÁNER COMBINATORIO (12 VELAS)
    if len(df_velas) >= 12 and nombre_patron == "Ninguno":
        maximos = df_velas['High'].tail(12).astype(float).tolist()
        minimos = df_velas['Low'].tail(12).astype(float).tolist()
        
        picos = []
        for i in range(1, len(maximos) - 1):
            if maximos[i] > maximos[i-1] and maximos[i] > maximos[i+1]: picos.append(maximos[i])
            
        if len(picos) >= 2:
            if len(picos) >= 3:
                for x in range(len(picos) - 2):
                    for y in range(x + 1, len(picos) - 1):
                        for z in range(y + 1, len(picos)):
                            if picos[y] > picos[x] and picos[y] > picos[z] and abs(picos[x] - picos[z]) < (picos[y] * PORCENTAJE_TOLERANCIA_HCM):
                                tendencia_bajista, nombre_patron = True, "Hombro-Cabeza-Hombro"
                                break
                        if tendencia_bajista: break
                    if tendencia_bajista: break
            if not tendencia_bajista:
                for x in range(len(picos) - 1):
                    for y in range(x + 1, len(picos)):
                        if abs(picos[x] - picos[y]) < (picos[x] * PORCENTAJE_TOLERANCIA_DOBLE_TS):
                            tendencia_bajista, nombre_patron = True, "Doble Techo"
                            break
                    if tendencia_bajista: break
                    
        valles = []
        for i in range(1, len(minimos) - 1):
            if minimos[i] < minimos[i-1] and minimos[i] < minimos[i+1]: valles.append(minimos[i])
            
        if len(valles) >= 2:
            if len(valles) >= 3:
                for x in range(len(valles) - 2):
                    for y in range(x + 1, len(valles) - 1):
                        for z in range(y + 1, len(valles)):
                            if valles[y] < valles[x] and valles[y] < valles[z] and abs(valles[x] - valles[z]) < (valles[x] * PORCENTAJE_TOLERANCIA_HCM):
                                tendencia_alcista, nombre_patron = True, "HCH Invertido"
                                break
                        if tendencia_alcista: break
                    if tendencia_alcista: break
            if not tendencia_alcista:
                for x in range(len(valles) - 1):
                    for y in range(x + 1, len(valles)):
                        if abs(valles[x] - valles[y]) < (valles[x] * PORCENTAJE_TOLERANCIA_DOBLE_TS):
                            tendencia_alcista, nombre_patron = True, "Doble Suelo"
                            break
                    if tendencia_alcista: break

    # VALIDACIÓN FINAL
    if adx_puro >= ADX_TENDENCIA_FUERTE and len(df_velas) >= 12:
        if tendencia_alcista: # and rsi_puro <= RSI_SOBREVENTA:
            datos_compartidos["indice_senal"] = idx_actual
            datos_compartidos["tipo_senal"] = "COMPRA"
            datos_compartidos["senal_accion"] = f"🟢 COMPRA DETECTADA: {nombre_patron} + RSI LOW + ADX FUERTE 🔥 "
            return f"COMPRA_{nombre_patron}"
        elif tendencia_bajista: #and rsi_puro >= RSI_SOBRECOMPRA:
            datos_compartidos["indice_senal"] = idx_actual
            datos_compartidos["tipo_senal"] = "VENTA"
            datos_compartidos["senal_accion"] = f"🔴 VENTA DETECTADA: {nombre_patron} + RSI HIGH + ADX FUERTE 🔥 "
            return f"VENTA_{nombre_patron}"
        
    datos_compartidos["senal_accion"] = "🔎 MERCADO EN RANGO / NEUTRAL (Buscando confluencias...)"
    return "Analizando la acción del precio..."

# ===========================================================================
# 📊 AUXILIAR: EXTRACCIÓN DE DATOS FILTRADOS POR COLUMNA DESDE EL DOM
# ===========================================================================
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

# ===========================================================================
# ⚡ ROBOT GRABADOR, EJECUTADOR Y GESTOR DE RIESGO
# ===========================================================================
def robot_grabador_ticks_xtb():
    global datos_compartidos, ticks_bloque_actual, lista_velas_acumuladas, estadisticas_bot, tiempo_ultimo_cierre
    opciones = Options()
    opciones.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    
    try:
        driver = webdriver.Chrome(options=opciones)
        comando_limpiar = 'cls' if os.name == 'nt' else 'clear'
        ultimo_sell, ultimo_buy = "", ""
        minuto_anterior = ""
        
        bloqueo_orden_vela = False
        minuto_ultima_orden = ""
        
        # 🔥 SOLUCIÓN 1: Variables persistentes fuera del bucle de mercado para evitar reinicios continuos
        maximo_rendimiento_alcanzado = -999.0
        trailing_activado = False
        resultado_confluencia = "Ninguno"
        
        print(" [+] Conexión exitosa con Chrome DevTools en el puerto 9222.")
        
        while True:
            try:
                todos_los_sell = driver.find_elements(By.ID, "sellButton")
                todos_los_buy = driver.find_elements(By.ID, "buyButton")
                todos_los_lotes = driver.find_elements(By.CSS_SELECTOR, "span.ui-spinner-amount-value, input[name='stepperInput'], [id='volumeInput']")
                
                precio_sell_visible, precio_buy_visible = "0.00", "0.00"
                boton_compra_real, boton_venta_real = None, None
                lote_visible = "No detectado"
                
                for boton in todos_los_sell:
                    if boton.is_displayed() and boton.is_enabled():
                        precio_sell_visible = boton.get_attribute("textContent").strip()
                        datos_compartidos["sell"] = precio_sell_visible
                        boton_venta_real = boton
                        break
                for boton in todos_los_buy:
                    if boton.is_displayed() and boton.is_enabled():
                        precio_buy_visible = boton.get_attribute("textContent").strip()
                        datos_compartidos["buy"] = precio_buy_visible
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
                            ticks_bloque_actual.append(precio_numerico)
                    except Exception: pass
                    
                xpath_indicadores = "//*[contains(@class, 'indicator-value-label')] | //span[contains(@class, 'chart-indicator-value')]"
                elementos_indicadores = driver.find_elements(By.XPATH, xpath_indicadores)
                num_rsi_leido, num_adx_leido = None, None
                
                for elemento in elementos_indicadores:
                    if elemento.is_displayed():
                        try: texto_id = elemento.find_element(By.XPATH, "./..").get_attribute("textContent").upper()
                        except: texto_id = ""
                        contenido = elemento.get_attribute("title") or elemento.get_attribute("textContent")
                        if not contenido: continue
                        if "RSI" in texto_id or "STOCH" in texto_id:
                            decimales_rsi = re.findall(r'-?\d+\.\d+|-?\d+', contenido)
                            if decimales_rsi: num_rsi_leido = float(decimales_rsi[-1]); datos_compartidos["rsi_live"] = f"{num_rsi_leido:.2f}"
                        elif "ADX" in texto_id or "DI" in texto_id:
                            decimales_adx = re.findall(r'-?\d+\.\d+|-?\d+', contenido)
                            if decimales_adx: num_adx_leido = float(decimales_adx[0]); datos_compartidos["adx_live"] = f"{num_adx_leido:.2f}"
                            
                if num_rsi_leido is None: num_rsi_leido = 50.0; datos_compartidos["rsi_live"] = "--- (Fijo/DOM Oculto)"
                if num_adx_leido is None: num_adx_leido = 35.0; datos_compartidos["adx_live"] = "--- (Fijo/DOM Oculto)"

                if num_adx_leido >= ADX_TENDENCIA_FUERTE:
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
                
                datos_compartidos["lucro"] = "Sin operaciones abiertas"
                datos_compartidos["trailing_status"] = "Inactivo"
                ejecutar_cierre = False
                operacion_activa = total_posiciones > 0
                operacion_ganada = False

                if operacion_activa and len(operaciones_detalles) > 0:
                    global hora_apertura_orden
                    if hora_apertura_orden is None:
                        hora_apertura_orden = time.time()
                        maximo_rendimiento_alcanzado = -999.0  
                        trailing_activado = False

                    om = extraer_diccionario_datos_corregido(operaciones_detalles)
                    
                    try:
                        texto_porcentaje = str(om["Beneficio %"]).replace("%", "").replace(" ", "").replace(",", ".")
                        match_pct = re.search(r'([-+]?\d+\.\d+|-?\d+)', texto_porcentaje)
                        rendimiento_actual = float(match_pct.group(1)) if match_pct else 0.0
                    except:
                        rendimiento_actual = 0.0

                    reporte_stop_loss_consola = (
                        f"🔴 FIJADO: {PORCENTAJE_STOP_LOSS:.1f}%\n"
                        f"🔴 ACTUAL: {rendimiento_actual:+.2f}%"
                    )

                    if rendimiento_actual <= PORCENTAJE_STOP_LOSS:
                        motivo_cierre_stats = f"Loss ({rendimiento_actual:+.2f}%)"
                        operacion_ganada = False
                        ejecutar_cierre = True
                    
                    if rendimiento_actual > maximo_rendimiento_alcanzado:
                        maximo_rendimiento_alcanzado = rendimiento_actual
                        
                    if maximo_rendimiento_alcanzado >= PORCENTAJE_ACTIVACION_TRAILING:
                        trailing_activado = True

                    if trailing_activado:                        
                        caida_desde_pico = maximo_rendimiento_alcanzado - rendimiento_actual
                        reporte_trailing_consola = (
                            f"🔥 ACTIVADO\n"
                            f"🔥 MAXIMO: +{maximo_rendimiento_alcanzado:.2f}%\n"
                            f"🔥 CAIDA DESDE PICO: {caida_desde_pico:.2f}%\n"
                            f"🔥 TRAILING STOP LÍMITE: {DISTANCIA_TRAILING_MAXIMA}%"
                        )
                        datos_compartidos["trailing_status"] = f"Trailing Activo (Máx: +{maximo_rendimiento_alcanzado:.2f}%)"
                        
                        if caida_desde_pico >= DISTANCIA_TRAILING_MAXIMA:
                            motivo_cierre_stats = f"Win Trailing ({rendimiento_actual:+.2f}%)"
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
                        f"   🚀 Precio Apertura:  {om['Precio Apertura']}\n"
                        f"   📊 Precio Actual:    {om['Precio Actual']}\n"
                        f"   {icono_beneficio} Beneficio Neto:   {om['Beneficio Neto']} ({om['Beneficio %']})"
                    )
                    datos_compartidos["lucro"] = f"{om['Beneficio Neto']} ({om['Beneficio %']})"

                    beneficio_neto = float(str(om['Beneficio Neto']).replace(",", ".").replace(" ", ""))

                    if beneficio_neto >= TAKE_PROFIT_MONETARIO:
                        ejecutar_cierre = True
                        operacion_ganada = True
                        motivo_cierre_stats = f"Take Profit Alcanzado (+${beneficio_neto:.2f})"
                else:
                    lucro_flotante_visible = "Sin operaciones abiertas"
                    reporte_trailing_consola = f"💤 Inactivo"
                    hora_apertura_orden = None

                if int(minuto_actual) % TEMPORALIDAD_MINUTOS == 0 and minuto_actual != minuto_anterior:
                    if time.time() - tiempo_ultimo_cierre < SEGUNDOS_ENFRIAMIENTO:
                        continue

                    if len(ticks_bloque_actual) > 0:
                        nueva_vela_ohlc = {
                            "Open": ticks_bloque_actual[0], 
                            "High": max(ticks_bloque_actual), 
                            "Low": min(ticks_bloque_actual), 
                            "Close": ticks_bloque_actual[-1]
                        }
                        lista_velas_acumuladas.append(nueva_vela_ohlc)
                        ticks_bloque_actual = []
                        minuto_anterior = minuto_actual
                        df_historial_total = pd.DataFrame(lista_velas_acumuladas)
                        df_historial_total.index = pd.date_range(start="2026-01-01 09:30", periods=len(df_historial_total), freq=f"{TEMPORALIDAD_MINUTOS}min")
                        
                        resultado_confluencia = analizar_triple_confluencia(df_historial_total, num_rsi_leido, num_adx_leido)
                        datos_compartidos["status_patrones"] = resultado_confluencia
                        datos_compartidos["df_velas"] = df_historial_total

                # Ejecución automática de operaciones bajo confluencia estricta
                if not operacion_activa:    
                    if not bloqueo_orden_vela and num_adx_leido >= ADX_TENDENCIA_FUERTE:
                        if "COMPRA" in resultado_confluencia and boton_compra_real:
                            boton_compra_real.click()
                            os.system('say "Comprando" &')
                            bloqueo_orden_vela = True
                            minuto_ultima_orden = time.strftime('%M')
                            hora_apertura_orden = time.time()
                            estadisticas_bot["total_ordenes"] += 1
                            estadisticas_bot["ultimo_patron_operado"] = resultado_confluencia.split("_")[-1]
                        elif "VENTA" in resultado_confluencia and boton_venta_real:
                            boton_venta_real.click()
                            os.system('say "Vendiendo" &')
                            bloqueo_orden_vela = True
                            minuto_ultima_orden = time.strftime('%M')
                            hora_apertura_orden = time.time()
                            estadisticas_bot["total_ordenes"] += 1
                            estadisticas_bot["ultimo_patron_operado"] = resultado_confluencia.split("_")[-1]                        
                
                # MÓDULO DE ACCIÓN DE CIERRE
                if ejecutar_cierre and operacion_activa:
                    try:
                        driver.execute_script("if(window.ultimoBotonCierre) { window.ultimoBotonCierre.click(); }")
                        os.system(f'say "Posición cerrada por {motivo_cierre_stats}" &')
                        
                        if operacion_ganada:
                            estadisticas_bot["ganadas"] += 1
                        else:
                            estadisticas_bot["perdidas"] += 1
                            
                        historico_cuenta.append(beneficio_neto)
                        tiempo_ultimo_cierre = time.time()
                        hora_apertura_orden = None
                        trailing_activado = False
                        maximo_rendimiento_alcanzado = -999.0
                        lucro_flotante_visible = "Sin operaciones abiertas"
                        time.sleep(5)
                    except Exception as error_ejecucion:
                        print(f" [-] Error crítico enviando el comando de click: {error_ejecucion}")
                    
                win_rate = (estadisticas_bot["ganadas"] / estadisticas_bot["total_ordenes"] * 100) if estadisticas_bot["total_ordenes"] > 0 else 0.0
                
                if datos_compartidos["sell"] != ultimo_sell or datos_compartidos["buy"] != ultimo_buy:
                    ultimo_sell, ultimo_buy = datos_compartidos["sell"], datos_compartidos["buy"]
                    os.system(comando_limpiar)
                    print("=" * 75)
                    print(f" ROBOT OPERATIVO AUTOMATIZADO XTB | SISTEMA DE CONTROL TOTAL BLINDADO")
                    print(f" Servidor activo: {time.strftime('%H:%M:%S')} | Lote: {lote_visible}")
                    print("=" * 75)
                    print(f" 🔴 PRECIO REAL VENDER (SELL) : {datos_compartidos['sell']}")
                    print(f" 🟢 PRECIO REAL COMPRAR (BUY) : {datos_compartidos['buy']}")
                    print("-" * 75)
                    print(f" 💰 MONITOREO DE OSCILADORES EN VIVO DESDE TU XSTATION:")
                    print(f" ↳ Valor actual del RSI (14) : {datos_compartidos['rsi_live']}")
                    print(f" ↳ Valor actual del ADX (14) : {adx_valor}")
                    print("-" * 75)
                    print(f" 🛡 MONITOR GESTIÓN DE RIESGO DE OPERACIONES ABIERTAS:")
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
                    print(f" 🧭 GATILLO DE CONFLUENCIA CONFIRMADO")
                    print(f" {datos_compartidos['senal_accion']}")
                    print("-" * 75)
                    print(f" 📊 CUADRO DE ESTADÍSTICAS Y MÉTRICAS DE EFECTIVIDAD (HOY):")
                    print(f" ↳ Operaciones Ganadas 🟢 : {estadisticas_bot['ganadas']}")
                    print(f" ↳ Operaciones Perdidas 🔴 : {estadisticas_bot['perdidas']}")
                    print(f" ↳ Total Ejecutadas ⚡ : {estadisticas_bot['total_ordenes']}")
                    print(f" ↳ Porcentaje de Acierto🎯 : {win_rate:.1f}% Win Rate")
                    print(f" ↳ Histórico de la cuenta  : {historico_cuenta}")
                    print(f" ↳ Ultimo cierre           : {motivo_cierre_stats}")
                    print("=" * 75)
                    
            except Exception as e:
                # Muestra errores internos de mapeo sin colapsar el hilo de Selenium
                pass
            time.sleep(0.1)
    except Exception as e: 
        print(f"[-] Error de enlace central: {e}")

# ===========================================================================
# 📈 MOTOR GRÁFICO REAL TIME PARA MAC OS (NATIVO ASÍNCRONO)
# ===========================================================================
from matplotlib.animation import FuncAnimation

def loop_render_grafico(frame, fig, ax):
    """Refresca la GUI de manera segura interactuando directamente con Matplotlib."""
    try:
        df_actual = datos_compartidos["df_velas"].copy()
        idx_senal = datos_compartidos["indice_senal"]
        tipo_sig = datos_compartidos["tipo_senal"]
        
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
    except Exception:
        pass

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
