import IA.IA as IA
import configuracion.parametros as parametros
import IA.configuracion as configuracion

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

configuracion.proximas_instrucciones = "SI el Close de la Vela 0 rompe el Mínimo Absoluto (28619.29) con una mecha inferior <= 0.1x cuerpo y tamaño de cuerpo >= 1.2x VP (152.82), ENTONCES ejecutar Venta. SI el precio rebota y forma un Martillo en el Mínimo Absoluto, ENTONCES ejecutar Compra."

#resultado = IA.ejecutar_operacion()
resultado = IA.reevaluar_operacion()
if resultado is None:
    print("No se ejecutó la IA")
else:
    accion, patron, confianza, explicacion, take_profit, stop_loss, trailing_stop, valor_entrada, velas_espera, puntos_control = resultado

    #print(f"ℹ️  IA recomienda {accion}. Patrón: {patron} - Confianza: {confianza} - Take profit: {take_profit} - Stop loss: {stop_loss} -  Trailing Stop: {trailing_stop} - Velas de espera: {velas_espera} - Explicación: {explicacion} -  Próximas instrucciones: {instrucciones}")
    print(f"ℹ️  IA recomienda {accion}. Patrón: {patron} - Confianza: {confianza} - Take profit: {take_profit} - Stop loss: {stop_loss} -  Trailing Stop: {trailing_stop} - Velas de espera: {velas_espera} - Explicación: {explicacion}")
