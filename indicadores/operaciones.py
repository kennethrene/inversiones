import config

def ejecutar_operacion():
    if config.valor_rsi is not None and config.valor_adx is not None:
        config.log_operacion = ""
        macd_debil_alcista = len(config.historico_macd) > 1 and config.historico_macd[-1] < config.historico_macd[-2]
        macd_debil_bajista = len(config.historico_macd) > 1 and config.historico_macd[-1] > config.historico_macd[-2]

        rsi_confirmacion_venta = len(config.historico_rsi) > 1 and config.historico_rsi[-1] < config.RSI_SOBRECOMPRA
        rsi_confirmacion_compra = len(config.historico_rsi) > 1 and config.historico_rsi[-1] > config.RSI_SOBREVENTA

        if config.valor_adx >= config.ADX_TENDENCIA_FUERTE:            
            if config.promedio_volumen_sin_actual >= config.VOL_ADECUADO_OPERAR:
                # Criterio 1: El RSI está en la zona de sobrecompra o sobreventa y el MACD se debilitó
                if float(config.valor_rsi) <= config.RSI_SOBREVENTA and macd_debil_bajista and rsi_confirmacion_compra:
                    config.log_operacion = f" ℹ️   Comprando por criterio 1: ADX fuerte - RSI adecuado {config.valor_rsi} - MACD débil bajista - RSI confirma compra"
                    return "Comprar"
                elif float(config.valor_rsi) >= config.RSI_SOBRECOMPRA and macd_debil_alcista and rsi_confirmacion_venta:
                    config.log_operacion = f" ℹ️   Vendiendo por criterio 1: ADX fuerte - RSI adecuado {config.valor_rsi} - MACD débil alcista - RSI confirma venta"
                    return "Vender"
                
                config.log_operacion = "\n ❌  ADX fuerte pero criterio 1 no cumple:"
                if float(config.valor_rsi) > config.RSI_SOBREVENTA or config.valor_rsi < config.RSI_SOBRECOMPRA:
                    config.log_operacion = config.log_operacion + f" └ RSI no cumple ({config.valor_rsi})\n"
                if float(config.valor_rsi) <= config.RSI_SOBREVENTA and not macd_debil_bajista:
                    config.log_operacion = config.log_operacion + " └ MACD bajista no es débil\n"
                if float(config.valor_rsi) >= config.RSI_SOBRECOMPRA and not macd_debil_alcista:
                    config.log_operacion = config.log_operacion + " └ MACD alcista no es débil\n"
                if float(config.valor_rsi) <= config.RSI_SOBREVENTA and macd_debil_bajista and not rsi_confirmacion_compra:
                    config.log_operacion = config.log_operacion + " └ RSI no confirma compra\n"
                if float(config.valor_rsi) >= config.RSI_SOBRECOMPRA and macd_debil_alcista and not rsi_confirmacion_venta:
                    config.log_operacion = config.log_operacion + " └ RSI no confirma venta\n"
                
                # Cirterio 2: El RSI estuvo en la zona de sobrecompra o sobreventa pero el macd no indicaba debilidad. Ahora está fuera de esa zona 
                # y el macd está debilitándose
                if float(config.valor_rsi) <= config.RSI_SOBREVENTA_MACD and macd_debil_bajista:
                    config.log_operacion = f"ℹ️   Comprando por criterio 2: ADX fuerte - RSI adecuado {config.valor_rsi} - MACD debil bajista"
                    return "Comprar"
                elif float(config.valor_rsi) >= config.RSI_SOBRECOMPRA_MACD and macd_debil_alcista:
                    config.log_operacion = f"ℹ️   Vendiendo por criterio 2: ADX fuerte - RSI adecuado {config.valor_rsi} - MACD debil alcista"
                    return "Vender"
                
                config.log_operacion = config.log_operacion + "\n ❌  ADX fuerte pero criterio 2 no cumple: "
                if float(config.valor_rsi) > config.RSI_SOBREVENTA_MACD or config.valor_rsi < config.RSI_SOBRECOMPRA_MACD:
                    config.log_operacion = config.log_operacion + f" └ RSI no cumple ({config.valor_rsi})\n"
                if float(config.valor_rsi) <= config.RSI_SOBREVENTA_MACD and not macd_debil_bajista:
                    config.log_operacion = config.log_operacion + " └ MACD bajista no es débil\n"
                if float(config.valor_rsi) >= config.RSI_SOBRECOMPRA_MACD and not macd_debil_alcista:
                    config.log_operacion = config.log_operacion + " └ MACD alcista no es débil\n"

                # Criterio 3: Solo MACD - La barra de MACD está creciendo ya sea bajista o alcista
                macd_fuerte_alcista = len(config.historico_macd) > 1 and config.historico_macd[-1] > 0 and config.historico_macd[-1] > config.historico_macd[-2]
                macd_fuerte_bajista = len(config.historico_macd) > 1 and config.historico_macd[-1] < 0 and config.historico_macd[-1] < config.historico_macd[-2]                

                if macd_fuerte_alcista:
                    config.log_operacion = f"ℹ️  Comprando por criterio 3 - MACD fuerte alcista"
                    return "Comprar"
                elif macd_fuerte_bajista:
                    config.log_operacion = f"ℹ️  Vendiendo por criterio 3 - MACD fuerte bajista"
                    return "Vender"
                
                config.log_operacion = config.log_operacion + "\n ❌  ADX fuerte pero criterio 3 no cumple: "
                if len(config.historico_macd) > 1 and config.historico_macd[-1] > 0 and config.historico_macd[-1] < config.historico_macd[-2]:
                    config.log_operacion = config.log_operacion + f" └ MACD no cumple: No está aumentando para comprar\n"
                if len(config.historico_macd) > 1 and config.historico_macd[-1] < 0 and config.historico_macd[-1] > config.historico_macd[-2]:
                    config.log_operacion = config.log_operacion + f" └ MACD no cumple: No está disminuyendo para vender\n"
        
                # Criterio 4: EMA y RSI
                tendencia_alcista = config.valor_ema_35 > config.valor_ema_50
                tendencia_bajista = config.valor_ema_35 < config.valor_ema_50

                if tendencia_alcista and float(config.valor_rsi) <= config.RSI_SOBREVENTA and float(config.valor_compra) > float(config.valor_ema_35):
                    config.log_operacion = f" ℹ️   Comprando por criterio 4: Tendencia alcista, RSI adecuado ({config.valor_rsi}) y precio por encima de EMA35: {config.valor_compra} > {config.valor_ema_35}"
                    return "Comprar"
                elif tendencia_bajista and float(config.valor_rsi) >= config.RSI_SOBRECOMPRA and float(config.valor_compra) < float(config.valor_ema_35):
                    config.log_operacion = f" ℹ️   Vendiendo por criterio 4: Tendencia bajista, RSI adecuado ({config.valor_rsi}) y precio por debajo de EMA35: {config.valor_compra} < {config.valor_ema_35}"
                    return "Vender"
                
                config.log_operacion = config.log_operacion + "\n ❌  ADX fuerte pero criterio 4 no cumple: "
                if tendencia_alcista and float(config.valor_rsi) > config.RSI_SOBREVENTA:
                    config.log_operacion = f" └ Tendencia alcista, RSI no adecuado ({config.valor_rsi})\n"
                if tendencia_alcista and float(config.valor_compra) <= float(config.valor_ema_35):
                    config.log_operacion = f" └ Tendencia alcista, pero el precio no está por encima de EMA35: {config.valor_compra} <= {config.valor_ema_35}\n"

                if tendencia_bajista and float(config.valor_rsi) < config.RSI_SOBRECOMPRA:
                    config.log_operacion = f" └ Tendencia bajista, RSI no adecuado ({config.valor_rsi})\n"
                if tendencia_bajista and float(config.valor_compra) >= float(config.valor_ema_35):
                    config.log_operacion = f" └ Tendencia bajista, pero el precio no está por debajo de EMA35: {config.valor_compra} > {config.valor_ema_35}\n"
            else:
                config.log_operacion = f"❌  ADX fuerte pero Volumen muy bajo: {config.promedio_volumen_sin_actual} - Requerido: {config.VOL_ADECUADO_OPERAR}"

        elif config.promedio_volumen_sin_actual >= config.VOL_ADECUADO_OPERAR:
            # Criterio 5: Subidas y bajadas muy rápidas
            if config.ultimo_valor_compra != None \
                and abs(float(config.valor_compra) - float(config.ultimo_valor_compra)) > float(config.movimiento_abrupto[config.activo_actual]) \
                and float(config.valor_compra) > float(config.ultimo_valor_compra):
                
                    config.log_operacion = f" ℹ️   Comprando por criterio 5: Movimiento abrupto {abs(float(config.valor_compra) - float(config.ultimo_valor_compra))} supera el requerido {config.movimiento_abrupto[config.activo_actual]}"

                    return "Comprar"
            if config.ultimo_valor_venta != None \
                and abs(float(config.valor_venta) - float(config.ultimo_valor_venta)) > float(config.movimiento_abrupto[config.activo_actual]) \
                and float(config.valor_venta) < float(config.ultimo_valor_venta):
                
                    config.log_operacion = f" ℹ️   Vendiendo por criterio 5: Movimiento abrupto {abs(float(config.valor_venta) - float(config.ultimo_valor_venta)) } supera el requerido {config.movimiento_abrupto[config.activo_actual]}"

                    return "Vender" 
            
    return ""
