from google import genai
from groq import Groq
from google.genai import types
from pydantic import BaseModel, Field
from extraccion.velas import extraer_velas_para_IA
import json
import configuracion.parametros as parametros
import configuracion.prompts as prompts
import configuracion.secrets as secrets
from typing import Dict, Any, Tuple
from tvDatafeed import Interval
from IA.esquemas import AnalisisPatronGroq, AnalisisPatronGemini

client = genai.Client(api_key=secrets.GOOGLE_IA)
client_groq = Groq(api_key=secrets.GROQ_IA)

def ejecutar_operacion():
    num_velas = 1
    if len(parametros.lista_velas_acumuladas) == 0:
        num_velas = 61

    velas = extraer_velas_para_IA(parametros.activo_actual, Interval.in_5_minute, num_velas)
    datos_en_texto = formatear_velas_para_ia(velas)

    banco_de_datos_bot = {
        "datos": datos_en_texto
    }

    mapa_prompts = obtener_prompts_estrategia_activa(parametros.TIPO_PROMPT)
    inputs_filtrados = {k: banco_de_datos_bot[k] for k in mapa_prompts["inicial_inputs"] if k in banco_de_datos_bot}
    prompt_plantilla = getattr(prompts, mapa_prompts["inicial"])
    prompt = prompt_plantilla.format(**inputs_filtrados)

    if velas != None and len(velas) > 0:
        proveedor_activo, modelo = obtener_modelo_ia_activo(parametros.MODELO_IA)
        json_crudo_texto = ""

        if proveedor_activo == "Gemini":
            response = client.models.generate_content(
                model=modelo,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=AnalisisPatronGemini,
                    temperature=0.1
                ),
            )
            json_crudo_texto = response.text
            objeto_validado = AnalisisPatronGemini.model_validate_json(json_crudo_texto)

        elif proveedor_activo == "Groq":
            completion = client_groq.chat.completions.create(
                model=modelo,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "AnalisisPatronGroq",
                        "strict": True,
                        "schema": AnalisisPatronGroq.model_json_schema() # Pydantic genera el mapa de llaves automáticamente
                    }
                },
                temperature=0.1  # Determinismo máximo para evitar alucinaciones
            )
            json_crudo_texto = completion.choices[0].message.content

            # 1. Cargamos el texto crudo en un diccionario común de Python
            dict_sucio = json.loads(json_crudo_texto)
            
            # 2. Creamos una bolsa de datos unificada mezclando sub-estructuras si existen
            analisis_sub = dict_sucio.get("analisis_mercado", {})
            decision_sub = dict_sucio.get("decision_operativa", {})
            monitoreo_sub = dict_sucio.get("monitoreo_sistema", {})
            
            datos_mezclados = {**dict_sucio, **analisis_sub, **decision_sub, **monitoreo_sub}
            
            # 3. Construimos a mano el diccionario plano final garantizando las 7 llaves críticas
            dict_reparado = {
                "decision_accion": datos_mezclados.get("accion_sugerida") or datos_mezclados.get("decision_accion") or "Mantener",
                "reevaluacion": datos_mezclados.get("reevaluacion") or "Mantener",
                "nombre_del_patron": datos_mezclados.get("patron_detectado") or datos_mezclados.get("nombre_del_patron") or "Ninguno",
                "fiabilidad": datos_mezclados.get("fiabilidad_patron") or datos_mezclados.get("fiabilidad") or "Baja",
                "precio_entrada": float(datos_mezclados.get("precio_entrada") or 0.0),
                "stop_loss": float(datos_mezclados.get("stop_loss") or 0.0),
                "take_profit": float(datos_mezclados.get("take_profit") or 0.0),
                "trailing_stop_activation": float(datos_mezclados.get("trailing_stop_activation") or datos_mezclados.get("trailing_stop") or 0.0),
                "puntos_control_patron": datos_mezclados.get("puntos_control_patron")
            }
            
            # Corrección estricta para números enteros en velas de espera
            try:
                dict_reparado["velas_espera_validacion"] = int(datos_mezclados.get("velas_espera_validacion") or datos_mezclados.get("velas_espera") or 1)
            except:
                dict_reparado["velas_espera_validacion"] = 1
                
            # Extracción y duplicación de textos explicativos
            texto_explicativo = datos_mezclados.get("justificacion_riesgo") or datos_mezclados.get("explicacion_reevaluacion") or datos_mezclados.get("explicacion_tecnica") or "Estructura validada."
            dict_reparado["explicacion_tecnica"] = datos_mezclados.get("explicacion_tecnica") or texto_explicativo
            dict_reparado["explicacion_reevaluacion"] = datos_mezclados.get("explicacion_reevaluacion") or texto_explicativo

            objeto_validado = AnalisisPatronGroq.model_validate(dict_reparado)

        accion                  = objeto_validado.decision_accion
        patron                  = objeto_validado.nombre_del_patron
        explicacion             = objeto_validado.explicacion_tecnica
        confianza               = objeto_validado.fiabilidad
        take_profit             = objeto_validado.take_profit
        stop_loss               = objeto_validado.stop_loss
        trailing_stop           = objeto_validado.trailing_stop_activation
        valor_entrada           = objeto_validado.precio_entrada
        velas_espera            = objeto_validado.velas_espera_validacion
        
        if objeto_validado.puntos_control_patron is not None:
            puntos_control = objeto_validado.puntos_control_patron
        else:
            puntos_control = []

        return accion, patron, confianza, explicacion, take_profit, stop_loss, trailing_stop, valor_entrada, velas_espera, puntos_control
    else:
        parametros.error = "IA - No hay datos para analizar\n"

