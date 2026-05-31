import configuracion.parametros as parametros

# Criterio 2: El RSI estuvo en la zona de sobrecompra o sobreventa y debemos actuar a favor de la tendencia
def ejecutar_criterio(tendencia_alcista, tendencia_bajista):
    if float(parametros.valor_rsi) <= parametros.RSI_SOBREVENTA and tendencia_alcista:
        parametros.log_operacion = f"ℹ️  Comprando por criterio 2: ADX fuerte - RSI adecuado {parametros.valor_rsi} - Tendencia general alcista"                    
        parametros.datos_mapeados["Criterio Apertura"] = "Criterio 2"
        return "Comprar"
    elif float(parametros.valor_rsi) >= parametros.RSI_SOBRECOMPRA and tendencia_bajista:
        parametros.log_operacion = f"ℹ️  Vendiendo por criterio 2: ADX fuerte - RSI adecuado {parametros.valor_rsi} - Tendencia general bajista"
        parametros.datos_mapeados["Criterio Apertura"] = "Criterio 2"
        return "Vender"
    
    parametros.log_operacion += "\n ❌  ADX fuerte pero criterio 2 no cumple\n"
    if float(parametros.valor_rsi) > parametros.RSI_SOBREVENTA_MACD or parametros.valor_rsi < parametros.RSI_SOBRECOMPRA_MACD:
        parametros.log_operacion += f" └ RSI no cumple ({parametros.valor_rsi})\n"
    
    return None