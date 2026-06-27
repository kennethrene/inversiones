import IA.IA as IA
import configuracion.parametros as parametros
import IA.configuracion as configuracion

parametros.activo_actual = "GOLD"
parametros.datos_mapeados['Operacion'] = 'Compra'
parametros.datos_mapeados['Precio Apertura'] = "30535.29"
parametros.historico_rsi = [10, 20]
parametros.TAKE_PROFIT = 30620
parametros.STOP_LOSS = 30420
parametros.TRAILING_STOP = 30560
parametros.diferencia_precio = 50

parametros.datos_mapeados["Patron"] = 'Doble Suelo'
parametros.datos_mapeados['Beneficio Neto'] = -6.97

configuracion.explicacion_decision = "VP=2.58 | RCL=6.27 | BCA=1 | Filtro=Lateral_Consolidacion | Tipo=Rango_Lateral"

apertura = True

if apertura:
    resultado = IA.ejecutar_operacion()
else:
    resultado = IA.reevaluar_operacion()

if resultado is None:
    print("No se ejecutó la IA")
else:
    if apertura:
        accion, take_profit, stop_loss, trailing_stop, velas_espera, valor_entrada, explicacion = resultado

        print(f"ℹ️  IA recomienda {accion}\n"
            f"      Valor de entrada    : {valor_entrada:.2f}\n"
            f"      Take profit         : {take_profit:.2f}\n"
            f"      Stop loss           : {stop_loss:.2f}\n"
            f"      Trailing Stop       : {trailing_stop:.2f}\n"
            f"      Explicación         : {explicacion}\n"
            f"      Próxima validación  : {velas_espera} velas")
    else:
        accion, take_profit, stop_loss, trailing_stop, velas_espera, explicacion = resultado

        print(f"ℹ️  IA recomienda {accion}\n"
            f"      Take profit         : {take_profit:.2f}\n"
            f"      Stop loss           : {stop_loss:.2f}\n"
            f"      Trailing Stop       : {trailing_stop:.2f}\n"
            f"      Explicación         : {explicacion}\n"
            f"      Próxima validación  : {velas_espera} velas")
