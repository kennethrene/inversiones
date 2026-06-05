import time
import re
import configuracion.parametros as parametros
from indicadores.criterios import criterio1, criterio2, criterio3, criterio4, criterio5
from indicadores.criterios import criterio6
from ui.interfaz import ui_trailing
from archivos.seguimiento import guardar_estadistica
import IA.IA as IA
from datetime import datetime, timedelta

def debe_ejecutar_operacion():
    if not parametros.USAR_IA:
        if parametros.valor_rsi is not None and parametros.valor_adx is not None:
            parametros.log_operacion = ""
            rsi_confirmacion_venta = len(parametros.historico_rsi) > 1 and parametros.historico_rsi[-1] < parametros.RSI_SOBRECOMPRA
            rsi_confirmacion_compra = len(parametros.historico_rsi) > 1 and parametros.historico_rsi[-1] > parametros.RSI_SOBREVENTA

            tendencia_alcista = parametros.valor_adx_compra > parametros.valor_adx_venta
            tendencia_bajista = parametros.valor_adx_compra < parametros.valor_adx_venta

            macd_creciendo_alcista = len(parametros.historico_macd) > 2 and float(parametros.historico_macd[-1]) > float(parametros.historico_macd[-2]) and float(parametros.historico_macd[-2]) > float(parametros.historico_macd[-3])
            macd_disminuyendo_alcista = len(parametros.historico_macd) > 2 and float(parametros.historico_macd[-1]) < float(parametros.historico_macd[-2]) and float(parametros.historico_macd[-2]) < float(parametros.historico_macd[-3])

            macd_creciendo_bajista = len(parametros.historico_macd) > 2 and float(parametros.historico_macd[-1]) < float(parametros.historico_macd[-2]) and float(parametros.historico_macd[-2]) < float(parametros.historico_macd[-3])
            macd_disminuyendo_bajista = len(parametros.historico_macd) > 2 and float(parametros.historico_macd[-1]) < float(parametros.historico_macd[-2]) and float(parametros.historico_macd[-2]) < float(parametros.historico_macd[-3])

            rsi_creciendo = len(parametros.historico_rsi) > 2 and parametros.historico_rsi[-1] > 0 and float(parametros.historico_rsi[-1]) > float(parametros.historico_rsi[-2]) and float(parametros.historico_rsi[-2]) > float(parametros.historico_rsi[-3])
            rsi_disminuyendo = len(parametros.historico_rsi) > 2 and parametros.historico_rsi[-1] < 0 and float(parametros.historico_rsi[-1]) < float(parametros.historico_rsi[-2]) and float(parametros.historico_rsi[-2]) < float(parametros.historico_rsi[-3])

            if parametros.valor_adx >= parametros.ADX_TENDENCIA_FUERTE:
                if parametros.promedio_volumen_sin_actual >= parametros.VOL_ADECUADO_OPERAR:
                    if parametros.CRITERIO1:
                        accion = criterio1.ejecutar_criterio()
                        if accion is not None:
                            return accion
                    
                    if parametros.CRITERIO2:
                        accion = criterio2.ejecutar_criterio(tendencia_alcista, tendencia_bajista)
                        if accion is not None:
                            return accion
                    
                    if parametros.CRITERIO3:
                        accion = criterio3.ejecutar_criterio(tendencia_alcista, tendencia_bajista, macd_creciendo_alcista, macd_disminuyendo_bajista)
                        if accion is not None:
                            return accion
                    
                    if parametros.CRITERIO4:
                        accion = criterio4.ejecutar_criterio(tendencia_alcista, tendencia_bajista)
                        if accion is not None:
                            return accion
                        
                    if parametros.CRITERIO5:
                        accion = criterio5.ejecutar_criterio(rsi_creciendo, rsi_disminuyendo)
                        if accion is not None:
                            return accion
                else:
                    parametros.log_operacion += f"❌  ADX fuerte pero Volumen muy bajo: {parametros.promedio_volumen_sin_actual} - Requerido: {parametros.VOL_ADECUADO_OPERAR}"

            if parametros.CRITERIO6:
                if parametros.promedio_volumen_sin_actual >= parametros.VOL_ADECUADO_OPERAR:
                    accion = criterio6.ejecutar_criterio()
                    if accion is not None:
                        return accion
    else:
        now = datetime.now()

        if now.minute % parametros.TEMPORALIDAD_MINUTOS == 0 and now.second == 0:
            accion, patron, confianza, explicacion, take_profit, stop_loss, trailing_stop, valor_entrada, velas_espera, puntos_control = IA.ejecutar_operacion()

            if accion != "Mantener":
                # Ajustar valores de TradingView a los valores de XTB                
                diferencia_take_profit = abs(float(valor_entrada) - float(take_profit))
                diferencia_trailing_stop = abs(float(valor_entrada) - float(trailing_stop))
                diferencia_stop_loss = abs(float(valor_entrada) - float(stop_loss))
                parametros.velas_espera = velas_espera

                if accion == "Comprar":
                    parametros.diferencia_precio = abs(float(parametros.valor_compra) - float(valor_entrada))
                    take_profit_ajustado = float(parametros.valor_compra) + diferencia_take_profit
                    trailing_stop_ajustado = float(parametros.valor_compra) + diferencia_trailing_stop
                    stop_loss_ajustado = float(parametros.valor_compra) - diferencia_stop_loss
                elif accion == "Vender":
                    parametros.diferencia_precio = abs(float(parametros.valor_venta) - float(valor_entrada))
                    take_profit_ajustado = float(parametros.valor_venta) - diferencia_take_profit
                    trailing_stop_ajustado = float(parametros.valor_venta) - diferencia_trailing_stop
                    stop_loss_ajustado = float(parametros.valor_venta) + diferencia_stop_loss

                parametros.datos_mapeados["Criterio Apertura"] = "Criterio IA"
                parametros.datos_mapeados["Patron"] = patron
                hora_proxima_validacion = datetime.now() + timedelta(minutes=int(parametros.velas_espera) * 5)
                parametros.log_operacion = (
                        f"ℹ️  IA recomienda {accion}\n"
                        f"      Patrón              : {patron}\n"
                        f"      Confianza           : {confianza}\n"
                        f"      Take profit         : {take_profit_ajustado:.2f}\n"
                        f"      Stop loss           : {stop_loss_ajustado:.2f}\n"
                        f"      Trailing Stop       : {trailing_stop_ajustado:.2f}\n"
                        f"      Explicación         : {explicacion}\n"
                        f"      Puntos de control   : {puntos_control}\n"
                        f"      Próxima validación  : {parametros.velas_espera} velas ({hora_proxima_validacion.strftime('%H:%M')})"
                )
                parametros.TAKE_PROFIT = take_profit_ajustado
                parametros.STOP_LOSS = stop_loss_ajustado
                parametros.STOP_LOSS_INICIAL_TRAILING = stop_loss_ajustado
                parametros.TRAILING_STOP = trailing_stop_ajustado
                parametros.DISTANCIA_TRAILING_MAXIMA = abs(parametros.STOP_LOSS - parametros.TRAILING_STOP)
                parametros.explicacion_decision = f"{explicacion}. Puntos de control: {puntos_control}"
                return accion
            else:
                parametros.log_operacion = (
                    f"ℹ️  IA recomienda {accion}\n"
                    f"      Patrón: {patron}\n"
                    f"      Explicación: {explicacion}"
                )
                
    return ""

