import config

# Criterio 3: MACD y Bollinger - La barra de MACD está creciendo ya sea bajista o alcista
def ejecutar_criterio(tendencia_alcista, tendencia_bajista, macd_creciendo_alcista, macd_disminuyendo_bajista):
    if macd_creciendo_alcista:
        config.log_operacion = config.log_operacion + f"\n ❌  ADX fuerte pero criterio 3 no cumple - {config.historico_macd}\n"
        config.datos_mapeados["Criterio Apertura"] = "Criterio 3"
        config.datos_mapeados["Operacion"] = "Compra"

        # Casi imposible que pase que el MACD sea verde, esté aumentando y esté por debajo de la banda inferior
        if tendencia_bajista and float(config.valor_compra) < float(config.valor_bollinger_inferior):
            config.PORCENTAJE_STOP_LOSS = -10
            config.TAKE_PROFIT_MONETARIO = 10
            config.PORCENTAJE_ACTIVACION_TRAILING = 20
            config.DISTANCIA_TRAILING_MAXIMA = 5
            config.log_operacion = f"ℹ️  Comprando por criterio 3 en tendencia bajista. Se espera resistencia en Bollinger inferior: {config.valor_compra} < {config.valor_bollinger_inferior} - MACD: {config.historico_macd} - Aumentando márgenes"
            return "Comprar"

        # Es tendencia alcista y el valor de compra está por encima de la banda superior y el valor actual de la compra es mayor que el valor con el que se abrió la vela
        # osea, no es una vela roja si no verde lo que indica que el precio tiende a subir, de lo contrario se está recuperando y viene un retroceso de bajada
        elif tendencia_alcista and float(config.valor_compra) > float(config.valor_bollinger_superior) and float(config.valor_compra_abrio) < float(config.valor_compra):
            config.PORCENTAJE_STOP_LOSS = -5
            config.TAKE_PROFIT_MONETARIO = 2
            config.PORCENTAJE_ACTIVACION_TRAILING = 5
            config.DISTANCIA_TRAILING_MAXIMA = 2
            config.log_operacion = f"ℹ️  Comprando por criterio 3 en tendencia alcista con valor de compra mayor a Bollinger superior {config.valor_compra} > {config.valor_bollinger_superior} - MACD: {config.historico_macd} - Reduciendo márgenes"
            return "Comprar"
        
        # Es tendencia alcista y el valor de compra está entre la banda media y la superior y adicionalmente el precio de compra está por encima del valor de compra con el que se abrió (vela verde), lo que indica que la tendencia
        # es seguir subiendo
        elif tendencia_alcista and float(config.valor_compra) > float(config.valor_bollinger_media) and float(config.valor_compra) > float(config.valor_compra_abrio):
            config.PORCENTAJE_STOP_LOSS = -10
            config.TAKE_PROFIT_MONETARIO = 3
            config.PORCENTAJE_ACTIVACION_TRAILING = 8
            config.DISTANCIA_TRAILING_MAXIMA = 4
            config.log_operacion = f"ℹ️  Comprando por criterio 3 en tendencia alcista con valor de compra superior a Bollinger media {config.valor_compra} > {config.valor_bollinger_media} - MACD: {config.historico_macd} - Reduciendo márgenes"
            return "Comprar"
    
        if tendencia_bajista and float(config.valor_compra) >= float(config.valor_bollinger_inferior):
            config.log_operacion += f" └ Tendencia bajista, precio lejos de la banda inferior para comprar: {config.valor_compra} >= {config.valor_bollinger_inferior}\n"
        if tendencia_alcista and float(config.valor_compra) <= float(config.valor_bollinger_superior):
            config.log_operacion += f" └ Tendencia alcista, precio no ha superado la banda superior para comprar: {config.valor_compra} <= {config.valor_bollinger_superior}\n"
        if tendencia_alcista and float(config.valor_compra) > float(config.valor_bollinger_superior) and float(config.valor_compra_abrio) > float(config.valor_compra):
            config.log_operacion += f" └ Tendencia alcista, precio ha superado la banda superior para comprar, pero la vela es roja y viene un retroceso: {config.valor_compra_abrio} > {config.valor_compra}\n"
        if tendencia_alcista and float(config.valor_compra) <= float(config.valor_bollinger_media):
            config.log_operacion += f" └ Tendencia alcista, precio por debajo de la banda media para comprar: {config.valor_compra} <= {config.valor_bollinger_media}\n"
        if tendencia_alcista and float(config.valor_compra) > float(config.valor_bollinger_media) and float(config.valor_compra) < float(config.valor_compra_abrio):
            config.log_operacion += f" └ Tendencia alcista, precio entre la banda media y superior para comprar, pero el valor de compra es menor que el valor con el que abrió (vela roja); se está retrocediendo: {config.valor_compra} <= {config.valor_compra_abrio}\n"

        config.datos_mapeados["Criterio Apertura"] = ""
        config.datos_mapeados["Operacion"] = ""
        
    elif macd_disminuyendo_bajista:
        config.log_operacion = config.log_operacion + f"\n ❌  ADX fuerte pero criterio 3 no cumple - {config.historico_macd}\n"
        config.datos_mapeados["Criterio Apertura"] = "Criterio 3"
        config.datos_mapeados["Operacion"] = "Venta"

        if tendencia_alcista and float(config.valor_venta) > float(config.valor_bollinger_superior):
            config.log_operacion = f"ℹ️  Vendiendo por criterio 3 en tendencia alcista. Se espera resistencia en Bollinger superior: {config.valor_venta} > {config.valor_bollinger_superior} - MACD: {config.historico_macd}"
            return "Vender"
        
        # Es tendencia bajista y el valor de venta está por debajo de la banda inferior y el valor actual de la venta es menor que el valor con el que se abrió la vela
        # osea, no es una vela verde si no roja lo que indica que el precio tiende a bajar, de lo contrario se está recuperando y viene un retroceso de subida
        elif tendencia_bajista and float(config.valor_venta) < float(config.valor_bollinger_inferior) and float(config.valor_venta_abrio) > float(config.valor_venta):
            config.PORCENTAJE_STOP_LOSS = -5
            config.TAKE_PROFIT_MONETARIO = 2
            config.PORCENTAJE_ACTIVACION_TRAILING = 5
            config.DISTANCIA_TRAILING_MAXIMA = 2
            config.log_operacion = f"ℹ️  Vendiendo por criterio 3 en tendencia bajista con valor de venta menor a Bollinger inferior {config.valor_venta} < {config.valor_bollinger_inferior} - MACD: {config.historico_macd} - Reduciendo márgenes"
            return "Vender"
        
        # Es tendencia bajista y el valor de venta está entre la banda media y la inferior y adicionalmente el precio de venta está por debajo del valor de venta con el que se abrió (vela roja), lo que indica que la tendencia
        # es seguir bajando
        elif tendencia_bajista and float(config.valor_venta) < float(config.valor_bollinger_media) and float(config.valor_venta) < float(config.valor_venta_abrio):
            config.PORCENTAJE_STOP_LOSS = -10
            config.TAKE_PROFIT_MONETARIO = 3
            config.PORCENTAJE_ACTIVACION_TRAILING = 8
            config.DISTANCIA_TRAILING_MAXIMA = 4
            config.log_operacion = f"ℹ️  Vendiendo por criterio 3 en tendencia bajista con valor de venta superior a Bollinger media {config.valor_venta} < {config.valor_bollinger_media} - MACD: {config.historico_macd} -  Reduciendo márgenes"
            return "Vender"
        
        if tendencia_alcista and float(config.valor_venta) <= float(config.valor_bollinger_superior):
            config.log_operacion += f" └ Tendencia alcista, precio lejos de la banda inferior para vender: {config.valor_venta} <= {config.valor_bollinger_superior}\n"
        if tendencia_bajista and float(config.valor_venta) >= float(config.valor_bollinger_inferior):
            config.log_operacion += f" └ Tendencia bajista, precio lejos de la banda inferior para vender: {config.valor_venta} >= {config.valor_bollinger_inferior}\n"
        if tendencia_bajista and float(config.valor_venta) < float(config.valor_bollinger_inferior) and float(config.valor_venta_abrio) < float(config.valor_venta):
            config.log_operacion += f" └ Tendencia bajista, precio ha superado la banda inferior para vender, pero la vela es verde y viene un retroceso: {config.valor_venta_abrio} < {config.valor_venta}\n"
        if tendencia_bajista and float(config.valor_venta) > float(config.valor_bollinger_media):
            config.log_operacion += f" └ Tendencia alcista, precio por encima de la banda media para vender: {config.valor_venta} > {config.valor_bollinger_media}\n"
        if tendencia_bajista and float(config.valor_venta) < float(config.valor_bollinger_media) and float(config.valor_venta) >= float(config.valor_venta):
            config.log_operacion += f" └ Tendencia alcista, precio entre la banda media e inferior para vender, pero el valor de venta es mayor que el valor con el que abrió (vela verde); se esta retrocediendo: {config.valor_venta} >= {config.valor_venta}\n"

        config.datos_mapeados["Criterio Apertura"] = ""
        config.datos_mapeados["Operacion"] = ""
    
    return None