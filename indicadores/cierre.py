import config.config as config

def ejecutar_cierre(maximo_rendimiento_alcanzado, rendimiento_actual):
    ejecutar_cierre = False
    operacion_ganada = False
    motivo_cierre = ""

    ejecutar_cierre, operacion_ganada, motivo_cierre = ejecutar_cierre_stop_loss(rendimiento_actual)    
    
    if not ejecutar_cierre:          
        if config.trailing_activado:
            ejecutar_cierre, operacion_ganada, motivo_cierre = ejecutar_cierre_trailing_stop(maximo_rendimiento_alcanzado, rendimiento_actual)

        if not ejecutar_cierre:
            beneficio_neto =  float(config.datos_mapeados['Beneficio Neto'])
            ejecutar_cierre, operacion_ganada, motivo_cierre = ejecutar_cierre_take_profit(beneficio_neto)
            
            if not ejecutar_cierre:
                ejecutar_cierre, operacion_ganada, motivo_cierre = ejecutar_cierre_retroceso_rsi_inminente(beneficio_neto)

                if not ejecutar_cierre:
                    ejecutar_cierre, operacion_ganada, motivo_cierre = ejecutar_cierre_retroceso_macd_inminente(beneficio_neto)
    
    return ejecutar_cierre, operacion_ganada, motivo_cierre

def ejecutar_cierre_stop_loss(rendimiento_actual):
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

def ejecutar_cierre_trailing_stop(maximo_rendimiento_alcanzado, rendimiento_actual):       
    if not config.USAR_IA:
        caida_desde_pico = maximo_rendimiento_alcanzado - rendimiento_actual
    
        if caida_desde_pico >= config.DISTANCIA_TRAILING_MAXIMA:
            motivo_cierre = f"Win Trailing. Rendimiento actual: {rendimiento_actual:+.2f}%. Ultimo pico de rendimiento: {caida_desde_pico:+.2f}%."
            operacion_ganada = True

            return True, operacion_ganada, motivo_cierre

    return False, False, "Ejecutándose"

def ejecutar_cierre_take_profit(beneficio_neto):
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

def ejecutar_cierre_retroceso_rsi_inminente(beneficio_neto):
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

def ejecutar_cierre_retroceso_macd_inminente(beneficio_neto):
    
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