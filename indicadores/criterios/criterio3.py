import configuracion.parametros as parametros

# Criterio 3: MACD y Bollinger - La barra de MACD está creciendo ya sea bajista o alcista
def ejecutar_criterio(tendencia_alcista, tendencia_bajista, macd_creciendo_alcista, macd_disminuyendo_bajista):
    porcentaje_bollinger_estrecho = 100 * (float(parametros.valor_bollinger_superior) - float(parametros.valor_bollinger_inferior)) / float(parametros.valor_bollinger_media)

    if  porcentaje_bollinger_estrecho > float(parametros.porcentaje_bollinger_estrecho[parametros.activo_actual]):
        if macd_creciendo_alcista:
            parametros.log_operacion = parametros.log_operacion + f"\n ❌  ADX fuerte pero criterio 3 no cumple - {parametros.historico_macd}\n"
            parametros.datos_mapeados["Criterio Apertura"] = "Criterio 3"
            parametros.datos_mapeados["Operacion"] = "Compra"
            banda_limite = float(parametros.valor_bollinger_media) + (float(parametros.valor_bollinger_superior) - float(parametros.valor_bollinger_media)) * parametros.PORCENTAJE_BOLLINGER_BANDA_MEDIA

            # Aumentando MACD y valor de compra por debajo de la banda inferior
            if tendencia_bajista and float(parametros.valor_compra) < float(parametros.valor_bollinger_inferior):
                parametros.STOP_LOSS = -10
                parametros.TAKE_PROFIT = 10
                parametros.TRAILING_STOP = 20
                parametros.DISTANCIA_TRAILING_MAXIMA = 5
                parametros.log_operacion = f"ℹ️  Comprando por criterio 3 en tendencia bajista. Se espera resistencia en Bollinger inferior: {parametros.valor_compra} < {parametros.valor_bollinger_inferior} - MACD: {parametros.historico_macd} - Aumentando márgenes"
                return "Comprar"

            # Es tendencia alcista y el valor de compra está por encima de la banda superior y el valor actual de la compra es mayor que el valor con el que se abrió la vela
            # osea, no es una vela roja si no verde lo que indica que el precio tiende a subir, de lo contrario se está recuperando y viene un retroceso de bajada
            elif tendencia_alcista and float(parametros.valor_compra) > float(parametros.valor_bollinger_superior) and float(parametros.valor_compra_abrio) < float(parametros.valor_compra):
                parametros.STOP_LOSS = -5
                parametros.TAKE_PROFIT = 2
                parametros.TRAILING_STOP = 5
                parametros.DISTANCIA_TRAILING_MAXIMA = 2
                parametros.log_operacion = f"ℹ️  Comprando por criterio 3 en tendencia alcista con valor de compra mayor a Bollinger superior {parametros.valor_compra} > {parametros.valor_bollinger_superior} - MACD: {parametros.historico_macd} - Reduciendo márgenes"
                return "Comprar"
            
            # Es tendencia alcista y el valor de compra está entre la banda media y la superior
            # El precio de compra está por encima del valor de compra con el que se abrió (vela verde), lo que indica que la tendencia es seguir subiendo
            # El precio de compra está entre la banda media y el PORCENTAJE_BOLLINGER_BANDA_MEDIA de la superior
            elif tendencia_alcista and float(parametros.valor_compra) > float(parametros.valor_bollinger_media) \
                    and float(parametros.valor_compra) < banda_limite \
                    and float(parametros.valor_compra) > float(parametros.valor_compra_abrio):
                parametros.log_operacion = f"ℹ️  Comprando por criterio 3 en tendencia alcista con valor de venta entre Bollinger media y el límite configurado - {banda_limite} > {parametros.valor_compra} > {parametros.valor_bollinger_media} - MACD: {parametros.historico_macd}"
                return "Comprar"
            
            # Es tendencia alcista y el valor de compra está entre la banda media y la superior
            # El precio de compra está por encima del valor de compra con el que se abrió (vela verde), lo que indica que la tendencia es seguir subiendo
            # El precio de compra está entre el PORCENTAJE_BOLLINGER_BANDA_MEDIA y la banda superior
            elif tendencia_alcista and float(parametros.valor_compra) > float(parametros.valor_bollinger_media) \
                    and float(parametros.valor_compra) > banda_limite \
                    and float(parametros.valor_compra) > float(parametros.valor_compra_abrio):
                parametros.STOP_LOSS = -10
                parametros.TAKE_PROFIT = 3
                parametros.TRAILING_STOP = 8
                parametros.DISTANCIA_TRAILING_MAXIMA = 4
                parametros.log_operacion = f"ℹ️  Comprando por criterio 3 en tendencia alcista con valor de compra superior a Bollinger media {parametros.valor_compra} > {parametros.valor_bollinger_media} - MACD: {parametros.historico_macd} - Reduciendo márgenes"
                return "Comprar"
        
            if tendencia_bajista and float(parametros.valor_compra) >= float(parametros.valor_bollinger_inferior):
                parametros.log_operacion += f" └ Tendencia bajista, precio lejos de la banda inferior para comprar: {parametros.valor_compra} >= {parametros.valor_bollinger_inferior}\n"
            if tendencia_alcista and float(parametros.valor_compra) <= float(parametros.valor_bollinger_superior):
                parametros.log_operacion += f" └ Tendencia alcista, precio no ha superado la banda superior para comprar: {parametros.valor_compra} <= {parametros.valor_bollinger_superior}\n"
            if tendencia_alcista and float(parametros.valor_compra) > float(parametros.valor_bollinger_superior) and float(parametros.valor_compra_abrio) > float(parametros.valor_compra):
                parametros.log_operacion += f" └ Tendencia alcista, precio ha superado la banda superior para comprar, pero la vela es roja y viene un retroceso: {parametros.valor_compra_abrio} > {parametros.valor_compra}\n"
            if tendencia_alcista and float(parametros.valor_compra) <= float(parametros.valor_bollinger_media):
                parametros.log_operacion += f" └ Tendencia alcista, precio por debajo de la banda media para comprar: {parametros.valor_compra} <= {parametros.valor_bollinger_media}\n"
            if tendencia_alcista and float(parametros.valor_compra) > float(parametros.valor_bollinger_media) and float(parametros.valor_compra) < float(parametros.valor_compra_abrio):
                parametros.log_operacion += f" └ Tendencia alcista, precio entre la banda media y superior para comprar, pero el valor de compra es menor que el valor con el que abrió (vela roja); se está retrocediendo: {parametros.valor_compra} <= {parametros.valor_compra_abrio}\n"

            parametros.datos_mapeados["Criterio Apertura"] = ""
            parametros.datos_mapeados["Operacion"] = ""
            
        elif macd_disminuyendo_bajista:
            parametros.log_operacion = parametros.log_operacion + f"\n ❌  ADX fuerte pero criterio 3 no cumple - {parametros.historico_macd}\n"
            parametros.datos_mapeados["Criterio Apertura"] = "Criterio 3"
            parametros.datos_mapeados["Operacion"] = "Venta"
            banda_limite = float(parametros.valor_bollinger_media) - (float(parametros.valor_bollinger_media) - float(parametros.valor_bollinger_inferior)) * parametros.PORCENTAJE_BOLLINGER_BANDA_MEDIA

            # Disminuyendo MACD y valor de venta por encima de la banda superior
            if tendencia_alcista and float(parametros.valor_venta) > float(parametros.valor_bollinger_superior):
                parametros.STOP_LOSS = -10
                parametros.TAKE_PROFIT = 10
                parametros.TRAILING_STOP = 20
                parametros.DISTANCIA_TRAILING_MAXIMA = 5
                parametros.log_operacion = f"ℹ️  Vendiendo por criterio 3 en tendencia alcista. Se espera resistencia en Bollinger superior: {parametros.valor_venta} > {parametros.valor_bollinger_superior} - MACD: {parametros.historico_macd} - Aumentando márgenes"
                return "Vender"
            
            # Es tendencia bajista y el valor de venta está por debajo de la banda inferior y el valor actual de la venta es menor que el valor con el que se abrió la vela
            # osea, no es una vela verde si no roja lo que indica que el precio tiende a bajar, de lo contrario se está recuperando y viene un retroceso de subida
            elif tendencia_bajista and float(parametros.valor_venta) < float(parametros.valor_bollinger_inferior) and float(parametros.valor_venta_abrio) > float(parametros.valor_venta):
                parametros.STOP_LOSS = -5
                parametros.TAKE_PROFIT = 2
                parametros.TRAILING_STOP = 5
                parametros.DISTANCIA_TRAILING_MAXIMA = 2
                parametros.log_operacion = f"ℹ️  Vendiendo por criterio 3 en tendencia bajista con valor de venta menor a Bollinger inferior {parametros.valor_venta} < {parametros.valor_bollinger_inferior} - MACD: {parametros.historico_macd} - Reduciendo márgenes"
                return "Vender"
            
            # Es tendencia bajista y el valor de venta está entre la banda media y la inferior
            # El precio de venta está por debajo del valor de venta con el que se abrió (vela roja), lo que indica que la tendencia es seguir bajando
            # El precio de venta está entre la banda media y el PORCENTAJE_BOLLINGER_BANDA_MEDIA de la inferior
            elif tendencia_bajista and float(parametros.valor_venta) < float(parametros.valor_bollinger_media) \
                    and float(parametros.valor_venta) > banda_limite \
                    and float(parametros.valor_venta) < float(parametros.valor_venta_abrio):
                parametros.log_operacion = f"ℹ️  Vendiendo por criterio 3 en tendencia bajista con valor de venta entre Bollinger media y el límite configurado - {banda_limite} > {parametros.valor_venta} < {parametros.valor_bollinger_media} - MACD: {parametros.historico_macd}"
                return "Vender"

            # Es tendencia bajista y el valor de venta está entre la banda media y la inferior
            # El precio de venta está por debajo del valor de venta con el que se abrió (vela roja), lo que indica que la tendencia es seguir bajando
            # El precio de venta está entre el PORCENTAJE_BOLLINGER_BANDA_MEDIA y la banda inferior
            elif tendencia_bajista and float(parametros.valor_venta) < float(parametros.valor_bollinger_media) \
                    and float(parametros.valor_venta) < banda_limite \
                    and float(parametros.valor_venta) < float(parametros.valor_venta_abrio):
                parametros.STOP_LOSS = -10
                parametros.TAKE_PROFIT = 3
                parametros.TRAILING_STOP = 8
                parametros.DISTANCIA_TRAILING_MAXIMA = 4
                parametros.log_operacion = f"ℹ️  Vendiendo por criterio 3 en tendencia bajista con valor de venta menor que Bollinger media y entre límite y banda inferior {parametros.valor_venta} < {parametros.valor_bollinger_media} - MACD: {parametros.historico_macd} -  Reduciendo márgenes"
                return "Vender"
            
            if tendencia_alcista and float(parametros.valor_venta) <= float(parametros.valor_bollinger_superior):
                parametros.log_operacion += f" └ Tendencia alcista, precio lejos de la banda superior para vender: {parametros.valor_venta} <= {parametros.valor_bollinger_superior}\n"
            if tendencia_bajista and float(parametros.valor_venta) >= float(parametros.valor_bollinger_inferior):
                parametros.log_operacion += f" └ Tendencia bajista, precio lejos de la banda inferior para vender: {parametros.valor_venta} >= {parametros.valor_bollinger_inferior}\n"
            if tendencia_bajista and float(parametros.valor_venta) < float(parametros.valor_bollinger_inferior) and float(parametros.valor_venta_abrio) < float(parametros.valor_venta):
                parametros.log_operacion += f" └ Tendencia bajista, precio ha superado la banda inferior para vender, pero la vela es verde y viene un retroceso: {parametros.valor_venta_abrio} < {parametros.valor_venta}\n"
            if tendencia_bajista and float(parametros.valor_venta) > float(parametros.valor_bollinger_media):
                parametros.log_operacion += f" └ Tendencia alcista, precio por encima de la banda media para vender: {parametros.valor_venta} > {parametros.valor_bollinger_media}\n"
            if tendencia_bajista and float(parametros.valor_venta) < float(parametros.valor_bollinger_media) and float(parametros.valor_venta) >= float(parametros.valor_venta):
                parametros.log_operacion += f" └ Tendencia alcista, precio entre la banda media e inferior para vender, pero el valor de venta es mayor que el valor con el que abrió (vela verde); se esta retrocediendo: {parametros.valor_venta} >= {parametros.valor_venta}\n"

            parametros.datos_mapeados["Criterio Apertura"] = ""
            parametros.datos_mapeados["Operacion"] = ""
    else:
        parametros.log_operacion += f" Bollinger estrecho: {porcentaje_bollinger_estrecho:.2f} < {float(parametros.porcentaje_bollinger_estrecho[parametros.activo_actual])}\n"
    
    return None