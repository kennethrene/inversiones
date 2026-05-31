import time
import traceback
import config.config as config
from files.tracking import actualizar_ultima_operacion, actualizar_estadisticas_cierre

def operacion_debe_cerrar():
    ejecutar_cierre = False
    operacion_ganada = False
    motivo_cierre = ""

    ejecutar_cierre, operacion_ganada, motivo_cierre = cierre_stop_loss(config.rendimiento_actual)    
    
    if not ejecutar_cierre:          
        if config.trailing_activado:
            ejecutar_cierre, operacion_ganada, motivo_cierre = cierre_trailing_stop(config.maximo_rendimiento_alcanzado, config.rendimiento_actual)

        if not ejecutar_cierre:
            beneficio_neto =  float(config.datos_mapeados['Beneficio Neto'])
            ejecutar_cierre, operacion_ganada, motivo_cierre = cierre_take_profit(beneficio_neto)
            
            if not ejecutar_cierre:
                ejecutar_cierre, operacion_ganada, motivo_cierre = cierre_retroceso_rsi_inminente(beneficio_neto)

                if not ejecutar_cierre:
                    ejecutar_cierre, operacion_ganada, motivo_cierre = cierre_retroceso_macd_inminente(beneficio_neto)
    
    return ejecutar_cierre, operacion_ganada, motivo_cierre

def ejecutar_cierre(driver, motivo_cierre):
    try:
        beneficio_neto = float(config.datos_mapeados['Beneficio Neto'])

        driver.execute_script("if(window.ultimoBotonCierre) { window.ultimoBotonCierre.click(); }")
        #os.system(f'say "Posición cerrada por {motivo_cierre_stats}" &')
        config.historico_cuenta.append(beneficio_neto)

        # 🔥 REGISTRAR EL TIEMPO EXACTO DEL CIERRE
        config.TIEMPO_ULTIMO_CIERRE = time.time()

        config.maximo_rendimiento_alcanzado = 0.0
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

def cierre_stop_loss(rendimiento_actual):
    if not config.USAR_IA:
        if rendimiento_actual <= config.STOP_LOSS:
            motivo_cierre = f"Stop Loss: {rendimiento_actual:+.2f}%"
            operacion_ganada = False

            return True, operacion_ganada, motivo_cierre
    elif config.datos_mapeados['Operacion'] == "Compra" and config.valor_compra <= config.STOP_LOSS:
        motivo_cierre = f"Stop Loss: {config.valor_compra} <= {config.STOP_LOSS}"
        operacion_ganada = False

        return True, operacion_ganada, motivo_cierre
    elif config.datos_mapeados['Operacion'] == "Venta" and config.valor_venta >= config.STOP_LOSS:
        motivo_cierre = f"Stop Loss: {config.valor_venta} >= {config.STOP_LOSS}"
        operacion_ganada = False

        return True, operacion_ganada, motivo_cierre

    return False, False, "Ejecutándose"

def cierre_trailing_stop(maximo_rendimiento_alcanzado, rendimiento_actual):       
    if not config.USAR_IA:
        caida_desde_pico = maximo_rendimiento_alcanzado - rendimiento_actual
    
        if caida_desde_pico >= config.DISTANCIA_TRAILING_MAXIMA:
            motivo_cierre = f"Win Trailing. Rendimiento actual: {rendimiento_actual:+.2f}%. Ultimo pico de rendimiento: {caida_desde_pico:+.2f}%."
            operacion_ganada = True

            return True, operacion_ganada, motivo_cierre

    return False, False, "Ejecutándose"

def cierre_take_profit(beneficio_neto):
    if not config.USAR_IA:
        if beneficio_neto >= config.TAKE_PROFIT:
            operacion_ganada = True
            motivo_cierre = f"Take Profit: ${beneficio_neto:.2f}"

            return True, operacion_ganada, motivo_cierre
    elif config.datos_mapeados['Operacion'] == "Compra" and config.valor_compra >= config.TAKE_PROFIT:
        motivo_cierre = f"Take Profit: {config.valor_compra} >= {config.TAKE_PROFIT}"
        operacion_ganada = True

        return True, operacion_ganada, motivo_cierre
    elif config.datos_mapeados['Operacion'] == "Venta" and config.valor_venta <= config.TAKE_PROFIT:
        motivo_cierre = f"Take Profit: {config.valor_venta} <= {config.TAKE_PROFIT}"
        operacion_ganada = True

        return True, operacion_ganada, motivo_cierre

    return False, False, "Ejecutándose"

def cierre_retroceso_rsi_inminente(beneficio_neto):
    if not config.USAR_IA:
        if config.datos_mapeados["Operacion"] == "Venta" and beneficio_neto > 0 and float(config.valor_rsi) < config.RSI_SOBREVENTA_MACD:
            operacion_ganada = True
            motivo_cierre = f"Venta salió del RSI de sobreventa ({config.valor_rsi} < {config.RSI_SOBREVENTA_MACD}) - Se espera retroceso (+${beneficio_neto:.2f})"
            return True, operacion_ganada, motivo_cierre
        
        if config.datos_mapeados["Operacion"] == "Compra" and beneficio_neto > 0 and float(config.valor_rsi) > config.RSI_SOBRECOMPRA_MACD:
            operacion_ganada = True
            motivo_cierre = f"Venta salió del RSI de sobrecompra ({config.valor_rsi} > {config.RSI_SOBRECOMPRA_MACD}) - Se espera retroceso (+${beneficio_neto:.2f})"
            return True, operacion_ganada, motivo_cierre
    
    return False, False, "Ejecutándose"

def cierre_retroceso_macd_inminente(beneficio_neto):
    
    if not config.USAR_IA:
        if config.datos_mapeados["Operacion"] == "Venta" and beneficio_neto > 0 and float(config.valor_macd) > float(config.historico_macd[-1]):
            operacion_ganada = True
            motivo_cierre = f"Venta saliendo del MACD bajista: {config.valor_macd} > {config.historico_macd[-1]}- Se espera retroceso (+${beneficio_neto:.2f})"
            return True, operacion_ganada, motivo_cierre
        
        if config.datos_mapeados["Operacion"] == "Compra" and beneficio_neto > 0 and float(config.valor_macd) < float(config.historico_macd[-1]):
            operacion_ganada = True
            motivo_cierre = f"Compra salió del MACD alcista {config.valor_rsi} < {config.historico_macd[-1]} - Se espera retroceso (+${beneficio_neto:.2f})"
            return True, operacion_ganada, motivo_cierre
    
    return False, False, "Ejecutándose"