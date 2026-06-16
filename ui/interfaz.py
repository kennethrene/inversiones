import re
import os
import time
import configuracion.parametros as parametros

texto_separador = "-" * 75

def ui_macd(parent_text_content, texto_componente, historico, texto_macd_actual):
    if indicador_habilitado("MACD") and "MACD" in parent_text_content and "." in texto_componente:
        partes_macd = [p.strip() for p in texto_componente.split(".")]

        if len(partes_macd) >= 2:        
            decimales_macd = re.findall(r'-?\d+\.\d+|-?\d+', texto_componente)
            valor_compra = float(decimales_macd[0])
            valor_venta = float(decimales_macd[1])
            valor = valor_compra - valor_venta
            tendencia = "🔴 A LA BAJA" if valor < 0 else "🟢 AL ALZA"
            parametros.valor_macd = f"{valor:.2f}"
            if valor > 0:
                fuerza = "🔴 Tendencia Alcista Debilitándose" if len(historico) > 1 and historico[-1] < historico[-2] else  "🟢 Tendencia Alcista Fortaleciéndose"
            else:
                fuerza = "🔴 Tendencia Bajista Debilitándose" if len(historico) > 1 and historico[-1] > historico[-2] else  "🟢 Tendencia Bajista Fortaleciéndose"
            
            return (
                f"{texto_separador}\n"
                f" 📉 HISTOGRAMA MACD\n"
                f"  ───────────────────────────────────\n"
                #f"   Línea venta  : {valor_venta}\n"
                #f"   Línea compra : {valor_compra}\n"
                f"   Diferencia   : {parametros.valor_macd}\n"
                f"   Tendencia    : {tendencia}\n"
                f"   Histórico    : {historico}\n"
                f"   Fuerza       : {fuerza}"
            )

    return texto_macd_actual

def ui_bollinger(parent_text_content, texto_componente, texto_bollinger_actual):
    if indicador_habilitado("BOLLINGER") and "BOLLINGER [20, 2]" in parent_text_content and "." in texto_componente:
        partes_bollinger = [p.strip() for p in texto_componente.split(".")]

        if len(partes_bollinger) >= 3:        
            valores_bollinger = re.findall(r"\d+\.\d+", texto_componente)
            if len(valores_bollinger) == 0:
               valores_bollinger = partes_bollinger

            parametros.valor_bollinger_superior = float(valores_bollinger[0])
            parametros.valor_bollinger_media = float(valores_bollinger[1])
            parametros.valor_bollinger_inferior = float(valores_bollinger[2])

            porcentaje_bollinger_estrecho = 100 * (float(parametros.valor_bollinger_superior) - float(parametros.valor_bollinger_inferior)) / float(parametros.valor_bollinger_media)
            texto_estrecho = ""
            if float(porcentaje_bollinger_estrecho) < float(parametros.porcentaje_bollinger_estrecho[parametros.activo_actual]):
                texto_estrecho = f"🚧 Bandas de Bollinger estrechas -  {porcentaje_bollinger_estrecho:.2f} < {parametros.porcentaje_bollinger_estrecho[parametros.activo_actual]}\n" 

            return (
                f"{texto_separador}\n"
                f" 🧬 BANDAS DE BOLLINGER\n"
                f"  ───────────────────────────────────\n"
                f"   Banda superior : {parametros.valor_bollinger_superior}\n"
                f"   Banda media    : {parametros.valor_bollinger_media}\n"
                f"   Banda inferior : {parametros.valor_bollinger_inferior}\n"
                f"                    {texto_estrecho}"
            )

    return texto_bollinger_actual

def ui_rsi(parent_text_content, texto_componente, historico, texto_rsi_actual):
    if indicador_habilitado("RSI") and "RSI" in parent_text_content:
        decimales_rsi = re.findall(r'-?\d+\.\d+|-?\d+', texto_componente)
        if decimales_rsi:
            parametros.ultimo_valor_rsi = parametros.valor_rsi
            parametros.valor_rsi = float(decimales_rsi[-1])
            if float(parametros.valor_rsi) >= parametros.RSI_SOBRECOMPRA: valor_rsi = f"{parametros.valor_rsi:.2f} ⚠️"
            elif float(parametros.valor_rsi) <= parametros.RSI_SOBREVENTA: valor_rsi = f"{parametros.valor_rsi:.2f} ⚠️"
            else: valor_rsi = f"{parametros.valor_rsi:.2f}"            

            return (
                f"{texto_separador}\n"
                f" ⚛️  OSCILADOR RSI\n"
                f"  ───────────────────────────────────\n"
                f"   Valor actual : {valor_rsi}\n"
                f"   Histórico    : {historico}"
            )

    return texto_rsi_actual

