from extraccion.velas import extraer_velas_para_IA
import configuracion.parametros as parametros
import IA.configuracion as configuracion
from typing import Dict, Any, Optional
from tvDatafeed import Interval
import importlib
import IA.gemini as gemini
import IA.groq as groq

def ejecutar_operacion():
    num_velas = 1

    if len(parametros.lista_velas_acumuladas) == 0:
        num_velas = 61

    velas = extraer_velas_para_IA(parametros.activo_actual, Interval.in_5_minute, num_velas)

    if velas is not None and len(velas) > 0:
        velas = formatear_velas_para_ia(velas)

        nombre_ia, modelo, cache, version, _, version_cache, _ = obtener_modelo_ia_activo(configuracion.MODELO_IA)
        configuracion_prompt = obtener_prompts_estrategia_activa(configuracion.TIPO_PROMPT)

        if cache:
            prompt_apertura = importlib.import_module(f"IA.prompts.apertura.{nombre_ia}.{version_cache}_CACHE")
            prompt = getattr(prompt_apertura, configuracion_prompt["apertura"])
        else:
            prompt_apertura = importlib.import_module(f"IA.prompts.apertura.{nombre_ia}.{version}")
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
            accion          = objeto_validado.decision_accion
            patron          = objeto_validado.nombre_del_patron
            explicacion     = objeto_validado.explicacion_tecnica
            confianza       = objeto_validado.fiabilidad
            take_profit     = objeto_validado.take_profit
            stop_loss       = objeto_validado.stop_loss
            trailing_stop   = objeto_validado.trailing_stop_activation
            valor_entrada   = objeto_validado.precio_entrada
            velas_espera    = objeto_validado.velas_espera_validacion
            
            if objeto_validado.puntos_control_patron is not None:
                puntos_control = objeto_validado.puntos_control_patron
            else:
                puntos_control = []

            return (accion, patron, confianza, explicacion, take_profit, stop_loss, trailing_stop, valor_entrada, velas_espera, puntos_control)
        else:
            return None
    else:
        parametros.error = "IA - No se recibieron datos de velas\n"

def reevaluar_operacion():
    num_velas = parametros.velas_espera
    if len(parametros.lista_velas_acumuladas) == 0:
        num_velas = 61

    velas = extraer_velas_para_IA(parametros.activo_actual, Interval.in_5_minute, num_velas)

    if velas is not None and len(velas) > 0:
        velas = formatear_velas_para_ia(velas)

        nombre_ia, modelo, cache, _, version, _, version_cache = obtener_modelo_ia_activo(configuracion.MODELO_IA)
        configuracion_prompt = obtener_prompts_estrategia_activa(configuracion.TIPO_PROMPT)        

        if cache:
            prompt_reevaluacion = importlib.import_module(f"IA.prompts.reevaluacion.{nombre_ia}.{version_cache}_CACHE")
            obtener_datos_filtro = getattr(prompt_reevaluacion,"obtener_datos_filtro")
            datos = obtener_datos_filtro(velas)
            prompt = getattr(prompt_reevaluacion, configuracion_prompt["reevaluacion"])
        else:
            prompt_reevaluacion = importlib.import_module(f"IA.prompts.reevaluacion.{nombre_ia}.{version}")
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
            reevaluacion       = objeto_validado.reevaluacion 
            patron             = objeto_validado.nombre_del_patron
            explicacion_reeval = objeto_validado.explicacion_reevaluacion
            confianza          = objeto_validado.fiabilidad
            take_profit        = objeto_validado.take_profit
            stop_loss          = objeto_validado.stop_loss
            trailing_stop      = objeto_validado.trailing_stop_activation
            valor_entrada      = objeto_validado.precio_entrada
            velas_espera       = objeto_validado.velas_espera_validacion
            
            if objeto_validado.puntos_control_patron is not None:
                puntos_control = objeto_validado.puntos_control_patron
            else:
                puntos_control = []

            return (reevaluacion, patron, confianza, explicacion_reeval, take_profit, stop_loss, trailing_stop, valor_entrada, velas_espera, puntos_control)
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
                            datos_ia.get("cache", False), \
                            datos_ia.get("version_apertura"), \
                            datos_ia.get("version_reevaluacion"), \
                            datos_ia.get("version_apertura_cache"), \
                            datos_ia.get("version_reevaluacion_cache")
    return None
