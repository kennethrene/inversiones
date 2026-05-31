import time
import traceback
import configuracion.parametros as parametros
from archivos.seguimiento import actualizar_ultima_operacion, actualizar_estadisticas_cierre

def operacion_debe_cerrar():
    ejecutar_cierre = False
    operacion_ganada = False
    motivo_cierre = ""

    ejecutar_cierre, operacion_ganada, motivo_cierre = cierre_stop_loss(parametros.rendimiento_actual)    
    
    if not ejecutar_cierre:          
        if parametros.trailing_activado:
            ejecutar_cierre, operacion_ganada, motivo_cierre = cierre_trailing_stop(parametros.maximo_rendimiento_alcanzado, parametros.rendimiento_actual)

        if not ejecutar_cierre:
            beneficio_neto =  float(parametros.datos_mapeados['Beneficio Neto'])
            ejecutar_cierre, operacion_ganada, motivo_cierre = cierre_take_profit(beneficio_neto)
            
            if not ejecutar_cierre:
                ejecutar_cierre, operacion_ganada, motivo_cierre = cierre_retroceso_rsi_inminente(beneficio_neto)

                if not ejecutar_cierre:
                    ejecutar_cierre, operacion_ganada, motivo_cierre = cierre_retroceso_macd_inminente(beneficio_neto)
    
    return ejecutar_cierre, operacion_ganada, motivo_cierre

def ejecutar_cierre(driver, motivo_cierre):
    try:
        beneficio_neto = float(parametros.datos_mapeados['Beneficio Neto'])

        driver.execute_script("if(window.ultimoBotonCierre) { window.ultimoBotonCierre.click(); }")
        #os.system(f'say "Posición cerrada por {motivo_cierre_stats}" &')
        parametros.historico_cuenta.append(beneficio_neto)

        # 🔥 REGISTRAR EL TIEMPO EXACTO DEL CIERRE
        parametros.TIEMPO_ULTIMO_CIERRE = time.time()

        parametros.maximo_rendimiento_alcanzado = 0.0
        parametros.TRAILING_STOP = 15.0
        parametros.DISTANCIA_TRAILING_MAXIMA = 4.0
        parametros.TAKE_PROFIT = 5.0
        parametros.STOP_LOSS  = -10.0
        parametros.trailing_activado = False

        # Sincronizador de estadísticas con lectura de resultados reales
        if beneficio_neto > 0:
            actualizar_ultima_operacion(parametros.datos_mapeados, "Ganada", motivo_cierre)
            actualizar_estadisticas_cierre(True)
        else:
            actualizar_ultima_operacion(parametros.datos_mapeados, "Perdida", motivo_cierre)
            actualizar_estadisticas_cierre(False)

        time.sleep(5)
    except Exception as error_ejecucion:
        parametros.error = traceback.format_exc()

def cierre_stop_loss(rendimiento_actual):
    if not parametros.USAR_IA:
        if rendimiento_actual <= parametros.STOP_LOSS:
            motivo_cierre = f"Stop Loss: {rendimiento_actual:+.2f}%"
            operacion_ganada = False

            return True, operacion_ganada, motivo_cierre
    elif parametros.datos_mapeados['Operacion'] == "Compra" and parametros.valor_compra <= parametros.STOP_LOSS:
        motivo_cierre = f"Stop Loss: {parametros.valor_compra} <= {parametros.STOP_LOSS}"
        operacion_ganada = False

        return True, operacion_ganada, motivo_cierre
    elif parametros.datos_mapeados['Operacion'] == "Venta" and parametros.valor_venta >= parametros.STOP_LOSS:
        motivo_cierre = f"Stop Loss: {parametros.valor_venta} >= {parametros.STOP_LOSS}"
        operacion_ganada = False

        return True, operacion_ganada, motivo_cierre

    return False, False, "Ejecutándose"

def cierre_trailing_stop(maximo_rendimiento_alcanzado, rendimiento_actual):       
    if not parametros.USAR_IA:
        caida_desde_pico = maximo_rendimiento_alcanzado - rendimiento_actual
    
        if caida_desde_pico >= parametros.DISTANCIA_TRAILING_MAXIMA:
            motivo_cierre = f"Win Trailing. Rendimiento actual: {rendimiento_actual:+.2f}%. Ultimo pico de rendimiento: {caida_desde_pico:+.2f}%."
            operacion_ganada = True

            return True, operacion_ganada, motivo_cierre

    return False, False, "Ejecutándose"

def cierre_take_profit(beneficio_neto):
    if not parametros.USAR_IA:
        if beneficio_neto >= parametros.TAKE_PROFIT:
            operacion_ganada = True
            motivo_cierre = f"Take Profit: ${beneficio_neto:.2f}"

            return True, operacion_ganada, motivo_cierre
    elif parametros.datos_mapeados['Operacion'] == "Compra" and parametros.valor_compra >= parametros.TAKE_PROFIT:
        motivo_cierre = f"Take Profit: {parametros.valor_compra} >= {parametros.TAKE_PROFIT}"
        operacion_ganada = True

        return True, operacion_ganada, motivo_cierre
    elif parametros.datos_mapeados['Operacion'] == "Venta" and parametros.valor_venta <= parametros.TAKE_PROFIT:
        motivo_cierre = f"Take Profit: {parametros.valor_venta} <= {parametros.TAKE_PROFIT}"
        operacion_ganada = True

        return True, operacion_ganada, motivo_cierre

    return False, False, "Ejecutándose"

def cierre_retroceso_rsi_inminente(beneficio_neto):
    if not parametros.USAR_IA:
        if parametros.datos_mapeados["Operacion"] == "Venta" and beneficio_neto > 0 and float(parametros.valor_rsi) < parametros.RSI_SOBREVENTA_MACD:
            operacion_ganada = True
            motivo_cierre = f"Venta salió del RSI de sobreventa ({parametros.valor_rsi} < {parametros.RSI_SOBREVENTA_MACD}) - Se espera retroceso (+${beneficio_neto:.2f})"
            return True, operacion_ganada, motivo_cierre
        
        if parametros.datos_mapeados["Operacion"] == "Compra" and beneficio_neto > 0 and float(parametros.valor_rsi) > parametros.RSI_SOBRECOMPRA_MACD:
            operacion_ganada = True
            motivo_cierre = f"Venta salió del RSI de sobrecompra ({parametros.valor_rsi} > {parametros.RSI_SOBRECOMPRA_MACD}) - Se espera retroceso (+${beneficio_neto:.2f})"
            return True, operacion_ganada, motivo_cierre
    
    return False, False, "Ejecutándose"

def cierre_retroceso_macd_inminente(beneficio_neto):
    
    if not parametros.USAR_IA:
        if parametros.datos_mapeados["Operacion"] == "Venta" and beneficio_neto > 0 and float(parametros.valor_macd) > float(parametros.historico_macd[-1]):
            operacion_ganada = True
            motivo_cierre = f"Venta saliendo del MACD bajista: {parametros.valor_macd} > {parametros.historico_macd[-1]}- Se espera retroceso (+${beneficio_neto:.2f})"
            return True, operacion_ganada, motivo_cierre
        
        if parametros.datos_mapeados["Operacion"] == "Compra" and beneficio_neto > 0 and float(parametros.valor_macd) < float(parametros.historico_macd[-1]):
            operacion_ganada = True
            motivo_cierre = f"Compra salió del MACD alcista {parametros.valor_rsi} < {parametros.historico_macd[-1]} - Se espera retroceso (+${beneficio_neto:.2f})"
            return True, operacion_ganada, motivo_cierre
    
    return False, False, "Ejecutándose"