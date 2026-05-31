import configuracion.parametros as parametros

# Criterio 1: El RSI está en la zona de sobrecompra o sobreventa y el MACD se debilitó
def ejecutar_criterio():
    if float(parametros.valor_rsi) <= parametros.RSI_SOBREVENTA and macd_creciendo and rsi_confirmacion_compra:
        parametros.log_operacion = f" ℹ️  Comprando por criterio 1: ADX fuerte - RSI adecuado {parametros.valor_rsi} - MACD débil bajista - RSI confirma compra"
        parametros.datos_mapeados["Criterio Apertura"] = "Criterio 1"
        return "Comprar"
    elif float(parametros.valor_rsi) >= parametros.RSI_SOBRECOMPRA and macd_disminuyendo and rsi_confirmacion_venta:
        parametros.log_operacion = f" ℹ️  Vendiendo por criterio 1: ADX fuerte - RSI adecuado {parametros.valor_rsi} - MACD débil alcista - RSI confirma venta"
        parametros.datos_mapeados["Criterio Apertura"] = "Criterio 1"
        return "Vender"
    
    parametros.log_operacion = "\n ❌  ADX fuerte pero criterio 1 no cumple\n"
    if float(parametros.valor_rsi) > parametros.RSI_SOBREVENTA or parametros.valor_rsi < parametros.RSI_SOBRECOMPRA:
        parametros.log_operacion += f" └ RSI no cumple ({parametros.valor_rsi})\n"
    if float(parametros.valor_rsi) <= parametros.RSI_SOBREVENTA and not macd_creciendo:
        parametros.log_operacion += " └ MACD bajista no es débil\n"
    if float(parametros.valor_rsi) >= parametros.RSI_SOBRECOMPRA and not macd_disminuyendo:
        parametros.log_operacion = parametros.log_operacion + " └ MACD alcista no es débil\n"
    if float(parametros.valor_rsi) <= parametros.RSI_SOBREVENTA and macd_creciendo and not rsi_confirmacion_compra:
        parametros.log_operacion += " └ RSI no confirma compra\n"
    if float(parametros.valor_rsi) >= parametros.RSI_SOBRECOMPRA and macd_disminuyendo and not rsi_confirmacion_venta:
        parametros.log_operacion += " └ RSI no confirma venta\n"

    return None