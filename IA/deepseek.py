from IA.esquemas import AnalisisPatronGemini
from openai import OpenAI
import configuracion.secrets as secrets

cliente = OpenAI(
    api_key=secrets.DEEPSEEK_IA, 
    base_url="https://api.deepseek.com"
)

def ejecutar_prompt(modelo, prompt):
    completion = cliente.chat.completions.create(
        model=modelo,
        messages=[
            {
                "role": "system",
                "content": "Eres un núcleo de ejecución cuantitativa automatizado. Tu única tarea es analizar datos OHLC y responder exclusivamente con un objeto JSON válido según las especificaciones del usuario."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        stream=False,
        response_format={"type": "json_object"},
        reasoning_effort="high",
        temperature=0.1
    )

    return completion.choices[0].message.content.strip()