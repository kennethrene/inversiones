import re
import config

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
            config.valor_macd = f"{valor:.2f}"
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
                f"   Diferencia   : {config.valor_macd}\n"
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

            config.valor_bollinger_superior = float(valores_bollinger[0])
            config.valor_bollinger_media = float(valores_bollinger[1])
            config.valor_bollinger_inferior = float(valores_bollinger[2])

            return (
                f"{texto_separador}\n"
                f" 🧬 BANDAS DE BOLLINGER\n"
                f"  ───────────────────────────────────\n"
                f"   Banda superior : {config.valor_bollinger_superior}\n"
                f"   Banda media    : {config.valor_bollinger_media}\n"
                f"   Banda inferior : {config.valor_bollinger_inferior}\n"
            )

    return texto_bollinger_actual

def ui_rsi(parent_text_content, texto_componente, historico, texto_rsi_actual):
    if indicador_habilitado("RSI") and "RSI" in parent_text_content:
        decimales_rsi = re.findall(r'-?\d+\.\d+|-?\d+', texto_componente)
        if decimales_rsi:
            config.ultimo_valor_rsi = config.valor_rsi
            config.valor_rsi = float(decimales_rsi[-1])
            if float(config.valor_rsi) >= config.RSI_SOBRECOMPRA: valor_rsi = f"{config.valor_rsi:.2f} ⚠️"
            elif float(config.valor_rsi) <= config.RSI_SOBREVENTA: valor_rsi = f"{config.valor_rsi:.2f} ⚠️"
            else: valor_rsi = f"{config.valor_rsi:.2f}"            

            return (
                f"{texto_separador}\n"
                f" ⚛️  OSCILADOR RSI\n"
                f"  ───────────────────────────────────\n"
                f"   Valor actual : {valor_rsi}\n"
                f"   Histórico    : {historico}"
            )

    return texto_rsi_actual

def ui_adx(parent_text_content, texto_componente, texto_adx_actual):
    if "ADX" in parent_text_content:
        decimales_adx = re.findall(r'-?\d+\.\d+|-?\d+', texto_componente)
        if decimales_adx:
            config.valor_adx = float(decimales_adx[0])
            config.valor_adx_compra = float(decimales_adx[1])
            config.valor_adx_venta = float(decimales_adx[2])

            tendencia = "🔴 A LA BAJA" if config.valor_adx_compra < config.valor_adx_venta else "🟢 AL ALZA"

            if config.valor_adx >= config.ADX_TENDENCIA_FUERTE: 
                return (
                    f"{texto_separador}\n"
                    f" 🔋 ADX\n"
                    f"  ───────────────────────────────────\n"
                    f" 📊 IMPULSO ADX : {config.valor_adx:.2f} 🔥 (Tendencia Fuerte)\n"
                    f"\n"
                    f" 📈 TENDENCIA GENERAL : {tendencia}\n"
                )
            else:
                return (
                    f" 🔋 ADX\n"
                    f"  ───────────────────────────────────\n"
                    f" 📊 IMPULSO ADX : {config.valor_adx:.2f} 💤 (Mercado Lateral)\n"
                    f"\n"
                    f" 📈 TENDENCIA GENERAL : {tendencia}\n"
                )

    return texto_adx_actual

def ui_volumen(parent_text_content, texto_componente, texto_volumen_actual):
    if "VOL" in parent_text_content:
        if texto_componente != "n/a":
            config.valor_volumen = int(texto_componente)
            return (
                f"{texto_separador}\n"
                f" 🔋 VOLUMEN\n"
                f"  ───────────────────────────────────\n"
                f"    Actual                   : {config.valor_volumen}\n"
                f"    Ultimo                   : {config.ultimo_valor_volumen}\n"
                f"    Histórico                : {config.historico_volumen}\n"
                f"    Promedio                 : {config.promedio_volumen:.2f}\n"
                f"    Promedio sin el actual   : {config.promedio_volumen_sin_actual:.2f}"
            )
    
    return texto_volumen_actual

def ui_ema(parent_text_content, texto_componente, texto_ema_actual):
    if indicador_habilitado("EMA"):
        if "EMA [35" in parent_text_content:
            decimales_ema = re.findall(r'-?\d+\.\d+|-?\d+', texto_componente)
            if decimales_ema:
                config.valor_ema_35 = float(decimales_ema[0])
        
        if "EMA [50" in parent_text_content:
            decimales_ema = re.findall(r'-?\d+\.\d+|-?\d+', texto_componente)
            if decimales_ema:
                config.valor_ema_50 = float(decimales_ema[0])

        if config.valor_ema_35 != None and config.valor_ema_50 != None:
            return (
                f"{texto_separador}\n"
                f" 🔋 EMA\n"
                f"  ───────────────────────────────────\n"
                f" ⚡ EMA 35 : {config.valor_ema_35:.2f}\n"
                f" 🐢 EMA 50 : {config.valor_ema_50:.2f}\n"
            )

    return texto_ema_actual

