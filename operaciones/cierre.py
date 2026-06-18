import time
import traceback
import configuracion.parametros as parametros
from archivos.seguimiento import actualizar_ultima_operacion, actualizar_estadisticas_cierre

def operacion_debe_cerrar():
    ejecutar_cierre = False
    operacion_ganada = False
    motivo_cierre = ""

    ejecutar_cierre, operacion_ganada, motivo_cierre = cierre_stop_loss(parametros.rendimiento_actual)    
    
    if not ejecutar_cierre:
        beneficio_neto = float(parametros.datos_mapeados['Beneficio Neto'])
        
        ejecutar_cierre, operacion_ganada, motivo_cierre = cierre_take_profit(beneficio_neto)
        
    return ejecutar_cierre, operacion_ganada, motivo_cierre

def ejecutar_cierre(driver, motivo_cierre):
    try:
        if not parametros.DEBUG:
            beneficio_neto = float(parametros.datos_mapeados['Beneficio Neto'])
        
            driver.execute_script(
                f"if (window.botonesCerrar && window.botonesCerrar.get('{parametros.activo_actual}')) {{ "
                f"    window.botonesCerrar.get('{parametros.activo_actual}').click(); "
                f"}}"
            )

            parametros.historico_cuenta.append(beneficio_neto)
            parametros.TIEMPO_ULTIMO_CIERRE = time.time()

            # Sincronizador de estadísticas con lectura de resultados reales
            if beneficio_neto > 0:
                actualizar_ultima_operacion(parametros.datos_mapeados, "Ganada", motivo_cierre)
                actualizar_estadisticas_cierre(True)
            else:
                actualizar_ultima_operacion(parametros.datos_mapeados, "Perdida", motivo_cierre)
                actualizar_estadisticas_cierre(False)
            
            parametros.maximo_rendimiento_alcanzado = 0.0
            parametros.TRAILING_STOP = 15.0
            parametros.DISTANCIA_TRAILING_MAXIMA = 4.0
            parametros.TAKE_PROFIT = 3.5
            parametros.STOP_LOSS  = -7.5
            parametros.trailing_activado = False

            time.sleep(2)
    except Exception as error_ejecucion:
        parametros.error += traceback.format_exc() + "\n"

def cierre_stop_loss(rendimiento_actual):
    beneficio_neto = float(parametros.datos_mapeados['Beneficio Neto'])
    
    if parametros.datos_mapeados['Operacion'] == "Compra" and float(parametros.valor_compra) <= float(parametros.STOP_LOSS):
        motivo_cierre = f"Stop Loss: {parametros.valor_compra} <= {float(parametros.STOP_LOSS):.2f}"
        operacion_ganada = False

        # Cuando es IA el trailing stop ha movido el stop loss, por lo que si el beneficio neto es > 0 entonces se aseguró ganancia
        if beneficio_neto > 0:
            motivo_cierre = f"Trailing Stop. Beneficio neto {beneficio_neto:.2f}"

        return True, operacion_ganada, motivo_cierre
    elif parametros.datos_mapeados['Operacion'] == "Venta" and float(parametros.valor_venta) >= float(parametros.STOP_LOSS):
        motivo_cierre = f"Stop Loss: {parametros.valor_venta} >= {float(parametros.STOP_LOSS):.2f}"
        operacion_ganada = False

        if beneficio_neto > 0:
            motivo_cierre = f"Trailing Stop. Beneficio neto {beneficio_neto:.2f}"

        return True, operacion_ganada, motivo_cierre

    return False, False, "Ejecutándose"

def cierre_take_profit(beneficio_neto):
    if beneficio_neto >= parametros.TAKE_PROFIT_USD:
        operacion_ganada = True
        motivo_cierre = f"Take Profit USD: ${beneficio_neto:.2f}"

        return True, operacion_ganada, motivo_cierre
    
    if parametros.datos_mapeados['Operacion'] == "Compra" and float(parametros.valor_compra) >= float(parametros.TAKE_PROFIT):
        motivo_cierre = f"Take Profit: {parametros.valor_compra} >= {float(parametros.TAKE_PROFIT):.2f}"
        operacion_ganada = True

        return True, operacion_ganada, motivo_cierre
    elif parametros.datos_mapeados['Operacion'] == "Venta" and float(parametros.valor_venta) <= float(parametros.TAKE_PROFIT):
        motivo_cierre = f"Take Profit: {parametros.valor_venta} <= {float(parametros.TAKE_PROFIT):.2f}"
        operacion_ganada = True

        return True, operacion_ganada, motivo_cierre

    return False, False, "Ejecutándose"