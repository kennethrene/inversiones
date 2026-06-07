
from IA.esquemas import AnalisisPatronGemini
from google import genai
from google.genai import types
import configuracion.secrets as secrets

cliente = genai.Client(api_key=secrets.GOOGLE_IA)

def ejecutar_prompt(modelo, prompt):
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