def ui_adx(parent_text_content, texto_componente, texto_adx_actual):
    if indicador_habilitado("ADX") and "ADX" in parent_text_content:
        decimales_adx = re.findall(r'-?\d+\.\d+|-?\d+', texto_componente)
        if decimales_adx:
            parametros.valor_adx = float(decimales_adx[0])
            parametros.valor_adx_compra = float(decimales_adx[1])
            parametros.valor_adx_venta = float(decimales_adx[2])

            tendencia = "🔴 A LA BAJA" if parametros.valor_adx_compra < parametros.valor_adx_venta else "🟢 AL ALZA"

            if parametros.valor_adx >= parametros.ADX_TENDENCIA_FUERTE: 
                return (
                    f"{texto_separador}\n"
                    f" 🔋 ADX\n"
                    f"  ───────────────────────────────────\n"
                    f" 📊 IMPULSO ADX : {parametros.valor_adx:.2f} 🔥 (Tendencia Fuerte)\n"
                    f"\n"
                    f" 📈 TENDENCIA GENERAL : {tendencia}\n"
                )
            else:
                return (
                    f" 🔋 ADX\n"
                    f"  ───────────────────────────────────\n"
                    f" 📊 IMPULSO ADX : {parametros.valor_adx:.2f} 💤 (Mercado Lateral)\n"
                    f"\n"
                    f" 📈 TENDENCIA GENERAL : {tendencia}\n"
                )

    return texto_adx_actual

def ui_volumen(parent_text_content, texto_componente, texto_volumen_actual):
    if indicador_habilitado("VOL") and "VOL" in parent_text_content:
        if texto_componente != "n/a":
            parametros.valor_volumen = int(texto_componente)
            return (
                f"{texto_separador}\n"
                f" 🔋 VOLUMEN\n"
                f"  ───────────────────────────────────\n"
                f"    Actual                   : {parametros.valor_volumen}\n"
                f"    Ultimo                   : {parametros.ultimo_valor_volumen}\n"
                f"    Histórico                : {parametros.historico_volumen}\n"
                f"    Promedio                 : {parametros.promedio_volumen:.2f}\n"
                f"    Promedio sin el actual   : {parametros.promedio_volumen_sin_actual:.2f}"
            )
    
    return texto_volumen_actual

def ui_ema(parent_text_content, texto_componente, texto_ema_actual):
    if indicador_habilitado("EMA"):
        if "EMA [35" in parent_text_content:
            decimales_ema = re.findall(r'-?\d+\.\d+|-?\d+', texto_componente)
            if decimales_ema:
                parametros.valor_ema_35 = float(decimales_ema[0])
        
        if "EMA [50" in parent_text_content:
            decimales_ema = re.findall(r'-?\d+\.\d+|-?\d+', texto_componente)
            if decimales_ema:
                parametros.valor_ema_50 = float(decimales_ema[0])

        if parametros.valor_ema_35 != None and parametros.valor_ema_50 != None:
            return (
                f"{texto_separador}\n"
                f" 🔋 EMA\n"
                f"  ───────────────────────────────────\n"
                f" ⚡ EMA 35 : {parametros.valor_ema_35:.2f}\n"
                f" 🐢 EMA 50 : {parametros.valor_ema_50:.2f}\n"
            )

    return texto_ema_actual