def ui_trailing(habilitado, activo, rendimiento_actual, caida_desde_pico):
    if not habilitado:
        return (
            f"{texto_separador}\n"
            f" 🧭 TRAILING STOP\n"
            f"  ───────────────────────────────────\n"
            f"    Inactivo (Sin operaciones en ejecución)\n"
        )
    elif activo:
        return (
            f"{texto_separador}\n"
            f" 🧭 TRAILING STOP\n"
            f"  ───────────────────────────────────\n"
            f"   🔥 Activado\n"
            f"   🔥 Máximo rendimiento alcanzado : +{rendimiento_actual:.2f}%\n"
            f"   🔥 Caída desde el último pico   : {caida_desde_pico:.2f}%\n"
            f"   🔥 % Activación de trailing     : {config.PORCENTAJE_ACTIVACION_TRAILING}%\n"
            f"   🔥 % Trailing stop              : {config.DISTANCIA_TRAILING_MAXIMA}%\n"
        )
    else:
        return (
            f"{texto_separador}\n"
            f" 🧭 TRAILING STOP\n"
            f"  ───────────────────────────────────\n"
            f"   💤 Inactivo\n"
            f"   % Actual    : {rendimiento_actual:+.2f}%\n"
            f"   % Requerido : {config.PORCENTAJE_ACTIVACION_TRAILING}%\n"
        )

def ui_stop_loss(activo, rendimiento):
    if not activo:
        return (
            f"{texto_separador}\n"
            f" 🧭 STOP LOSS ACTUAL\n"
            f"  ───────────────────────────────────\n"
            f"   🔴 FIJADO: --\n"
            f"   🔴 ACTUAL: --\n"
        )
    else:
        return (
            f"{texto_separador}\n"
            f" 🧭 STOP LOSS ACTUAL\n"
            f"  ───────────────────────────────────\n"
            f"   🔴 FIJADO: {config.PORCENTAJE_STOP_LOSS:.1f}%\n"
            f"   🔴 ACTUAL: {rendimiento:+.2f}%\n"
        )

def ui_operacion_activa(activo, rendimiento_actual):
    if activo:
        icono_beneficio = "🟢" if rendimiento_actual >= 0 else "🔴"

        return (
            f"{texto_separador}\n"
            f"📌 [OPERACION]\n"
            f"  ───────────────────────────────────\n"
            f"   Operación          : {config.datos_mapeados["Operacion"]}\n"
            f"   💱 Instrumento     : {config.datos_mapeados['Activo']} ({config.datos_mapeados['Tipo']})\n"
            f"   📦 Volumen (Lotes) : {config.datos_mapeados['Volumen']}\n"
            f"   🚀 Precio Apertura : {config.datos_mapeados['Precio Apertura']}\n"
            f"   📊 Precio Actual   : {config.datos_mapeados['Precio Actual']}\n"
            f"   {icono_beneficio} Beneficio Neto  : {config.datos_mapeados['Beneficio Neto']} ({config.datos_mapeados['Beneficio %']})\n\n"
            f"   Log operación\n"
            f"  ───────────────────────────────────\n"
            f"   {config.log_operacion}\n"
        )
    else:
        return (
            f"{texto_separador}\n"
            f"📌 SIN OPERACIONES ACTIVAS\n"
            f"  ───────────────────────────────────\n"
            f"   {config.log_operacion}"
        )

def ui_estadisticas(motivo_cierre):
    win_rate = (config.estadisticas_bot["ganadas"] / config.estadisticas_bot["total_ordenes"] * 100) if config.estadisticas_bot["total_ordenes"] > 0 else 0.0

    return (
        f"{texto_separador}\n"
        " 📊 CUADRO DE ESTADISTICAS Y METRICAS DE EFECTIVIDAD (HOY):\n"
        f"    └ Operaciones Ganadas  🟢 : {config.estadisticas_bot['ganadas']}\n"
        f"    └ Operaciones Perdidas 🔴 : {config.estadisticas_bot['perdidas']}\n"
        f"    └ Total Ejecutadas     ⚡ : {config.estadisticas_bot['total_ordenes']}\n"
        f"    └ Porcentaje de Acierto🎯 : {win_rate:.1f}% Win Rate\n"
        f"    └ Histórico de la cuenta  : {config.historico_cuenta}\n"
        f"    └ Ultimo cierre           : {motivo_cierre}\n"
    )

def ui_general():
    return (
        f"{texto_separador}\n"
        f" 🏷️  ACTIVO              : {config.activo_actual}\n"
        f" 🔴 PRECIO ASK (VENTA)  : {config.valor_venta}\n"
        f" 🟢 PRECIO BID (COMPRA) : {config.valor_compra}\n"
        f" 🔢 LOTE                : {config.valor_lote}\n"
        f" 🟢 VALOR COMPRA ABRE   : {config.valor_compra_abrio}\n"
        f" 🔴 VALOR VENTA ABRE    : {config.valor_venta_abrio}\n"
    )

def ui_patrones():
    return (
        f"{texto_separador}\n"
        f" 📌 [PATRONES]\n"
        f"  ───────────────────────────────────\n"
        f" 🏷️  PATRON IDENTIFICADO     : {config.datos_graficos['patron']}\n"
        f" 🟢 ULTIMO PATRON DETECTADO : {config.ultimo_patron}\n\n"
        f"   Log operación\n"
        f"  ───────────────────────────────────"
        f"   {config.datos_graficos["log"]}"
    )

def indicador_habilitado(indicador):
    num_criterio = 0

    for criterio in config.CRITERIO_INDICADORES:
        if num_criterio == 0:
            num_criterio += 1
            continue

        criterio_general_activo = getattr(config, f"CRITERIO{num_criterio}", False)
        if criterio_general_activo and criterio.get(indicador.upper(), False):
            return True
        
        num_criterio += 1
    
    return False