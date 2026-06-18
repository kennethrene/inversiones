from extraccion.velas import extraer_velas_para_IA, extraer_velas_para_indicadores
from extraccion.indicadores import obtener_datos_indicadores
import configuracion.parametros as parametros
import IA.configuracion as configuracion
from typing import Dict, Any, Optional
from tvDatafeed import Interval
import importlib
import IA.gemini as gemini
import IA.groq as groq

def ejecutar_operacion():
    num_velas = 1
    configuracion_prompt = obtener_prompts_estrategia_activa(configuracion.TIPO_PROMPT)

    if not configuracion_prompt["indicadores"]:
        if len(parametros.lista_velas_acumuladas) == 0:
            num_velas = 61

        velas = extraer_velas_para_IA(parametros.activo_actual, Interval.in_5_minute, num_velas)
    else:
        if len(parametros.lista_velas_acumuladas) == 0:
            num_velas = 121
        
        velas, _ = obtener_datos_indicadores(extraer_velas_para_indicadores(parametros.activo_actual, Interval.in_5_minute, num_velas))

    if velas is not None and len(velas) > 0:
        nombre_ia, modelo, cache = obtener_modelo_ia_activo(configuracion.MODELO_IA)

        if not configuracion_prompt["indicadores"]:
            velas = formatear_velas_para_ia(velas)
        else:
            velas = formatear_indicadores_para_ia(velas)

        if cache:
            prompt_apertura = importlib.import_module(f"IA.prompts.apertura.{nombre_ia}.{configuracion_prompt['version_apertura_cache']}_CACHE")
            prompt = getattr(prompt_apertura, configuracion_prompt["apertura"])
        else:
            prompt_apertura = importlib.import_module(f"IA.prompts.apertura.{nombre_ia}.{configuracion_prompt['version_apertura']}")
            obtener_datos_filtro = getattr(prompt_apertura,"obtener_datos_filtro")
            inputs_filtrados = obtener_datos_filtro(velas)
            prompt_plantilla = getattr(prompt_apertura, configuracion_prompt["apertura"])
            prompt = prompt_plantilla.format(**inputs_filtrados)

        esquema = getattr(prompt_apertura, "Esquema")
        
        if nombre_ia == "Gemini":
            objeto_validado = gemini.ejecutar_prompt(modelo, prompt, cache, True, None, velas, esquema)

        elif nombre_ia == "Groq":
            objeto_validado = groq.ejecutar_prompt(modelo, prompt, esquema, True)

        if objeto_validado is not None:
            accion          = objeto_validado.a
            take_profit     = objeto_validado.tp
            stop_loss       = objeto_validado.sl
            trailing_stop   = objeto_validado.ts
            velas_espera    = objeto_validado.v
            valor_entrada   = objeto_validado.pe
            explicacion     = objeto_validado.p

            parametros.datos_fuente_velas["Valor Apertura"] = valor_entrada
            parametros.datos_fuente_velas["Stop Loss"] = stop_loss
            parametros.datos_fuente_velas["Take Profit"] = take_profit
            parametros.datos_fuente_velas["Trailing Stop"] = trailing_stop
            
            return (accion, take_profit, stop_loss, trailing_stop, velas_espera, valor_entrada, explicacion)
        else:
            return None
    else:
        parametros.error = "IA - No se recibieron datos de velas\n"