def ui_trailing(habilitado, activo, caida_desde_pico):
    if not habilitado:
        return (
            f"{texto_separador}\n"
            f" 🧭 TRAILING STOP\n"
            f"  ───────────────────────────────────\n"
            f"    Inactivo (Sin operaciones en ejecución)\n"
        )
    
    if not parametros.USAR_IA:
        if activo:
            return (
                f"{texto_separador}\n"
                f" 🧭 TRAILING STOP\n"
                f"  ───────────────────────────────────\n"
                f"   🔥 Activado\n"
                f"   🔥 Máximo rendimiento alcanzado : +{parametros.maximo_rendimiento_alcanzado:.2f}%\n"
                f"   🔥 Caída desde el último pico   : {caida_desde_pico:.2f}%\n"
                f"   🔥 % Activación de trailing     : {parametros.TRAILING_STOP}%\n"
                f"   🔥 % Trailing stop              : {parametros.DISTANCIA_TRAILING_MAXIMA}%\n"
            )
        else:
            return (
                f"{texto_separador}\n"
                f" 🧭 TRAILING STOP\n"
                f"  ───────────────────────────────────\n"
                f"   💤 Inactivo\n"
                f"   % Actual    : {parametros.rendimiento_actual:+.2f}%\n"
                f"   % Requerido : {parametros.TRAILING_STOP}%\n"
            )
    else:
        return (
                f"{texto_separador}\n"
                f" 🧭 TRAILING STOP\n"
                f"  ───────────────────────────────────\n"
                f"   🔥 Activado\n"
                f"   🔥 Trailing Stop     : {parametros.TRAILING_STOP:.2f}\n"
                f"   🔥 Distancia Máxima  : {parametros.DISTANCIA_TRAILING_MAXIMA:.2f}\n"
                f"   🔥 Stop Loss inicial : {parametros.STOP_LOSS_INICIAL_TRAILING:.2f}\n"
                f"   🔥 Stop Loss actual  : {parametros.STOP_LOSS:.2f}\n"
            )

def ui_stop_loss(activo):
    if not activo:
        return (
            f"{texto_separador}\n"
            f" 🧭 STOP LOSS ACTUAL\n"
            f"  ───────────────────────────────────\n"
            f"   🔴 FIJADO: --\n"
            f"   🔴 ACTUAL: --\n"
        )
    elif not parametros.USAR_IA:
        return (
            f"{texto_separador}\n"
            f" 🧭 STOP LOSS ACTUAL\n"
            f"  ───────────────────────────────────\n"
            f"   🔴 FIJADO: {parametros.STOP_LOSS:.1f}%\n"
            f"   🔴 ACTUAL: {parametros.rendimiento_actual:+.2f}%\n"
        )
    elif parametros.USAR_IA:
        return (
            f"{texto_separador}\n"
            f" 🧭 STOP LOSS ACTUAL\n"
            f"  ───────────────────────────────────\n"
            f"   🔴 FIJADO: {parametros.STOP_LOSS:.1f}\n"
        )

def ui_operacion_activa(activo):
    if activo and parametros.activo_actual == parametros.datos_mapeados['Activo']:
        icono_beneficio = "🟢" if parametros.rendimiento_actual >= 0 else "🔴"

        return (
            f"{texto_separador}\n"
            f"📌 [OPERACION]\n"
            f"  ───────────────────────────────────\n"
            f"   Operación          : {parametros.datos_mapeados['Operacion']}\n"
            f"   💱 Instrumento     : {parametros.datos_mapeados['Activo']} ({parametros.datos_mapeados['Tipo']})\n"
            f"   📦 Volumen (Lotes) : {parametros.datos_mapeados['Volumen']}\n"
            f"   🚀 Precio Apertura : {float(parametros.datos_mapeados['Precio Apertura'].replace(' ', ''))}\n"
            f"   📊 Precio Actual   : {float(parametros.datos_mapeados['Precio Actual'].replace(' ', ''))}\n"
            f"   {icono_beneficio} Beneficio Neto  : {parametros.datos_mapeados['Beneficio Neto']} ({parametros.datos_mapeados['Beneficio %']})\n\n"
            f"   Log operación\n"
            f"  ───────────────────────────────────\n"
            f"   {parametros.log_operacion}\n"
        )
    else:
        return (
            f"{texto_separador}\n"
            f"📌 SIN OPERACIONES ACTIVAS PARA {parametros.activo_actual}\n"
            f"  ───────────────────────────────────\n"
            f"   {parametros.log_operacion}"
        )