def reevaluar_operacion():
    num_velas = parametros.velas_espera
    if len(parametros.lista_velas_acumuladas) == 0:
        num_velas = 61

    velas = extraer_velas_para_IA(parametros.activo_actual, Interval.in_5_minute, num_velas)
    datos_en_texto = formatear_velas_para_ia(velas)

    if velas != None and len(velas) > 0 :
        # Ajustar valores para TradingView (cuyos valores son mas bajos que XTB)
        precio_apertura_ajustado = float(parametros.datos_mapeados['Precio Apertura'].replace(" ", "")) - float(parametros.diferencia_precio)
        take_profit_ajustado = float(parametros.TAKE_PROFIT) - float(parametros.diferencia_precio)
        stop_loss_ajustado = float(parametros.STOP_LOSS)  - float(parametros.diferencia_precio)
        trailing_stop_ajustado = float(parametros.TRAILING_STOP) - float(parametros.diferencia_precio)

        mapa_prompts = obtener_prompts_estrategia_activa(parametros.TIPO_PROMPT)
        banco_de_datos_bot = {
            "datos": datos_en_texto,
            "rsi1": parametros.historico_rsi[-1],
            "rsi2": parametros.historico_rsi[-2],
            "precio_apertura": precio_apertura_ajustado,
            "take_profit": take_profit_ajustado,
            "stop_loss": stop_loss_ajustado,
            "trailing_stop": trailing_stop_ajustado,
            "explicacion": parametros.explicacion_decision,
            "beneficio_neto": parametros.datos_mapeados["Beneficio Neto"],
            "patron": parametros.datos_mapeados["Patron"],
            "operacion": parametros.datos_mapeados['Operacion']
        }

        inputs_filtrados = {k: banco_de_datos_bot[k] for k in mapa_prompts["auditoria_inputs"] if k in banco_de_datos_bot}
        prompt_plantilla = getattr(prompts, mapa_prompts["auditoria"])
        prompt = prompt_plantilla.format(**inputs_filtrados)

        proveedor_activo, modelo = obtener_modelo_ia_activo(parametros.MODELO_IA)
        json_crudo_texto = ""

        if proveedor_activo == "Gemini":
            response = client.models.generate_content(
                model=modelo,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=AnalisisPatronGemini,
                    temperature=0.1
                ),
            )
            json_crudo_texto = response.text
            objeto_validado = AnalisisPatronGemini.model_validate_json(json_crudo_texto)

        elif proveedor_activo == "Groq":
            completion = client_groq.chat.completions.create(
                model=modelo,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "AnalisisPatronGroq",
                        "schema": AnalisisPatronGroq.model_json_schema() # Pydantic genera el mapa de llaves automáticamente
                    }
                },
                temperature=0.1  # Determinismo máximo para evitar alucinaciones
            )
            json_crudo_texto = completion.choices[0].message.content

            # 1. Cargamos el texto crudo en un diccionario común de Python
            dict_sucio = json.loads(json_crudo_texto)
            
            # 2. Creamos una bolsa de datos unificada mezclando sub-estructuras si existen
            analisis_sub = dict_sucio.get("analisis_mercado", {})
            decision_sub = dict_sucio.get("decision_operativa", {})
            monitoreo_sub = dict_sucio.get("monitoreo_sistema", {})
            
            datos_mezclados = {**dict_sucio, **analisis_sub, **decision_sub, **monitoreo_sub}
            
            # 3. Construimos a mano el diccionario plano final garantizando las 7 llaves críticas
            dict_reparado = {
                "decision_accion": datos_mezclados.get("accion_sugerida") or datos_mezclados.get("decision_accion") or "Mantener",
                "reevaluacion": datos_mezclados.get("reevaluacion") or "Mantener",
                "nombre_del_patron": datos_mezclados.get("patron_detectado") or datos_mezclados.get("nombre_del_patron") or "Ninguno",
                "fiabilidad": datos_mezclados.get("fiabilidad_patron") or datos_mezclados.get("fiabilidad") or "Baja",
                "precio_entrada": float(datos_mezclados.get("precio_entrada") or 0.0),
                "stop_loss": float(datos_mezclados.get("stop_loss") or 0.0),
                "take_profit": float(datos_mezclados.get("take_profit") or 0.0),
                "trailing_stop_activation": float(datos_mezclados.get("trailing_stop_activation") or datos_mezclados.get("trailing_stop") or 0.0),
                "puntos_control_patron": datos_mezclados.get("puntos_control_patron")
            }
            
            # Corrección estricta para números enteros en velas de espera
            try:
                dict_reparado["velas_espera_validacion"] = int(datos_mezclados.get("velas_espera_validacion") or datos_mezclados.get("velas_espera") or 1)
            except:
                dict_reparado["velas_espera_validacion"] = 1
                
            # Extracción y duplicación de textos explicativos
            texto_explicativo = datos_mezclados.get("justificacion_riesgo") or datos_mezclados.get("explicacion_reevaluacion") or datos_mezclados.get("explicacion_tecnica") or "Estructura validada."
            dict_reparado["explicacion_tecnica"] = datos_mezclados.get("explicacion_tecnica") or texto_explicativo
            dict_reparado["explicacion_reevaluacion"] = datos_mezclados.get("explicacion_reevaluacion") or texto_explicativo

            objeto_validado = AnalisisPatronGroq.model_validate(dict_reparado)

        reevaluacion            = objeto_validado.reevaluacion  # Agregado para que no se pierda este field crítico
        patron                  = objeto_validado.nombre_del_patron
        explicacion_reeval      = objeto_validado.explicacion_reevaluacion # Extraído para tus logs
        confianza               = objeto_validado.fiabilidad
        take_profit             = objeto_validado.take_profit
        stop_loss               = objeto_validado.stop_loss
        trailing_stop           = objeto_validado.trailing_stop_activation
        valor_entrada           = objeto_validado.precio_entrada
        velas_espera            = objeto_validado.velas_espera_validacion
        
        if objeto_validado.puntos_control_patron is not None:
            puntos_control = objeto_validado.puntos_control_patron
        else:
            puntos_control = []

        return reevaluacion, patron, confianza, explicacion_reeval, take_profit, stop_loss, trailing_stop, valor_entrada, velas_espera, puntos_control
    else:
        parametros.error = "IA - No hay datos para analizar\n"

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
        "inicial": datos_estrategia["inicial"],
        "inicial_inputs": datos_estrategia["inicial_inputs"],
        "auditoria": datos_estrategia["auditoria"],
        "auditoria_inputs": datos_estrategia["auditoria_inputs"]
    }

def obtener_modelo_ia_activo(configuracion: Dict[str, Any]) -> Tuple[str, str]:
    # 1. Filtramos las plataformas que tienen 'activo' en True
    plataformas_activas = [
        (proveedor, datos["modelo"]) 
        for proveedor, datos in configuracion.items() 
        if datos.get("activo") is True
    ]
    
    # 2. Control de seguridad: Si no hay ninguna activa
    if not plataformas_activas:
        raise ValueError("Error Crítico: No hay ningún proveedor de IA marcado como 'activo': True en MODELO_IA.")
        
    # 3. Control de seguridad: Si hay más de una activa por error
    if len(plataformas_activas) > 1:
        proveedores_en_conflicto = [p[0] for p in plataformas_activas]
        raise ValueError(f"Error Crítico: Conflicto. Múltiples proveedores activos: {proveedores_en_conflicto}. Solo debe haber uno.")
    
    # 4. Devolvemos una tupla con (Proveedor, Nombre_del_Modelo)
    return plataformas_activas[0]