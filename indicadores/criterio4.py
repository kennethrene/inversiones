import config

# Criterio 4: EMA y RSI
def ejecutar_criterio(tendencia_alcista, tendencia_bajista):
    if tendencia_alcista and float(config.valor_rsi) <= config.RSI_SOBREVENTA and float(config.valor_compra) > float(config.valor_ema_35):
        config.log_operacion = f"ℹ️  Comprando por criterio 4: Tendencia alcista, RSI adecuado ({config.valor_rsi}) y precio por encima de EMA35: {config.valor_compra} > {config.valor_ema_35}"
        config.datos_mapeados["Criterio Apertura"] = "Criterio 4"
        return "Comprar"
    elif tendencia_bajista and float(config.valor_rsi) >= config.RSI_SOBRECOMPRA and float(config.valor_venta) < float(config.valor_ema_35):
        config.log_operacion = f"ℹ️  Vendiendo por criterio 4: Tendencia bajista, RSI adecuado ({config.valor_rsi}) y precio por debajo de EMA35: {config.valor_compra} < {config.valor_ema_35}"
        config.datos_mapeados["Criterio Apertura"] = "Criterio 4"
        return "Vender"
    
    config.log_operacion += "\n ❌  ADX fuerte pero criterio 4 no cumple\n"
    if tendencia_alcista and float(config.valor_rsi) > config.RSI_SOBREVENTA:
        config.log_operacion += f" └ Tendencia alcista, RSI no adecuado para comprar: {config.valor_rsi} > {config.RSI_SOBREVENTA}\n"
    if tendencia_alcista and float(config.valor_compra) <= float(config.valor_ema_35):
        config.log_operacion += f" └ Tendencia alcista, pero el precio no está por encima de EMA35: {config.valor_compra} <= {config.valor_ema_35}\n"

    if tendencia_bajista and float(config.valor_rsi) < config.RSI_SOBRECOMPRA:
        config.log_operacion += f" └ Tendencia bajista, RSI no adecuado para vender: {config.valor_rsi} < {config.RSI_SOBRECOMPRA}\n"
    if tendencia_bajista and float(config.valor_venta) >= float(config.valor_ema_35):
        config.log_operacion += f" └ Tendencia bajista, pero el precio no está por debajo de EMA35: {config.valor_compra} > {config.valor_ema_35}\n"

    return None