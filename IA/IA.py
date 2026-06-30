from extraccion.velas import extraer_velas_para_IA
import configuracion.parametros as parametros
import IA.configuracion as configuracion
from tvDatafeed import Interval
import importlib
import IA.gemini as gemini
import IA.groq as groq
import IA.utils as utils
from datetime import datetime
from IA.utils import guardar_tabla_valores

def ejecutar_operacion():
    num_velas = 61
    configuracion_prompt = utils.obtener_prompts_estrategia_activa(configuracion.TIPO_PROMPT)

    indicador = None
    if configuracion_prompt["indicadores"]:
        indicador = configuracion_prompt["indicador"]

    velas_M5 = extraer_velas_para_IA(parametros.activo_actual, Interval.in_5_minute, num_velas, indicador)
    velas_H1 = extraer_velas_para_IA(parametros.activo_actual, Interval.in_1_hour, num_velas, indicador)

    if parametros.MOSTRAR_TABLA_VALORES:        
        guardar_tabla_valores(velas_M5[-5:])

    if velas_M5 is not None and len(velas_M5) > 0:
        nombre_ia, modelo, cache = utils.obtener_modelo_ia_activo(configuracion.MODELO_IA)

        inputs = {
            "velas_M5": velas_M5,
            "velas_H1": velas_H1,
            "indicador": indicador
        }
        
        if cache:
            prompt_apertura = importlib.import_module(f"IA.prompts.apertura.{nombre_ia}.{configuracion_prompt['version_apertura_cache']}_CACHE")
            prompt = getattr(prompt_apertura, configuracion_prompt["apertura"])
        else:
            prompt_apertura = importlib.import_module(f"IA.prompts.apertura.{nombre_ia}.{configuracion_prompt['version_apertura']}")
            obtener_datos_filtro = getattr(prompt_apertura,"obtener_datos_filtro")            
            inputs_filtrados = obtener_datos_filtro(inputs)

            prompt_plantilla = getattr(prompt_apertura, configuracion_prompt["apertura"])
            prompt = prompt_plantilla.format(**inputs_filtrados)

        esquema = getattr(prompt_apertura, "Esquema")
        
        if nombre_ia == "Gemini":
            objeto_validado = gemini.ejecutar_prompt(modelo, prompt, cache, True, None, velas_M5, esquema)

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
        parametros.error += f"IA - No se recibieron datos de velas - {datetime.now().strftime('%H:%M')}\n"

def reevaluar_operacion():
    num_velas = parametros.velas_espera

    configuracion_prompt = utils.obtener_prompts_estrategia_activa(configuracion.TIPO_PROMPT)

    if not configuracion_prompt["indicadores"]:
        if len(parametros.lista_velas_acumuladas) == 0:
            num_velas = 61

        velas = extraer_velas_para_IA(parametros.activo_actual, Interval.in_5_minute, num_velas)
    else:
        if len(parametros.lista_velas_acumuladas) == 0:
            num_velas = 121
        
        #velas, _ = obtener_datos_indicadores(extraer_velas_para_indicadores(parametros.activo_actual, Interval.in_5_minute, num_velas))

    if velas is not None and len(velas) > 0:
        nombre_ia, modelo, cache = utils.obtener_modelo_ia_activo(configuracion.MODELO_IA)
        
        if not configuracion_prompt["indicadores"]:
            velas = utils.formatear_velas_para_ia(velas)
        else:
            velas = None

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
        parametros.error += f"IA - No se recibieron datos de velas - {datetime.now().strftime('%H:%M')}\n"
