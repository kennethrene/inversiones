import config

# Criterio 1: El RSI está en la zona de sobrecompra o sobreventa y el MACD se debilitó
def ejecutar_criterio():
    if float(config.valor_rsi) <= config.RSI_SOBREVENTA and macd_creciendo and rsi_confirmacion_compra:
        config.log_operacion = f" ℹ️  Comprando por criterio 1: ADX fuerte - RSI adecuado {config.valor_rsi} - MACD débil bajista - RSI confirma compra"
        config.datos_mapeados["Criterio Apertura"] = "Criterio 1"
        return "Comprar"
    elif float(config.valor_rsi) >= config.RSI_SOBRECOMPRA and macd_disminuyendo and rsi_confirmacion_venta:
        config.log_operacion = f" ℹ️  Vendiendo por criterio 1: ADX fuerte - RSI adecuado {config.valor_rsi} - MACD débil alcista - RSI confirma venta"
        config.datos_mapeados["Criterio Apertura"] = "Criterio 1"
        return "Vender"
    
    config.log_operacion = "\n ❌  ADX fuerte pero criterio 1 no cumple\n"
    if float(config.valor_rsi) > config.RSI_SOBREVENTA or config.valor_rsi < config.RSI_SOBRECOMPRA:
        config.log_operacion += f" └ RSI no cumple ({config.valor_rsi})\n"
    if float(config.valor_rsi) <= config.RSI_SOBREVENTA and not macd_creciendo:
        config.log_operacion += " └ MACD bajista no es débil\n"
    if float(config.valor_rsi) >= config.RSI_SOBRECOMPRA and not macd_disminuyendo:
        config.log_operacion = config.log_operacion + " └ MACD alcista no es débil\n"
    if float(config.valor_rsi) <= config.RSI_SOBREVENTA and macd_creciendo and not rsi_confirmacion_compra:
        config.log_operacion += " └ RSI no confirma compra\n"
    if float(config.valor_rsi) >= config.RSI_SOBRECOMPRA and macd_disminuyendo and not rsi_confirmacion_venta:
        config.log_operacion += " └ RSI no confirma venta\n"

    return None