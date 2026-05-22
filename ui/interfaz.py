import re
import config

def ui_macd(parent_text_content, texto_componente, historico, texto_macd_actual):
    if "MACD" in parent_text_content and "." in texto_componente:
        partes_macd = [p.strip() for p in texto_componente.split(".")]

        if len(partes_macd) >= 2:        
            decimales_macd = re.findall(r'-?\d+\.\d+|-?\d+', texto_componente)
            valor_compra = float(decimales_macd[0])
            valor_venta = float(decimales_macd[1])
            valor = valor_compra - valor_venta
            tendencia = "🔴 A LA BAJA" if valor < 0 else "🟢 AL ALZA"
            config.valor_macd = f"{valor:.2f}"
            
            return (
                f" 📉 HISTOGRAMA MACD\n"
                f"  ───────────────────────────────────\n"
                f"   Línea venta  : {valor_venta}\n"
                f"   Línea compra : {valor_compra}\n"
                f"   Diferencia   : {config.valor_macd}\n"
                f"   Tendencia    : {tendencia}\n"
                f"   Histórico    : {historico}"
            )

    return texto_macd_actual

def ui_rsi(parent_text_content, texto_componente, historico, texto_rsi_actual):
    if "RSI" in parent_text_content:
        decimales_rsi = re.findall(r'-?\d+\.\d+|-?\d+', texto_componente)
        if decimales_rsi:
            config.valor_rsi = float(decimales_rsi[-1])
            if config.valor_rsi >= config.RSI_SOBRECOMPRA: rsi_valor = f"{config.valor_rsi:.2f} ⚠️"
            elif config.valor_rsi <= config.RSI_SOBREVENTA: rsi_valor = f"{config.valor_rsi:.2f} ⚠️"
            else: rsi_valor = f"{config.valor_rsi:.2f}"

            return (
                f" ⚛️  OSCILADOR RSI\n"
                f"  ───────────────────────────────────\n"
                f"   Valor actual : {rsi_valor}\n"
                f"   Histórico    : {historico}"
            )

    return texto_rsi_actual

def ui_adx(parent_text_content, texto_componente, texto_adx_actual):
    if "ADX" in parent_text_content:
        decimales_adx = re.findall(r'-?\d+\.\d+|-?\d+', texto_componente)
        if decimales_adx:
            config.valor_adx = float(decimales_adx[0])
            if config.valor_adx >= config.ADX_TENDENCIA_FUERTE: 
                return f" 📊 IMPULSO ADX : {config.valor_adx:.2f} 🔥 (Tendencia Fuerte)"
            else: 
                return f" 📊 IMPULSO ADX : {config.valor_adx:.2f} 💤 (Mercado Lateral)"

    return texto_adx_actual