def reevaluar_operacion():
    num_velas = parametros.velas_espera

    configuracion_prompt = obtener_prompts_estrategia_activa(configuracion.TIPO_PROMPT)

    if not configuracion_prompt["indicadores"]:
        if len(parametros.lista_velas_acumuladas) == 0:
            num_velas = 61

        velas = extraer_velas_para_IA(parametros.activo_actual, Interval.in_5_minute, num_velas)
    else:
        if len(parametros.lista_velas_acumuladas) == 0:
            num_velas = 121
        
        velas, _ = obtener_datos_indicadores(extraer_velas_para_indicadores(parametros.activo_actual, Interval.in_5_minute, num_velas))

    if velas is not None and len(velas) > 0:
        nombre_ia, modelo, cache = obtener_modelo_ia_activo(configuracion.MODELO_IA)
        
        if not configuracion_prompt["indicadores"]:
            velas = formatear_velas_para_ia(velas)
        else:
            velas = formatear_indicadores_para_ia(velas)

        if cache:
            prompt_reevaluacion = importlib.import_module(f"IA.prompts.reevaluacion.{nombre_ia}.{configuracion_prompt['version_reevaluacion_cache']}_CACHE")
            obtener_datos_filtro = getattr(prompt_reevaluacion,"obtener_datos_filtro")
            datos = obtener_datos_filtro(velas)
            prompt = getattr(prompt_reevaluacion, configuracion_prompt["reevaluacion"])
        else:
            prompt_reevaluacion = importlib.import_module(f"IA.prompts.reevaluacion.{nombre_ia}.{configuracion_prompt['version_reevaluacion']}")
            obtener_datos_filtro = getattr(prompt_reevaluacion,"obtener_datos_filtro")
            datos, inputs_filtrados = obtener_datos_filtro(velas)
            prompt_plantilla = getattr(prompt_reevaluacion, configuracion_prompt["reevaluacion"])
            prompt = prompt_plantilla.format(**inputs_filtrados)

        esquema = getattr(prompt_reevaluacion, "Esquema")
        if nombre_ia == "Gemini":
            objeto_validado = gemini.ejecutar_prompt(modelo, prompt, cache, False, datos, velas, esquema)

        elif nombre_ia == "Groq":
            objeto_validado = groq.ejecutar_prompt(modelo, prompt, esquema, False)

        if objeto_validado is not None:
            reevaluacion       = objeto_validado.a
            explicacion_reeval = objeto_validado.p
            take_profit        = objeto_validado.tp
            stop_loss          = objeto_validado.sl
            trailing_stop      = objeto_validado.ts
            velas_espera       = objeto_validado.v

            parametros.datos_fuente_velas["Stop Loss"] = stop_loss
            parametros.datos_fuente_velas["Take Profit"] = take_profit
            parametros.datos_fuente_velas["Trailing Stop"] = trailing_stop

            return (reevaluacion, take_profit, stop_loss, trailing_stop, velas_espera, explicacion_reeval)
        else:
            return None
    else:
        parametros.error = "IA - No se recibieron datos de velas\n"

def formatear_velas_para_ia(datos):
    # Crear el encabezado para guiar la lectura del modelo
    lineas = ["Vela,Open,High,Low,Close"]
    
    # Obtener el total de velas en el arreglo
    total_velas = len(datos)
    
    for i in range(total_velas):
        # Calculamos el índice inverso para que la IA sepa el orden cronológico.
        # La vela más antigua será la Vela -59 y la que acaba de cerrar será la Vela 0.
        indice_ia = -(total_velas - 1 - i)
        
        open_p  = round(float(datos[i]['Open']), 2)
        high_p  = round(float(datos[i]['High']), 2)
        low_p   = round(float(datos[i]['Low']), 2)
        close_p = round(float(datos[i]['Close']), 2)
        
        lineas.append(f"{indice_ia},{open_p},{high_p},{low_p},{close_p}")

        
    # Unir todo en un solo string de texto plano separado por saltos de línea
    return "\n".join(lineas)

