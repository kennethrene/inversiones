import configuracion.parametros as parametros

# Criterio 4: EMA y RSI
def ejecutar_criterio(tendencia_alcista, tendencia_bajista):
    if tendencia_alcista and float(parametros.valor_rsi) <= parametros.RSI_SOBREVENTA and float(parametros.valor_compra) > float(parametros.valor_ema_35):
        parametros.log_operacion = f"ℹ️  Comprando por criterio 4: Tendencia alcista, RSI adecuado ({parametros.valor_rsi}) y precio por encima de EMA35: {parametros.valor_compra} > {parametros.valor_ema_35}"
        parametros.datos_mapeados["Criterio Apertura"] = "Criterio 4"
        return "Comprar"
    elif tendencia_bajista and float(parametros.valor_rsi) >= parametros.RSI_SOBRECOMPRA and float(parametros.valor_venta) < float(parametros.valor_ema_35):
        parametros.log_operacion = f"ℹ️  Vendiendo por criterio 4: Tendencia bajista, RSI adecuado ({parametros.valor_rsi}) y precio por debajo de EMA35: {parametros.valor_compra} < {parametros.valor_ema_35}"
        parametros.datos_mapeados["Criterio Apertura"] = "Criterio 4"
        return "Vender"
    
    parametros.log_operacion += "\n ❌  ADX fuerte pero criterio 4 no cumple\n"
    if tendencia_alcista and float(parametros.valor_rsi) > parametros.RSI_SOBREVENTA:
        parametros.log_operacion += f" └ Tendencia alcista, RSI no adecuado para comprar: {parametros.valor_rsi} > {parametros.RSI_SOBREVENTA}\n"
    if tendencia_alcista and float(parametros.valor_compra) <= float(parametros.valor_ema_35):
        parametros.log_operacion += f" └ Tendencia alcista, pero el precio no está por encima de EMA35: {parametros.valor_compra} <= {parametros.valor_ema_35}\n"

    if tendencia_bajista and float(parametros.valor_rsi) < parametros.RSI_SOBRECOMPRA:
        parametros.log_operacion += f" └ Tendencia bajista, RSI no adecuado para vender: {parametros.valor_rsi} < {parametros.RSI_SOBRECOMPRA}\n"
    if tendencia_bajista and float(parametros.valor_venta) >= float(parametros.valor_ema_35):
        parametros.log_operacion += f" └ Tendencia bajista, pero el precio no está por debajo de EMA35: {parametros.valor_compra} > {parametros.valor_ema_35}\n"

    return None