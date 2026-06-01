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
import configuracion.parametros as parametros
from patrones.identificar_patrones import identificar_patrones
from extraccion.velas import extraer_velas
from extraccion.datos_xtb import extraer_datos_operacion, obtener_datos_operaciones, obtener_datos_compra_venta
from ui.interfaz import ui_adx, ui_macd, ui_rsi, ui_ema, ui_trailing, ui_stop_loss, ui_operacion_activa, ui_estadisticas, ui_volumen, ui_datos_generales, ui_patrones
from archivos.seguimiento import guardar_estadistica, actualizar_ultima_operacion, actualizar_estadisticas_cierre

hora_apertura_orden = None
operacion_ganada = None
maximo_rendimiento_alcanzado = 0.0  
trailing_activado = False
bloqueo_ejecutar_orden = False
minuto_anterior = ""
minuto_ultima_orden = ""
motivo_cierre_stats = "N/D"
driver = None
comando_limpiar = None

# ===========================================================================
# ⚡ ROBOT GRABADOR, EJECUTADOR Y GESTOR DE RIESGO
# ===========================================================================
def bot_scalping():
    global datos_compartidos, lista_velas_acumuladas, estadisticas_bot, tiempo_ultimo_cierre, historico_volumen, promedio_volumen
    global promedio_volumen_sin_actual, motivo_cierre_stats, error, df_historial_total, hora_apertura_orden
    opciones = Options()
    opciones.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    
    try:
        driver = webdriver.Chrome(options=opciones)
        comando_limpiar = 'cls' if os.name == 'nt' else 'clear'
        ultimo_sell, ultimo_buy = "", ""
        minuto_anterior = ""
        
        bloqueo_ejecutar_orden = False
        minuto_ultima_orden = ""
        texto_macd = ""
        texto_volumen = ""
        valor_volumen = 0
        
        # Variables persistentes fuera del bucle de mercado para evitar reinicios continuos
        maximo_rendimiento_alcanzado = -999.0
        trailing_activado = False
        resultado_confluencia = "Ninguno"
        
        print("Conexión exitosa con Chrome DevTools en el puerto 9222.")
        
        while True:
            try:
                if minuto_ultima_orden != time.strftime('%M'):
                    bloqueo_ejecutar_orden = False
                
                minuto_actual = time.strftime('%M')                
                if minuto_anterior == "": minuto_anterior = minuto_actual

                segundo_actual = time.strftime('%H:%M:%S')
                segundo_actual_int = time.strftime('%S')
                obtener_datos_compra_venta(segundo_actual, True, driver)

                if segundo_actual != parametros.ultimo_segundo_procesado:
                    parametros.ultimo_segundo_procesado = segundo_actual
                
                if int(segundo_actual_int) - 2 >= int(parametros.penultimo_segundo_procesado):
                    parametros.ultimo_valor_volumen = parametros.valor_volumen
                    parametros.penultimo_segundo_procesado = segundo_actual_int

                texto_macd = ""
                texto_rsi = ""
                texto_adx = ""
                texto_volumen = ""
                texto_ema = ""
                        
                #xpath_indicadores = "//*[contains(@class, 'indicator-value-label')] | //span[contains(@class, 'chart-indicator-value')]"
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
                            
                            texto_macd = ui_macd(parent_text_content, texto_componente, parametros.historico_macd, texto_macd)
                            texto_rsi = ui_rsi(parent_text_content, texto_componente, parametros.historico_rsi, texto_rsi)
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
                    bloqueo_ejecutar_orden = False

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
                    
                    try:
                        texto_porcentaje = str(parametros.datos_mapeados["Beneficio %"]).replace("%", "").replace(" ", "").replace(",", ".")
                        match_pct = re.search(r'([-+]?\d+\.\d+|-?\d+)', texto_porcentaje)
                        rendimiento_actual = float(match_pct.group(1)) if match_pct else 0.0
                    except:
                        rendimiento_actual = 0.0

                    # ─── LÓGICA DE CONTROL POR % NATIVO: STOP LOSS DIRECTO ───
                    texto_stop_loss = ui_stop_loss(True, rendimiento_actual)

                    if rendimiento_actual <= parametros.STOP_LOSS:
                        parametros.motivo_cierre_stats = f"Loss ({rendimiento_actual:+.2f}%)"
                        operacion_ganada = False
                        ejecutar_cierre = True
                    
                    # ─── LÓGICA DE CONTROL POR % NATIVO: TRAILING STOP ───
                    if rendimiento_actual > maximo_rendimiento_alcanzado:
                        maximo_rendimiento_alcanzado = rendimiento_actual
                        
                    if maximo_rendimiento_alcanzado >= parametros.TRAILING_STOP:
                        trailing_activado = True

                    if trailing_activado:                        
                        caida_desde_pico = maximo_rendimiento_alcanzado - rendimiento_actual
                        texto_trailing = ui_trailing(True, True, maximo_rendimiento_alcanzado, caida_desde_pico)
                        
                        if caida_desde_pico >= parametros.DISTANCIA_TRAILING_MAXIMA:
                            parametros.motivo_cierre_stats = f"Win Trailing. Rendimiento actual: {rendimiento_actual:+.2f}%. Ultimo pico de rendimiento: {caida_desde_pico:+.2f}%."
                            ejecutar_cierre = True
                            operacion_ganada = True
                    else:
                        reporte_trailing_consola = f"💤 Inactivo (% Actual: {rendimiento_actual:+.2f}% / Requerido: {parametros.TRAILING_STOP}%)"

                    texto_operacion_activa = ui_operacion_activa(True, rendimiento_actual)
                    beneficio_neto =  float(parametros.datos_mapeados['Beneficio Neto'])

                    if beneficio_neto >= parametros.TAKE_PROFIT:
                        ejecutar_cierre = True
                        operacion_ganada = True
                        parametros.motivo_cierre_stats = f"Take Profit Alcanzado (+${beneficio_neto:.2f})"

                    if beneficio_neto > 0 and float(parametros.valor_rsi) < parametros.RSI_SOBREVENTA_MACD and parametros.datos_mapeados["Operacion"] == "Venta":
                        ejecutar_cierre = True
                        operacion_ganada = True
                        motivo_cierre_stats = f"Venta alcanzó el RSI de sobreventa - Se espera retroceso (+${beneficio_neto:.2f})"
                    
                    if beneficio_neto > 0 and float(parametros.valor_rsi) > parametros.RSI_SOBRECOMPRA_MACD and parametros.datos_mapeados["Operacion"] == "Compra":
                        ejecutar_cierre = True
                        operacion_ganada = True
                        motivo_cierre_stats = f"Venta alcanzó el RSI de sobrecompra - Se espera retroceso (+${beneficio_neto:.2f})"
                else:
                    texto_operacion_activa = ui_operacion_activa(False, None)
                    hora_apertura_orden = None

                if int(minuto_actual) % parametros.TEMPORALIDAD_MINUTOS == 0 and minuto_actual != minuto_anterior:
                    if time.time() - parametros.TIEMPO_ULTIMO_CIERRE < parametros.SEGUNDOS_ENFRIAMIENTO:
                        continue

                    extraer_datos_velas()
                    resultado_confluencia = identificar_patrones(parametros.historico_velas, parametros.valor_adx)
                    minuto_anterior = minuto_actual

                    # Adicionar el valor de los indicadores
                    try:
                        valor_numerico = float(parametros.valor_macd)
                        parametros.historico_macd.append(valor_numerico)
                    except (ValueError, TypeError):
                        parametros.error = f"⚠️ No se pudo guardar: el valor del MACD no es numérico: {parametros.valor_macd}"

                    if len(parametros.historico_macd) > 2:
                        parametros.historico_macd.pop(0)

                    try:
                        valor_numerico = float(parametros.valor_rsi)
                        parametros.historico_rsi.append(valor_numerico)
                    except (ValueError, TypeError):
                        parametros.error = f"⚠️ No se pudo guardar: el valor del RSI no es numérico: {parametros.valor_rsi}"

                    if len(parametros.historico_rsi) > 2:
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

                # Ejecución automática de operaciones bajo confluencia estricta
                if not bloqueo_ejecutar_orden and not operacion_activa and parametros.valor_adx >= parametros.ADX_TENDENCIA_FUERTE:
                    # 🔥 CONTROL DE ENFRIAMIENTO TRAS CIERRE
                    if time.time() - parametros.TIEMPO_ULTIMO_CIERRE < parametros.SEGUNDOS_ENFRIAMIENTO:
                        continue # Salta la iteración si no ha pasado el tiempo mínimo

                    if "COMPRA" in resultado_confluencia and parametros.boton_comprar:
                        parametros.boton_comprar.click()
                        os.system('say "Comprando" &')
                        bloqueo_ejecutar_orden = True
                        minuto_ultima_orden = time.strftime('%M')
                        hora_apertura_orden = time.time()
                        parametros.datos_mapeados['Operacion'] = "Compra"
                        guardar_estadistica("Compra")
                        parametros.estadisticas_bot["ultimo_patron_operado"] = resultado_confluencia.split("_")[-1]
                    elif "VENTA" in resultado_confluencia and parametros.boton_vender:
                        parametros.boton_vender.click()
                        os.system('say "Vendiendo" &')
                        bloqueo_ejecutar_orden = True
                        minuto_ultima_orden = time.strftime('%M')
                        hora_apertura_orden = time.time()
                        parametros.datos_mapeados['Operacion'] = "Venta"
                        parametros.estadisticas_bot["ultimo_patron_operado"] = resultado_confluencia.split("_")[-1]
                
                # MÓDULO DE ACCIÓN DE CIERRE
                if ejecutar_cierre and operacion_activa:
                    try:
                        driver.execute_script("if(window.ultimoBotonCierre) { window.ultimoBotonCierre.click(); }")
                        os.system(f'say "Posición cerrada por {parametros.motivo_cierre_stats}" &')
                        parametros.historico_cuenta.append(beneficio_neto)

                         # 🔥 REGISTRAR EL TIEMPO EXACTO DEL CIERRE
                        parametros.TIEMPO_ULTIMO_CIERRE = time.time()

                        hora_apertura_orden = None
                        trailing_activado = False
                        maximo_rendimiento_alcanzado = 0.0
                        operacion_ganada = None

                        # Sincronizador de estadísticas con lectura de resultados reales
                        if beneficio_neto > 0:
                            actualizar_ultima_operacion(parametros.datos_mapeados, "Si", motivo_cierre_stats)
                            actualizar_estadisticas_cierre(True)
                        else:
                            actualizar_ultima_operacion(parametros.datos_mapeados, "No", motivo_cierre_stats)
                            actualizar_estadisticas_cierre(False)
                        
                    except Exception as error_ejecucion:
                        parametros.error = traceback.format_exc()
                    
                # IMPRESIÓN ACTUALIZADA EN LA CONSOLA
                os.system(comando_limpiar)
                print("=" * 75)
                print(f" ROBOT OPERATIVO AUTOMÁTICO XTB | MONITOR DE RIESGO % NATIVO FIXED")
                print(f" Servidor activo: {time.strftime('%H:%M:%S')}")
                print("=" * 75)
                print(f"{ui_datos_generales()}")
                print(f"{texto_indicadores}")
                print(f"{texto_operacion_activa}")
                print("-" * 75)
                print(f"{texto_trailing}")
                print("-" * 75)
                print(f"{texto_stop_loss}")
                print("-" * 75)
                print(f" 💰 TAKE PROFIT : {parametros.TAKE_PROFIT}")
                print("-" * 75)
                print(f" 🚦 FILTRO ENTRADAS : {'🔒 BLOQUEADO (Operación detectada)' if operacion_activa else '🔓 EN ESPERA DE SEÑAL'}")
                print("=" * 75)
                print(f"{ui_patrones()}")
                print("=" * 75)
                print(f"{ui_estadisticas(motivo_cierre_stats)}")
                print("=" * 75)
                print(f" 🔴 Ultimo error              : {parametros.error}")
                print("=" * 75)
                    
            except Exception as error_ejecucion:
                parametros.error = traceback.format_exc()
                pass
    except Exception as e: 
        parametros.error = traceback.format_exc()

