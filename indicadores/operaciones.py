import config
from . import criterio1, criterio2, criterio3, criterio4, criterio5, criterio6

def ejecutar_operacion():
    if config.valor_rsi is not None and config.valor_adx is not None:
        config.log_operacion = ""
        rsi_confirmacion_venta = len(config.historico_rsi) > 1 and config.historico_rsi[-1] < config.RSI_SOBRECOMPRA
        rsi_confirmacion_compra = len(config.historico_rsi) > 1 and config.historico_rsi[-1] > config.RSI_SOBREVENTA

        tendencia_alcista = config.valor_adx_compra > config.valor_adx_venta
        tendencia_bajista = config.valor_adx_compra < config.valor_adx_venta

        macd_creciendo_alcista = len(config.historico_macd) > 2 and float(config.historico_macd[-1]) > float(config.historico_macd[-2]) and float(config.historico_macd[-2]) > float(config.historico_macd[-3])
        macd_disminuyendo_alcista = len(config.historico_macd) > 2 and float(config.historico_macd[-1]) < float(config.historico_macd[-2]) and float(config.historico_macd[-2]) < float(config.historico_macd[-3])

        macd_creciendo_bajista = len(config.historico_macd) > 2 and float(config.historico_macd[-1]) < float(config.historico_macd[-2]) and float(config.historico_macd[-2]) < float(config.historico_macd[-3])
        macd_disminuyendo_bajista = len(config.historico_macd) > 2 and float(config.historico_macd[-1]) < float(config.historico_macd[-2]) and float(config.historico_macd[-2]) < float(config.historico_macd[-3])

        rsi_creciendo = len(config.historico_rsi) > 2 and config.historico_rsi[-1] > 0 and float(config.historico_rsi[-1]) > float(config.historico_rsi[-2]) and float(config.historico_rsi[-2]) > float(config.historico_rsi[-3])
        rsi_disminuyendo = len(config.historico_rsi) > 2 and config.historico_rsi[-1] < 0 and float(config.historico_rsi[-1]) < float(config.historico_rsi[-2]) and float(config.historico_rsi[-2]) < float(config.historico_rsi[-3])

        if config.valor_adx >= config.ADX_TENDENCIA_FUERTE:
            if config.promedio_volumen_sin_actual >= config.VOL_ADECUADO_OPERAR:
                if config.CRITERIO1:
                    accion = criterio1.ejecutar_criterio()
                    if accion is not None:
                        return accion
                
                if config.CRITERIO2:
                    accion = criterio2.ejecutar_criterio(tendencia_alcista, tendencia_bajista)
                    if accion is not None:
                        return accion
                
                if config.CRITERIO3:
                    accion = criterio3.ejecutar_criterio(tendencia_alcista, tendencia_bajista, macd_creciendo_alcista, macd_disminuyendo_bajista)
                    if accion is not None:
                        return accion
                
                if config.CRITERIO4:
                    accion = criterio4.ejecutar_criterio(tendencia_alcista, tendencia_bajista)
                    if accion is not None:
                        return accion
                    
                if config.CRITERIO5:
                    accion = criterio5.ejecutar_criterio(rsi_creciendo, rsi_disminuyendo)
                    if accion is not None:
                        return accion
            else:
                config.log_operacion += f"❌  ADX fuerte pero Volumen muy bajo: {config.promedio_volumen_sin_actual} - Requerido: {config.VOL_ADECUADO_OPERAR}"

        if config.CRITERIO6:
            if config.promedio_volumen_sin_actual >= config.VOL_ADECUADO_OPERAR:
                accion = criterio6.ejecutar_criterio()
                if accion is not None:
                    return accion
                
    return ""