def validar_trailing_stop():
    try:
        texto_porcentaje = str(parametros.datos_mapeados["Beneficio %"]).replace("%", "").replace(" ", "").replace(",", ".")
        match_pct = re.search(r'([-+]?\d+\.\d+|-?\d+)', texto_porcentaje)
        parametros.rendimiento_actual = float(match_pct.group(1)) if match_pct else 0.0
    except:
        parametros.rendimiento_actual = 0.0

    if parametros.rendimiento_actual > parametros.maximo_rendimiento_alcanzado:
        parametros.maximo_rendimiento_alcanzado = parametros.rendimiento_actual
        
    if not parametros.USAR_IA and parametros.maximo_rendimiento_alcanzado >= parametros.TRAILING_STOP:
        parametros.trailing_activado = True
    elif parametros.USAR_IA:
        if parametros.datos_mapeados['Operacion'] == "Compra" and float(parametros.valor_compra) >= float(parametros.TRAILING_STOP):
            parametros.trailing_activado = True
        if parametros.datos_mapeados['Operacion'] == "Venta" and float(parametros.valor_venta) <= float(parametros.TRAILING_STOP):
            parametros.trailing_activado = True

        
    if not parametros.USAR_IA:
        if parametros.trailing_activado:
            caida_desde_pico = parametros.maximo_rendimiento_alcanzado - parametros.rendimiento_actual
            return ui_trailing(True, True, caida_desde_pico)
        else:
            return ui_trailing(True, False, None)
    elif parametros.USAR_IA:
        if parametros.trailing_activado:
            if parametros.datos_mapeados['Operacion'] == "Compra" and float(parametros.valor_compra) > float(parametros.TRAILING_STOP):
                nuevo_stop_loss = float(parametros.valor_compra) - float(parametros.DISTANCIA_TRAILING_MAXIMA)

                if float(nuevo_stop_loss) > float(parametros.STOP_LOSS):
                    parametros.STOP_LOSS = nuevo_stop_loss
            if parametros.datos_mapeados['Operacion'] == "Venta" and float(parametros.valor_venta) < float(parametros.TRAILING_STOP):
                nuevo_stop_loss = float(parametros.valor_venta) + float(parametros.DISTANCIA_TRAILING_MAXIMA)

                if float(nuevo_stop_loss) < float(parametros.STOP_LOSS):
                    parametros.STOP_LOSS = nuevo_stop_loss
            
        return ui_trailing(True, True, None)
    
    return ""

