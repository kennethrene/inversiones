import time
import re
import configuracion.parametros as parametros
from ui.interfaz import ui_trailing
from archivos.seguimiento import guardar_estadistica
import IA.IA as IA
from datetime import datetime, timedelta
import IA.configuracion as configuracion

def debe_ejecutar_operacion():
    now = datetime.now()

    if now.minute % parametros.TEMPORALIDAD_MINUTOS == 0 and now.second == 0:
        resultado = IA.ejecutar_operacion()

        if resultado is not None:
            accion, take_profit, stop_loss, trailing_stop, velas_espera, valor_entrada, explicacion = resultado

            if accion != "No Abrir":
                # Ajustar valores de TradingView a los valores de XTB
                diferencia_take_profit = abs(float(valor_entrada) - float(take_profit))
                diferencia_trailing_stop = abs(float(valor_entrada) - float(trailing_stop))
                diferencia_stop_loss = abs(float(valor_entrada) - float(stop_loss))
                parametros.velas_espera = velas_espera
                configuracion.explicacion_decision = explicacion

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
                hora_proxima_validacion = datetime.now() + timedelta(minutes=int(parametros.velas_espera) * 5)
                parametros.log_operacion = (
                        f"ℹ️  IA recomienda {accion}\n"
                        f"      Take profit         : {take_profit_ajustado:.2f}\n"
                        f"      Stop loss           : {stop_loss_ajustado:.2f}\n"
                        f"      Trailing Stop       : {trailing_stop_ajustado:.2f}\n"
                        f"      Explicación         : {explicacion}\n"
                        f"      Próxima validación  : {parametros.velas_espera} velas ({hora_proxima_validacion.strftime('%H:%M')})\n"
                        f"      Hora log            : {datetime.now().strftime('%H:%M')}"
                )
                parametros.TAKE_PROFIT = take_profit_ajustado
                parametros.STOP_LOSS = stop_loss_ajustado
                parametros.STOP_LOSS_INICIAL_TRAILING = stop_loss_ajustado
                parametros.TRAILING_STOP = trailing_stop_ajustado
                parametros.DISTANCIA_TRAILING_MAXIMA = abs(parametros.STOP_LOSS - parametros.TRAILING_STOP)
                return accion
            else:
                parametros.log_operacion = (
                    f"ℹ️  IA recomienda {accion}\n"
                    f"      Explicación         : {explicacion}\n"
                    f"      Hora log            : {datetime.now().strftime('%H:%M')}"
                )
        else:
            parametros.error += "No se ejecutó la IA\n"
    
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
        
    if parametros.datos_mapeados['Operacion'] == "Compra" and float(parametros.valor_compra) >= float(parametros.TRAILING_STOP):
        parametros.trailing_activado = True
    if parametros.datos_mapeados['Operacion'] == "Venta" and float(parametros.valor_venta) <= float(parametros.TRAILING_STOP):
        parametros.trailing_activado = True
        
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

def reevaluar_operacion():
    now = datetime.now()

    if int(parametros.velas_espera) == 0:
        parametros.velas_espera = 1

    if now.minute % (int(parametros.TEMPORALIDAD_MINUTOS) * int(parametros.velas_espera)) == 0 and now.second == 0:
        resultado = IA.reevaluar_operacion()

        if resultado is not None:
            accion, take_profit, stop_loss, trailing_stop, velas_espera, explicacion = resultado
            parametros.velas_espera = velas_espera

            if accion != "Mantener":
                if accion == "Cerrar":
                    return "Cerrar", f"IA recomienda cerrar: {explicacion} - Hora log: {datetime.now().strftime('%H:%M')}"
                
                # Ajustar operación actual
                # Ajustar valores de TradingView a los valores de XTB
                take_profit_ajustado = abs(float(parametros.diferencia_precio) + float(take_profit))
                trailing_stop_ajustado = abs(float(parametros.diferencia_precio) + float(trailing_stop))
                stop_loss_ajustado = abs(float(parametros.diferencia_precio) + float(stop_loss))
                hora_proxima_validacion = datetime.now() + timedelta(minutes=int(parametros.velas_espera) * 5)

                parametros.log_operacion = (
                    f"ℹ️  IA ajustando\n"
                    f"      Take profit         : {take_profit_ajustado:.2f}\n"
                    f"      Stop loss           : {stop_loss_ajustado:.2f}\n"
                    f"      Trailing Stop       : {trailing_stop_ajustado:.2f}\n"
                    f"      Explicación         : {explicacion}\n"
                    f"      Próxima validación  : {parametros.velas_espera} velas ({hora_proxima_validacion.strftime('%H:%M')})\n"
                    f"      Hora log            : {datetime.now().strftime('%H:%M')}"
                )
                parametros.TAKE_PROFIT = take_profit_ajustado
                parametros.STOP_LOSS = stop_loss_ajustado
                parametros.STOP_LOSS_INICIAL_TRAILING = stop_loss_ajustado
                parametros.TRAILING_STOP = trailing_stop_ajustado
                parametros.DISTANCIA_TRAILING_MAXIMA = abs(parametros.STOP_LOSS - parametros.TRAILING_STOP)
                configuracion.explicacion_decision = explicacion
                guardar_estadistica("Ajuste")
                return accion, f"ℹ️  IA recomienda ajustar: {explicacion} - Hora log: {datetime.now().strftime('%H:%M')}"
            else:
                hora_proxima_validacion = datetime.now() + timedelta(minutes=int(parametros.velas_espera) * 5)
                
                parametros.log_operacion = (
                    f"ℹ️  IA recomienda mantener\n"
                    f"      Explicación         : {explicacion}\n"
                    f"      Próxima validación  : {parametros.velas_espera} velas ({hora_proxima_validacion.strftime('%H:%M')})\n"
                    f"      Hora log            : {datetime.now().strftime('%H:%M')}"
                )
        else:
            parametros.error += f"No se ejecutó la IA -  Hora log: {datetime.now().strftime('%H:%M')}\n"
    
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