# ===========================================================================
# 📈 MOTOR GRÁFICO REAL TIME PARA MAC OS (NATIVO ASÍNCRONO)
# ===========================================================================
from matplotlib.animation import FuncAnimation

def loop_render_grafico(frame, fig, ax):
    """Refresca la GUI de manera segura interactuando directamente con Matplotlib"""
    try:
        datos_vela = parametros.datos_graficos["datos_velas"].copy()
        hora_vela = parametros.datos_graficos["hora_vela"]
        operacion = parametros.datos_graficos["operacion"]
        
        # Generar set de prueba inicial para que el gráfico no nazca vacío
        if datos_vela.empty:
            return
            
        ax.clear() # Limpieza de primitivas viejas para evitar superposición
        apf = []
        
        if hora_vela is not None and hora_vela in datos_vela.index:
            compra_lista = [np.nan] * len(datos_vela)
            venta_lista = [np.nan] * len(datos_vela)
            pos_idx = datos_vela.index.get_loc(hora_vela)
            
            if "COMPRA" in operacion:
                compra_lista[pos_idx] = datos_vela.loc[hora_vela, 'Low'] - 2.0
                apf.append(mpf.make_addplot(compra_lista, type='scatter', markersize=150, marker='^', color='green', ax=ax))
            elif "VENTA" in operacion:
                venta_lista[pos_idx] = datos_vela.loc[hora_vela, 'High'] + 2.0
                apf.append(mpf.make_addplot(venta_lista, type='scatter', markersize=150, marker='v', color='red', ax=ax))
                
        # Corrección estructural: Pasar el eje explícito a mplfinance para evitar congelamientos en Mac
        if apf:
            mpf.plot(datos_vela, type='candle', ax=ax, addplot=apf, style='charles', datetime_format='%H:%M')
        else:
            mpf.plot(datos_vela, type='candle', ax=ax, style='charles', datetime_format='%H:%M')
            
        fig.canvas.draw_idle() # Redibujo eficiente optimizado para backend TkAgg
    except Exception as e:
        parametros.error = traceback.format_exc()
        pass

def extraer_datos_velas():
    parametros.lista_velas_acumuladas = extraer_velas()
    parametros.historico_velas = pd.DataFrame(parametros.lista_velas_acumuladas)
    parametros.datos_graficos["datos_velas"] = parametros.historico_velas
    parametros.historico_velas.index = pd.date_range(start="2026-01-01 09:30", periods=len(parametros.historico_velas), freq=f"{parametros.TEMPORALIDAD_MINUTOS}min")

def iniciar_renderizado_grafico_mac():
    # Inicialización de la figura y el eje nativo
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Lanzar subproceso del bot de forma segura y paralela
    hilo_grabador = threading.Thread(target=bot_scalping)
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
