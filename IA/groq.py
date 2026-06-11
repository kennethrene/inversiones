from groq import Groq
import json
import configuracion.secrets as secrets

cliente = Groq(api_key=secrets.GROQ_IA)

def ejecutar_prompt(modelo, prompt, esquema, inicial):
    formato_resp = {
        "type": "json_object"
    }

    prompt_ajustado = (
        f"{prompt}\n\n"
        f"DEBES RESPONDER ESTRICTAMENTE CON UN OBJETO JSON que cumpla con este formato:\n"
        f"{esquema.model_json_schema()}"
    )

    mensajes = [
        {"role": "system", "content": "You are a precise automated financial trading machine. You output raw valid JSON only."},
        {"role": "user", "content": prompt_ajustado}
    ]
    
    respuesta = cliente.chat.completions.create(
        model = modelo,
        messages = mensajes,
        response_format = formato_resp,
        temperature = 0.1
    )

    json_crudo_texto = respuesta.choices[0].message.content
    dict_sucio = json.loads(json_crudo_texto)
    
    analisis_sub = dict_sucio.get("analisis_mercado", {})
    decision_sub = dict_sucio.get("decision_operativa", {})
    monitoreo_sub = dict_sucio.get("monitoreo_sistema", {})
    
    datos_mezclados = {**dict_sucio, **analisis_sub, **decision_sub, **monitoreo_sub}
    
    puntos_ia = datos_mezclados.get("puntos_control_patron") or {}

    if not isinstance(puntos_ia, dict):
        puntos_ia = {}

    puntos_reparados = {
        "primer_pico": puntos_ia.get("primer_pico") or 0.0,
        "segundo_pico": puntos_ia.get("segundo_pico") or 0.0,
        "linea_cuello": puntos_ia.get("linea_cuello") or 0.0,
        "zona_soporte": puntos_ia.get("zona_soporte") or 0.0,
        "zona_resistencia": puntos_ia.get("zona_resistencia") or 0.0
    }

    dict_reparado = {
        "nombre_del_patron": datos_mezclados.get("patron_detectado") or datos_mezclados.get("nombre_del_patron") or "Ninguno",
        "fiabilidad": datos_mezclados.get("fiabilidad_patron") or datos_mezclados.get("fiabilidad") or "Baja",
        "precio_entrada": float(datos_mezclados.get("precio_entrada") or 0.0),
        "stop_loss": float(datos_mezclados.get("stop_loss") or 0.0),
        "take_profit": float(datos_mezclados.get("take_profit") or 0.0),
        "trailing_stop_activation": float(datos_mezclados.get("trailing_stop_activation") or datos_mezclados.get("trailing_stop") or 0.0),
        "puntos_control_patron": puntos_reparados
    }

    try:
        dict_reparado["velas_espera_validacion"] = int(datos_mezclados.get("velas_espera_validacion") or datos_mezclados.get("velas_espera") or 1)
    except:
        dict_reparado["velas_espera_validacion"] = 1

    texto_extraido_error = ""
    texto_explicativo = (
        datos_mezclados.get("justificacion_riesgo") or 
        datos_mezclados.get("explicacion_tecnica") or 
        texto_extraido_error or # Si se guardó el error de la IA, lo usamos como texto explicativo
        "Estructura validada automáticamente por el sistema de exclusión lateral."
    )

    if inicial:
        dict_reparado["decision_accion"] = datos_mezclados.get("accion_sugerida") or datos_mezclados.get("decision_accion") or "Mantener"
        dict_reparado["explicacion_tecnica"] = datos_mezclados.get("explicacion_tecnica") or texto_explicativo
    else:
        reevaluacion_ia = datos_mezclados.get("reevaluacion") or "Mantener"

        if reevaluacion_ia not in ["Mantener", "Cerrar", "Ajustar"]:
            texto_extraido_error = str(reevaluacion_ia) # Guardamos el texto largo para rescatarlo luego
            reevaluacion_ia = "Mantener" # Forzamos el valor Literal válido exigido por Pydantic

        dict_reparado["reevaluacion"] = reevaluacion_ia
        dict_reparado["explicacion_reevaluacion"] = datos_mezclados.get("explicacion_reevaluacion") or texto_explicativo

    return esquema.model_validate(dict_reparado)