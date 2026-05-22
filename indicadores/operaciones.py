import config

def ejecutar_operacion():
    if config.valor_rsi is not None and config.valor_adx is not None:
        macd_debil_alcista = len(config.historico_macd) > 1 and config.historico_macd[-1] < config.historico_macd[-2]
        macd_debil_bajista = len(config.historico_macd) > 1 and config.historico_macd[-1] > config.historico_macd[-2]

        rsi_confirmacion_venta = len(config.historico_rsi) > 1 and config.historico_rsi[-1] < config.RSI_SOBRECOMPRA
        rsi_confirmacion_compra = len(config.historico_rsi) > 1 and config.historico_rsi[-1] > config.RSI_SOBREVENTA

        # Criterio 1: El RSI está en la zona de sobrecompra o sobreventa y el macd se debilitó
        if config.valor_adx >= config.ADX_TENDENCIA_FUERTE:
            if config.valor_rsi <= config.RSI_SOBREVENTA and macd_debil_bajista and rsi_confirmacion_compra:
                config.log_operacion = f"⚠️  Comprando por criterio 1: ADX fuerte - RSI adecuado {config.valor_rsi} - MACD debil bajista - RSI confirma compra"
                return "Comprar"
            if config.valor_rsi >= config.RSI_SOBRECOMPRA and macd_debil_alcista and rsi_confirmacion_venta:
                config.log_operacion = f"⚠️  Vendiendo por criterio 1: ADX fuerte - RSI adecuado {config.valor_rsi} - MACD debil alcista - RSI confirma venta"
                return "Vender"
            
            config.log_operacion = "⚠️  ADX fuerte pero criterio 1 no cumple:"
            if config.valor_rsi > config.RSI_SOBREVENTA or config.valor_rsi < config.RSI_SOBRECOMPRA:
                config.log_operacion = config.log_operacion + f"RSI no cumple ({config.valor_rsi})"
            if config.valor_rsi <= config.RSI_SOBREVENTA and not macd_debil_bajista:
                config.log_operacion = config.log_operacion + " - MACD bajista no es debil"
            if config.valor_rsi >= config.RSI_SOBRECOMPRA and not macd_debil_alcista:
                config.log_operacion = config.log_operacion + " - MACD alcista no es debil"
            if config.valor_rsi <= config.RSI_SOBREVENTA and macd_debil_bajista and not rsi_confirmacion_compra:
                config.log_operacion = config.log_operacion + " - RSI no confirma compra"
            if config.valor_rsi >= config.RSI_SOBRECOMPRA and macd_debil_alcista and not rsi_confirmacion_venta:
                config.log_operacion = config.log_operacion + " - RSI no confirma venta"
            
            config.log_operacion = config.log_operacion + "\n"
        
        # Criterio 2: El RSI estuvo en la zona de sobrecompra o sobreventa pero el macd no indicaba debilidad. Ahora está fuera de esa zona 
        # y el macd está debilitándose
        if config.valor_adx >= config.ADX_TENDENCIA_FUERTE:        
            if config.valor_rsi <= config.RSI_SOBREVENTA_MACD and macd_debil_bajista:
                config.log_operacion = f"⚠️  Comprando por criterio 2: ADX fuerte - RSI adecuado {config.valor_rsi} - MACD debil bajista"
                return "Comprar"
            if config.valor_rsi >= config.RSI_SOBRECOMPRA_MACD and macd_debil_alcista:
                config.log_operacion = f"⚠️  Vendiendo por criterio 2: ADX fuerte - RSI adecuado {config.valor_rsi} - MACD debil alcista"
                return "Vender"
            
            config.log_operacion = "⚠️  ADX fuerte pero criterio 2 no cumple: "
            if config.valor_rsi > config.RSI_SOBREVENTA_MACD or config.valor_rsi < config.RSI_SOBRECOMPRA_MACD:
                config.log_operacion = config.log_operacion + f"RSI no cumple ({config.valor_rsi})"
            if config.valor_rsi <= config.RSI_SOBREVENTA_MACD and not macd_debil_bajista:
                config.log_operacion = config.log_operacion + " - MACD bajista no es debil"
            if config.valor_rsi >= config.RSI_SOBRECOMPRA_MACD and not macd_debil_alcista:
                config.log_operacion = config.log_operacion + " - MACD alcista no es debil"
    
    return ""
