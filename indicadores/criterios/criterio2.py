import config.config as config

# Criterio 2: El RSI estuvo en la zona de sobrecompra o sobreventa y debemos actuar a favor de la tendencia
def ejecutar_criterio(tendencia_alcista, tendencia_bajista):
    if float(config.valor_rsi) <= config.RSI_SOBREVENTA and tendencia_alcista:
        config.log_operacion = f"ℹ️  Comprando por criterio 2: ADX fuerte - RSI adecuado {config.valor_rsi} - Tendencia general alcista"                    
        config.datos_mapeados["Criterio Apertura"] = "Criterio 2"
        return "Comprar"
    elif float(config.valor_rsi) >= config.RSI_SOBRECOMPRA and tendencia_bajista:
        config.log_operacion = f"ℹ️  Vendiendo por criterio 2: ADX fuerte - RSI adecuado {config.valor_rsi} - Tendencia general bajista"
        config.datos_mapeados["Criterio Apertura"] = "Criterio 2"
        return "Vender"
    
    config.log_operacion += "\n ❌  ADX fuerte pero criterio 2 no cumple\n"
    if float(config.valor_rsi) > config.RSI_SOBREVENTA_MACD or config.valor_rsi < config.RSI_SOBRECOMPRA_MACD:
        config.log_operacion += f" └ RSI no cumple ({config.valor_rsi})\n"
    
    return None