def formatear_indicadores_para_ia(df_con_indicadores):
    """
    Recibe un DataFrame de Pandas que ya tiene calculados los indicadores:
    ['Open', 'High', 'Low', 'Close', 'RSI_4', 'MACD_Hist', 'Bollinger_Sup', 'Bollinger_Mid', 'Bollinger_Inf', 'VP_actual']
    
    Limpia los NaN, recorta a las últimas 60 velas, genera el índice retrospectivo
    y devuelve la matriz en formato de texto plano estructurado por columnas.
    """
    # 1. Crear una copia local para evitar modificar el DataFrame original en tu backend
    df = df_con_indicadores.copy()
    
    # 2. Limpieza de seguridad: Eliminar filas iniciales que se quedaron sin datos por el warm-up (NaN)
    columnas_control = ['RSI_4', 'MACD_Hist', 'Bollinger_Sup', 'Bollinger_Mid', 'Bollinger_Inf', 'VP_actual']
    df.dropna(subset=columnas_control, inplace=True)
    
    # 3. Recorte Estricto: Nos quedamos únicamente con las últimas 60 velas del historial
    df_ia = df.tail(60).copy()
    total_filas = len(df_ia)
    
    # 4. Generar el índice retrospectivo exacto exigido por tus patrones (Ej: -59 a 0)
    df_ia['Vela'] = range(-total_filas + 1, 1)
    
    # 5. Redondeo Cuantitativo: 2 decimales para optimizar drásticamente la lectura de la IA
    columnas_precio = ['Open', 'High', 'Low', 'Close', 'Bollinger_Sup', 'Bollinger_Mid', 'Bollinger_Inf']
    df_ia[columnas_precio] = df_ia[columnas_precio].round(2)
    df_ia[['RSI_4', 'MACD_Hist', 'VP_actual']] = df_ia[['RSI_4', 'MACD_Hist', 'VP_actual']].round(2)
    
    # 6. Reordenar las columnas en una jerarquía estructural limpia para la inyección del prompt
    columnas_finales = ['Vela', 'Open', 'High', 'Low', 'Close', 'RSI_4', 'MACD_Hist', 'Bollinger_Sup', 'Bollinger_Mid', 'Bollinger_Inf', 'VP_actual']
    df_resultado = df_ia[columnas_finales].reset_index(drop=True)
    
    # 7. Transformación a Texto Plano Tabular (Sin comas, alineado de forma visual por espacios)
    matriz_string_final = df_resultado.to_string(index=False)
    
    return matriz_string_final

def obtener_prompts_estrategia_activa(configuracion: Dict[str, Any]) -> Dict[str, str]:
    # 1. Filtramos las estrategias que tienen la bandera 'activo' en True
    estrategias_activas = [
        (nombre, datos) for nombre, datos in configuracion.items() 
        if datos.get("activo") is True
    ]
    
    # 2. Control de seguridad: Si no hay ninguna activa
    if not estrategias_activas:
        raise ValueError("Error Crítico: No hay ninguna estrategia con 'activo': True en TIPO_PROMPT.")
        
    # 3. Control de seguridad: Si hay más de una activa por error
    if len(estrategias_activas) > 1:
        nombres_conflictivos = [e[0] for e in estrategias_activas]
        raise ValueError(f"Error Crítico: Conflicto. Múltiples estrategias activas: {nombres_conflictivos}. Solo debe haber una.")
    
    # 4. Extraemos los datos de la única estrategia activa
    nombre_estrategia, datos_estrategia = estrategias_activas[0]
    
    # 5. Devolvemos directamente el mapeo de sus prompts asociados
    return {
        "estrategia": nombre_estrategia,
        "apertura": datos_estrategia["apertura"],
        "reevaluacion": datos_estrategia["reevaluacion"],
        "indicadores": datos_estrategia["indicadores"],
        "version_apertura": datos_estrategia["version_apertura"],
        "version_apertura_cache": datos_estrategia["version_apertura_cache"],
        "version_reevaluacion": datos_estrategia["version_reevaluacion"],
        "version_reevaluacion_cache": datos_estrategia["version_reevaluacion_cache"]
    }

def obtener_modelo_ia_activo(configuracion: dict) -> Optional[tuple[str, str, bool]]:
    # 1. Buscar la IA que tenga "activo": True
    for nombre_ia, datos_ia in configuracion.items():
        if datos_ia.get("activo"):
            # 2. Buscar el modelo que tenga "activo": True dentro de esa IA
            for item_modelo in datos_ia.get("modelos", []):
                if item_modelo.get("activo"):
                    return  nombre_ia, \
                            item_modelo["modelo"], \
                            datos_ia.get("cache", False)
    return None
