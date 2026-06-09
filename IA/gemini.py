
import datetime
import json
from IA.esquemas import AnalisisPatronGemini
from google import genai
from google.genai import types
import configuracion.secrets as secrets
import configuracion.parametros as parametros

cliente = genai.Client(api_key=secrets.GOOGLE_IA)
cache_prompt_inicial = ""
cache_prompt_reevaluacion = ""
fecha_expiracion_cache_inicial = None
fecha_expiracion_cache_reevaluacion = None

def crear_cache_de_reglas_inicial(modelo: str, prompt_sistema_reglas: str):
    global cache_prompt_inicial, fecha_expiracion_cache_inicial

    ttl_formato_google = f"{parametros.HORAS_CACHE * 3600}s"

    cache_prompt_inicial = cliente.caches.create(
        model = modelo,
        config = types.CreateCachedContentConfig(            
            contents = [prompt_sistema_reglas],
            ttl = ttl_formato_google
        )
    )

    fecha_expiracion_cache_inicial = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=parametros.HORAS_CACHE)

def ejecutar_prompt_inicial(modelo: str, prompt: str, velas: str):
    global cache_prompt_inicial, fecha_expiracion_cache_inicial

    now = datetime.datetime.now(datetime.timezone.utc)
    if cache_prompt_inicial == "" or now >= fecha_expiracion_cache_inicial:
        crear_cache_de_reglas_inicial(modelo, prompt)

    velas_json = json.dumps(velas)

    response = cliente.models.generate_content(
        model=modelo,
        contents=f"DATOS DE PRECIOS SUMINISTRADOS (OHLC): {velas_json}", 
        config=types.GenerateContentConfig(
            cached_content=cache_prompt_inicial.name, 
            response_mime_type="application/json",
            response_schema=AnalisisPatronGemini,
            temperature=0.0
        ),
    )
    
    return AnalisisPatronGemini.model_validate_json(response.text)

def crear_cache_de_reglas_reevaluacion(modelo: str, prompt_sistema_reglas: str):
    global cache_prompt_reevaluacion, fecha_expiracion_cache_reevaluacion

    ttl_formato_google = f"{parametros.HORAS_CACHE * 3600}s"

    cache_prompt_reevaluacion = cliente.caches.create(
        model = modelo,
        config = types.CreateCachedContentConfig(            
            contents = [prompt_sistema_reglas],
            ttl = ttl_formato_google
        )
    )

    fecha_expiracion_cache_reevaluacion = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=parametros.HORAS_CACHE)

def ejecutar_prompt_reevaluacion(modelo: str, prompt: str, datos: str, velas: str):
    global cache_prompt_reevaluacion, fecha_expiracion_cache_reevaluacion

    now = datetime.datetime.now(datetime.timezone.utc)

    if cache_prompt_reevaluacion == "" or now >= fecha_expiracion_cache_reevaluacion:
        crear_cache_de_reglas_reevaluacion(modelo, prompt)

    payload_completo = datos.copy()
    payload_completo["datos"] = velas
    datos_json = json.dumps(payload_completo)

    response = cliente.models.generate_content(
        model=modelo,
        contents=f"EVALUAR OPERACIÓN ACTIVA CON LOS SIGUIENTES DATOS DINÁMICOS: {datos_json}",
        config=types.GenerateContentConfig(
            cached_content=cache_prompt_reevaluacion.name, 
            response_mime_type="application/json",
            response_schema=AnalisisPatronGemini,
            temperature=0.0
        ),
    )
    
    return AnalisisPatronGemini.model_validate_json(response.text)

def ejecutar_prompt(modelo, prompt, cache, inicial, datos, velas):
    if not cache:    
        response = cliente.models.generate_content(
                model=modelo,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=AnalisisPatronGemini,
                    temperature=0.1
                ),
            )
        json_crudo_texto = response.text

        return AnalisisPatronGemini.model_validate_json(json_crudo_texto)
    else:
        if inicial:
            return ejecutar_prompt_inicial(modelo, prompt, velas)
        else:
            return ejecutar_prompt_reevaluacion(modelo, prompt, datos, velas)