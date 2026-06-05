from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import traceback
import threading
import matplotlib.pyplot as plt
import time
import os
import configuracion.parametros as parametros
from operaciones.ejecucion import ejecutar_operacion, validar_trailing_stop, reevaluar_operacion
from ui.interfaz import ui_trailing, ui_stop_loss, ui_operacion_activa, ui_general
from extraccion.datos_xtb import extraer_datos_operacion, obtener_datos_operaciones, obtener_datos_compra_venta
from operaciones.cierre import operacion_debe_cerrar, ejecutar_cierre
from indicadores.informacion import obtener_texto_indicadores, actualizar_informacion, precargar_datos
from ui.grafico import loop_render_grafico, extraer_datos_velas
from matplotlib.animation import FuncAnimation

minuto_anterior = ""
motivo_cierre = "N/D"
driver = None
comando_limpiar = None

def inicializar():
    global minuto_anterior, motivo_cierre, driver, comando_limpiar

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

    parametros.bloqueo_ejecutar_orden = False
    minuto_anterior = ""
    parametros.minuto_ultima_orden = ""
    motivo_cierre = "N/D"

    os.system(comando_limpiar)
    print("=" * 75)
    print("¡Conectado con éxito a xStation!")
    print("=" * 75)
    time.sleep(1)

def bot_scalping():
    global estadisticas_bot
    global trailing_activado, tiempo_ultimo_cierre
    global minuto_anterior, motivo_cierre, driver, comando_limpiar
    
    try:
        inicializar()

        while True:
            try:
                if parametros.minuto_ultima_orden != time.strftime('%M'):
                    parametros.bloqueo_ejecutar_orden = False
                
                minuto_actual = time.strftime('%M')                
                if minuto_anterior == "": minuto_anterior = minuto_actual

                segundo_actual = time.strftime('%H:%M:%S')
                obtener_datos_compra_venta(segundo_actual, False, driver)

                precargar_datos()

                if segundo_actual != parametros.ultimo_segundo_procesado:
                    parametros.ultimo_segundo_procesado = segundo_actual

                segundo_hace_dos_segs = time.time() - 2
                if segundo_hace_dos_segs >= parametros.penultimo_segundo_procesado:
                    parametros.ultimo_valor_volumen = parametros.valor_volumen
                    parametros.penultimo_segundo_procesado = segundo_hace_dos_segs

                # Escaneo de los indicadores técnicos
                xpath_indicadores = "//*[contains(@class, 'indicator-value-label')]"
                elementos_indicadores = driver.find_elements(By.XPATH, xpath_indicadores)
                texto_indicadores = obtener_texto_indicadores(elementos_indicadores)

                if parametros.minuto_ultima_orden != time.strftime('%M'):
                    parametros.bloqueo_ejecutar_orden = False

                # Obtener los datos de las operaciones actuales
                js_script_shadow = obtener_datos_operaciones()                
                resultado_shadow = driver.execute_script(js_script_shadow)
                operaciones_detalles = resultado_shadow["detalles"]
                
                total_posiciones = resultado_shadow["total"]
                operacion_activa = total_posiciones > 0
                ejecutar_cierre_operacion = False
                
                texto_trailing = ui_trailing(False, False, None)
                texto_stop_loss = ui_stop_loss(False)

                if operacion_activa and len(operaciones_detalles) > 0:
                    if parametros.hora_apertura_orden is None:
                        parametros.hora_apertura_orden = time.time()
                        parametros.maximo_rendimiento_alcanzado = -999.0

                    extraer_datos_operacion(operaciones_detalles)

                    texto_stop_loss         = ui_stop_loss(True)
                    texto_trailing          = validar_trailing_stop()
                    texto_operacion_activa  = ui_operacion_activa(True)

                    ejecutar_cierre_operacion, _, motivo_cierre = operacion_debe_cerrar()

                    # Si no se cierra, entonces validar si se debe ajustar
                    if not ejecutar_cierre_operacion:
                        accion, motivo = reevaluar_operacion()

                        if accion == "Cerrar":
                            ejecutar_cierre_operacion = True
                            motivo_cierre = motivo
                else:
                    texto_operacion_activa = ui_operacion_activa(False)
                    parametros.hora_apertura_orden = None

                # Actualizar informacion de indicadores
                if int(minuto_actual) % parametros.TEMPORALIDAD_MINUTOS == 0 and minuto_actual != minuto_anterior:
                    if time.time() - parametros.TIEMPO_ULTIMO_CIERRE < parametros.SEGUNDOS_ENFRIAMIENTO:
                        continue

                    if parametros.MOSTRAR_GRAFICO:
                        extraer_datos_velas()

                    minuto_anterior = minuto_actual
                    actualizar_informacion()

                # Ejecución automática de operaciones
                if not parametros.bloqueo_ejecutar_orden and not operacion_activa:
                    # 🔥 CONTROL DE ENFRIAMIENTO TRAS CIERRE
                    if not parametros.USAR_IA and time.time() - parametros.TIEMPO_ULTIMO_CIERRE < parametros.SEGUNDOS_ENFRIAMIENTO:
                        continue # Salta la iteración si no ha pasado el tiempo mínimo

                    # Validar y abrir posicion en caso que se cumplan las condiciones
                    ejecutar_operacion()

                # Ejecutar el cierre de la operacion
                if ejecutar_cierre_operacion and operacion_activa:
                   ejecutar_cierre(driver, motivo_cierre)

                # Impresión de la UI en la consola
                ui_general(texto_indicadores, operacion_activa, texto_operacion_activa, texto_trailing, texto_stop_loss, motivo_cierre)
                        
            except Exception as e_bucle:
                parametros.error += traceback.format_exc()
                time.sleep(0.1)
            
    except Exception as e:
        parametros.error += traceback.format_exc()

def iniciar_renderizado_grafico_mac():
    # Inicialización de la figura y el eje nativo
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Lanzar subproceso del bot de forma segura y paralela
    hilo_grabador = threading.Thread(target=bot_scalping)
    hilo_grabador.daemon = True
    hilo_grabador.start()
    
    # Animación automática nativa que maneja el refresco asíncrono
    ani = FuncAnimation(fig, loop_render_grafico, fargs=(fig, ax), interval=1000, cache_frame_data=False)
    plt.show()

if __name__ == "__main__":
    try:
        if not parametros.MOSTRAR_GRAFICO:
            bot_scalping()
        else:
            iniciar_renderizado_grafico_mac()
    except KeyboardInterrupt:
        print("\n\nSistema apagado de forma segura")

