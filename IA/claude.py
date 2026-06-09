import configuracion.secrets as secrets
from IA.esquemas import AnalisisPatronGemini
import anthropic
import json

cliente = anthropic.Anthropic(api_key=secrets.CLAUDE_IA)

def ejecutar_prompt_inicial(modelo: str, prompt: str, velas: dict, cache: bool) -> AnalisisPatronGemini:
    payload_dinamico_json = json.dumps(velas)
    
    if cache:
        sistema = [
            {
                "type": "text",
                "text": prompt,
                "cache_control": {"type": "ephemeral"}
            }
        ]
    else:
        sistema = prompt

    respuesta = cliente.messages.create(
        model = modelo,
        max_tokens = 1000,
        temperature = 0.0,
        
        system = sistema,
        
        messages = [
            {
                "role": "user",
                "content": f"EVALUAR OPERACIÓN ACTIVA CON LOS SIGUIENTES DATOS DINÁMICOS: {payload_dinamico_json}"
            }
        ]
    )
    
    json_respuesta_texto = respuesta.content[0].text

    return AnalisisPatronGemini.model_validate_json(json_respuesta_texto)