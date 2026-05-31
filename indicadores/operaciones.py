import config.config as config
from . import criterio1, criterio2, criterio3, criterio4, criterio5, criterio6
import IA
from datetime import datetime

def ejecutar_operacion():
    if not config.USAR_IA:
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
    else:
        now = datetime.now()

        if now.minute % 5 == 0 and now.second == 0:
            accion, patron, confianza, explicacion, take_profit, stop_loss, trailing_stop, valor_entrada = IA.ejecutar_operacion()

            if accion != "Mantener":
                # Ajustar valores de TradingView a los valores de XTB
                diferencia_take_profit = abs(float(valor_entrada) - float(take_profit))
                diferencia_trailing_stop = abs(float(valor_entrada) - float(trailing_stop))
                diferencia_stop_loss = abs(float(valor_entrada) - float(stop_loss))

                if accion == "Comprar":
                    take_profit_ajustado = float(config.valor_compra) + diferencia_take_profit
                    trailing_stop_ajustado = float(config.valor_compra) + diferencia_trailing_stop
                    stop_loss_ajustado = float(config.valor_compra) - diferencia_stop_loss
                elif accion == "Vender":
                    take_profit_ajustado = float(config.valor_venta) - diferencia_take_profit
                    trailing_stop_ajustado = float(config.valor_venta) - diferencia_trailing_stop
                    stop_loss_ajustado = float(config.valor_venta) + diferencia_stop_loss

                config.datos_mapeados["Criterio Apertura"] = "Criterio IA"
                config.log_operacion = f"ℹ️  IA recomienda {accion}. Patrón: {patron} - Confianza: {confianza} - Take profit: {take_profit_ajustado} - Stop loss: {stop_loss_ajustado} -  Trailing Stop: {trailing_stop_ajustado}"
                config.TAKE_PROFIT = take_profit_ajustado
                config.STOP_LOSS = stop_loss_ajustado
                config.STOP_LOSS_INICIAL_TRAILING = stop_loss_ajustado
                config.TRAILING_STOP = trailing_stop_ajustado
                config.DISTANCIA_TRAILING_MAXIMA = abs(config.STOP_LOSS - config.TRAILING_STOP)
                return accion
            else:
                config.log_operacion = f"ℹ️  IA recomienda {accion}. Patrón: {patron} - Explicación: {explicacion}"
                
    return ""