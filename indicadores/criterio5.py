import config.config as config

# Cirterio 5: RSI decreciendo o creciendo en la zona de posible compra o venta
def ejecutar_criterio(rsi_creciendo, rsi_disminuyendo):
    if rsi_creciendo and config.valor_rsi > config.RSI_SOBREVENTA:
        config.log_operacion = f"ℹ️  Comprando por criterio 5: RSI creció y salió de la zona de sobreventa - ({config.historico_rsi}) RSI: {config.valor_rsi}"
        config.datos_mapeados["Criterio Apertura"] = "Criterio 5"
        return "Comprar"
    elif rsi_disminuyendo and config.valor_rsi < config.RSI_SOBRECOMPRA:
        config.log_operacion = f"ℹ️  Vendiendo por criterio 5: RSI disminuyó y salió de la zona de sobrecompra - ({config.historico_rsi}) RSI: {config.valor_rsi}"
        config.datos_mapeados["Criterio Apertura"] = "Criterio 5"
        return "Vender"
    
    config.log_operacion += "\n ❌  Criterio 5 no cumple\n"

    if not rsi_creciendo and not rsi_disminuyendo:
        config.log_operacion += f" └ RSI no disminuye ni crece uniformemente ({config.historico_rsi})\n"
    if rsi_creciendo and config.valor_rsi < config.RSI_SOBREVENTA:
        config.log_operacion += f" └ RSI creciendo pero esperando confirmación de salida de sobreventa - RSI: ({config.valor_rsi})\n"
    if rsi_disminuyendo and config.valor_rsi > config.RSI_SOBRECOMPRA:
        config.log_operacion += f" └ RSI disminuyendo pero esperando confirmación de salida de sobrecompra - RSI: ({config.valor_rsi})\n"
    
    return None