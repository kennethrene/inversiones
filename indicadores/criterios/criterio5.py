import configuracion.parametros as parametros

# Cirterio 5: RSI decreciendo o creciendo en la zona de posible compra o venta
def ejecutar_criterio(rsi_creciendo, rsi_disminuyendo):
    if rsi_creciendo and parametros.valor_rsi > parametros.RSI_SOBREVENTA:
        parametros.log_operacion = f"ℹ️  Comprando por criterio 5: RSI creció y salió de la zona de sobreventa - ({parametros.historico_rsi}) RSI: {parametros.valor_rsi}"
        parametros.datos_mapeados["Criterio Apertura"] = "Criterio 5"
        return "Comprar"
    elif rsi_disminuyendo and parametros.valor_rsi < parametros.RSI_SOBRECOMPRA:
        parametros.log_operacion = f"ℹ️  Vendiendo por criterio 5: RSI disminuyó y salió de la zona de sobrecompra - ({parametros.historico_rsi}) RSI: {parametros.valor_rsi}"
        parametros.datos_mapeados["Criterio Apertura"] = "Criterio 5"
        return "Vender"
    
    parametros.log_operacion += "\n ❌  Criterio 5 no cumple\n"

    if not rsi_creciendo and not rsi_disminuyendo:
        parametros.log_operacion += f" └ RSI no disminuye ni crece uniformemente ({parametros.historico_rsi})\n"
    if rsi_creciendo and parametros.valor_rsi < parametros.RSI_SOBREVENTA:
        parametros.log_operacion += f" └ RSI creciendo pero esperando confirmación de salida de sobreventa - RSI: ({parametros.valor_rsi})\n"
    if rsi_disminuyendo and parametros.valor_rsi > parametros.RSI_SOBRECOMPRA:
        parametros.log_operacion += f" └ RSI disminuyendo pero esperando confirmación de salida de sobrecompra - RSI: ({parametros.valor_rsi})\n"
    
    return None