def reevaluar_operacion():
    if parametros.USAR_IA:
        now = datetime.now()

        if now.minute % (int(parametros.TEMPORALIDAD_MINUTOS) * int(parametros.velas_espera)) == 0 and now.second == 0:
            accion, patron, confianza, explicacion, take_profit, stop_loss, trailing_stop, valor_entrada, velas_espera, puntos_control = IA.reevaluar_operacion()
            parametros.velas_espera = velas_espera

            if accion != "Mantener":
                if accion == "Cerrar":
                    return "Cerrar", f"IA recomienda cerrar: {explicacion}"
                
                # Ajustar operación actual
                # Ajustar valores de TradingView a los valores de XTB                
                take_profit_ajustado = abs(float(parametros.diferencia_precio) + float(take_profit))
                trailing_stop_ajustado = abs(float(parametros.diferencia_precio) + float(trailing_stop))
                stop_loss_ajustado = abs(float(parametros.diferencia_precio) + float(stop_loss))
                hora_proxima_validacion = datetime.now() + timedelta(minutes=int(parametros.velas_espera) * 5)

                parametros.log_operacion = (
                    f"ℹ️  IA ajustando\n"
                    f"      Patrón              : {patron}\n"
                    f"      Confianza           : {confianza}\n"
                    f"      Take profit         : {take_profit_ajustado:.2f}\n"
                    f"      Stop loss           : {stop_loss_ajustado:.2f}\n"
                    f"      Trailing Stop       : {trailing_stop_ajustado:.2f}\n"
                    f"      Explicación         : {explicacion}\n"
                    f"      Puntos de control   : {puntos_control}\n"
                    f"      Próxima validación  : {parametros.velas_espera} velas ({hora_proxima_validacion.strftime('%H:%M')})"
                )
                parametros.TAKE_PROFIT = take_profit_ajustado
                parametros.STOP_LOSS = stop_loss_ajustado
                parametros.STOP_LOSS_INICIAL_TRAILING = stop_loss_ajustado
                parametros.TRAILING_STOP = trailing_stop_ajustado
                parametros.DISTANCIA_TRAILING_MAXIMA = abs(parametros.STOP_LOSS - parametros.TRAILING_STOP)
                parametros.explicacion_decision = f"{explicacion}. Puntos de control: {puntos_control}"
                guardar_estadistica("Ajuste")
                return accion, f"ℹ️  IA recomienda ajustar: {explicacion}"
            else:
                hora_proxima_validacion = datetime.now() + timedelta(minutes=int(parametros.velas_espera) * 5)
                
                parametros.log_operacion = (
                    f"ℹ️  IA recomienda mantener\n"
                    f"      Explicación         : {explicacion}\n"
                    f"      Próxima validación  : {parametros.velas_espera} velas ({hora_proxima_validacion.strftime('%H:%M')})"
                )
    
    return "", ""


def ejecutar_operacion():
    operacion = debe_ejecutar_operacion()

    if not parametros.DEBUG:
        if parametros.boton_comprar and operacion == "Comprar":                            
                parametros.boton_comprar.click()
                parametros.bloqueo_ejecutar_orden = True
                parametros.minuto_ultima_orden = time.strftime('%M')
                parametros.hora_apertura_orden = time.time()
                parametros.datos_mapeados['Operacion'] = "Compra"
                guardar_estadistica("Compra")
        elif parametros.boton_vender and operacion == "Vender":                            
                parametros.boton_vender.click()
                parametros.bloqueo_ejecutar_orden = True
                parametros.minuto_ultima_orden = time.strftime('%M')
                parametros.hora_apertura_orden = time.time()
                parametros.datos_mapeados['Operacion'] = "Venta"
                guardar_estadistica("Venta")