def ui_estadisticas(motivo_cierre):
    win_rate = (parametros.estadisticas_bot["ganadas"] / parametros.estadisticas_bot["total_ordenes"] * 100) if parametros.estadisticas_bot["total_ordenes"] > 0 else 0.0

    return (
        f"{texto_separador}\n"
        " 📊 CUADRO DE ESTADISTICAS Y METRICAS DE EFECTIVIDAD (HOY):\n"
        f"    └ Operaciones Ganadas  🟢 : {parametros.estadisticas_bot['ganadas']}\n"
        f"    └ Operaciones Perdidas 🔴 : {parametros.estadisticas_bot['perdidas']}\n"
        f"    └ Total Ejecutadas     ⚡ : {parametros.estadisticas_bot['total_ordenes']}\n"
        f"    └ Porcentaje de Acierto🎯 : {win_rate:.1f}% Win Rate\n"
        f"    └ Histórico de la cuenta  : {parametros.historico_cuenta}\n"
        f"    └ Ultimo cierre           : {motivo_cierre}\n"
    )

def ui_datos_generales():
    return (
        f"{texto_separador}\n"
        f" 🏷️  ACTIVO              : {parametros.activo_actual}\n"
        f" 🔴 PRECIO ASK (VENTA)  : {parametros.valor_venta}\n"
        f" 🟢 PRECIO BID (COMPRA) : {parametros.valor_compra}\n"
        f" 🔢 LOTE                : {parametros.valor_lote}\n"
        f" 🟢 VALOR COMPRA ABRE   : {parametros.valor_compra_abrio}\n"
        f" 🔴 VALOR VENTA ABRE    : {parametros.valor_venta_abrio}\n"
    )

def ui_patrones():
    return (
        f"{texto_separador}\n"
        f" 📌 [PATRONES]\n"
        f"  ───────────────────────────────────\n"
        f" 🏷️  PATRON IDENTIFICADO     : {parametros.datos_graficos['patron']}\n"
        f" 🟢 ULTIMO PATRON DETECTADO : {parametros.ultimo_patron}\n\n"
        f"   Log operación\n"
        f"  ───────────────────────────────────"
        f"   {parametros.datos_graficos['log']}"
    )

def indicador_habilitado(indicador):
    num_criterio = 0

    for criterio in parametros.CRITERIO_INDICADORES:
        if num_criterio == 0:
            num_criterio += 1
            continue

        criterio_general_activo = getattr(parametros, f"CRITERIO{num_criterio}", False)
        if criterio_general_activo and criterio.get(indicador.upper(), False):
            return True
        
        num_criterio += 1
    
    return False

# IMPRESIÓN ACTUALIZADA EN LA CONSOLA
def ui_general(texto_indicadores, operacion_activa, texto_operacion_activa, texto_trailing, texto_stop_loss, motivo_cierre):
    limpiar_pantalla()
    print("-" * 75)
    print(f" ROBOT OPERATIVO AUTOMÁTICO XTB | MONITOR DE RIESGO % NATIVO FIXED")
    print(f" Servidor activo: {time.strftime('%H:%M:%S')}")
    print(f"{ui_datos_generales()}")
    print(f"{texto_indicadores}")
    print(f"{texto_operacion_activa}")
    print(f"{texto_trailing}")
    print(f"{texto_stop_loss}")
    print("-" * 75)
    print(f" 💰 TAKE PROFIT     : {parametros.TAKE_PROFIT:.2f}")
    print(f" 💰 TAKE PROFIT USD : {parametros.TAKE_PROFIT_USD:.2f}")
    print("-" * 75)
    print(f" 🚦 FILTRO ENTRADAS : {'🔒 BLOQUEADO (Operación detectada)' if operacion_activa else '🔓 EN ESPERA DE SEÑAL'}")
    print(f"{ui_estadisticas(motivo_cierre)}")
    print("=" * 75)
    print(f" 🔴 Ultimo error              : {parametros.error}")
    print("=" * 75)

def limpiar_pantalla():
    if os.name == 'nt':
        os.system('cls')
    else:
        # Funciona en Mac (Terminal nativa, VS Code, iTerm2) y Linux
        print("\033[H\033[2J\033[3J", end="", flush=True)