import IA
import configuracion.parametros as parametros

parametros.activo_actual = "US100"
parametros.datos_mapeados['Operacion'] = 'Compra'
parametros.datos_mapeados['Precio Apertura'] = "30535.29"
parametros.historico_rsi = [10, 20]
parametros.TAKE_PROFIT = 30620
parametros.STOP_LOSS = 30420
parametros.TRAILING_STOP = 30560
parametros.diferencia_precio = 50

parametros.datos_mapeados["Patron"] = 'Doble Suelo'
parametros.datos_mapeados['Beneficio Neto'] = -6.97

#accion, patron, confianza, explicacion, take_profit, stop_loss, trailing_stop, valor_entrada, velas_espera, puntos_control = IA.ejecutar_operacion()
accion, patron, confianza, explicacion, take_profit, stop_loss, trailing_stop, valor_entrada, velas_espera, puntos_control = IA.reevaluar_operacion()

print(f"ℹ️  IA recomienda {accion}. Patrón: {patron} - Confianza: {confianza} - Take profit: {take_profit} - Stop loss: {stop_loss} -  Trailing Stop: {trailing_stop} - Velas de espera: {velas_espera} - Explicación: {explicacion}")
