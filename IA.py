from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from extraccion.velas import extraer_velas_para_IA
import json
import configuracion.parametros as parametros
from typing import Literal
import configuracion.secrets as secrets
from tvDatafeed import Interval

class AnalisisPatron(BaseModel):
    decision_accion: Literal["Comprar", "Vender", "Mantener"] = Field(
        ..., 
        description="La acción recomendada basada exclusivamente en el análisis de los datos."
    )
    nombre_del_patron: str = Field(
        ..., 
        description="Nombre técnico formal del patrón de velas o gráfico detectado (ej. 'Martillo', 'Envolvente Alcista', 'Hombro Cabeza Hombro', etc.). Si no hay un patrón claro, indicar 'Ninguno'."
    )
    explicacion_tecnica: str = Field(
        ..., 
        description="Breve justificación de por qué se identifica ese patrón analizando los precios."
    )
    fiabilidad: Literal["Alta", "Media", "Baja"] = Field(
        ..., 
        description="Nivel de confianza o fuerza que tiene la señal detectada."
    )
    take_profit: float = Field(
        ..., 
        description="Precio objetivo sugerido para cerrar la operación con ganancias, calculado técnicamente según las resistencias o la proyección del patrón."
    )
    stop_loss: float = Field(
        ..., 
        description="Precio límite sugerido para cortar pérdidas, colocado estratégicamente (por ejemplo, abajo del mínimo de la estructura analizada)."
    )
    trailing_stop_activation: float = Field(
        ...,
        description="Precio objetivo intermedio en el cual el Trailing Stop debe activarse y empezar a mover el Stop Loss original para asegurar ganancias."
    )
    precio_entrada: float = Field(
        ...,
        description="El precio de mercado actual tomado como punto de partida para la operación (corresponde exactamente al último valor de 'Close')."
    )

client = genai.Client(api_key=secrets.GOOGLE_IA)

def ejecutar_operacion():
    velas = extraer_velas_para_IA(parametros.activo_actual, Interval.in_5_minute)
    datos_en_texto = json.dumps(velas)

    if velas != None and len(velas)> 0 :
        response = client.models.generate_content(
            model='gemini-3.5-flash',
            contents=f"""
            Analiza rigurosamente la siguiente serie temporal de precios OHLC ordenada cronológicamente:
            {datos_en_texto}

            Reglas estrictas para estructurar la respuesta:
            1. Identifica el 'precio_entrada' óptimo basándote en la última estructura de precios analizada para maximizar la probabilidad de acierto.
            2. Si la acción recomendada es 'Comprar', calcula el 'take_profit' y el 'trailing_stop_activation' por encima de este precio de entrada, y el 'stop_loss' por debajo.
            3. Si la acción recomendada es 'Vender', realiza los cálculos inversos de manera matemática y precisa.
            4. Identifica el nombre técnico formal del patrón de velas o chartista presente en los datos y determina la decisión operativa final.
            5. Ajusta los niveles de 'take_profit', 'stop_loss' y 'trailing_stop_activation' proporcionalmente según el nivel de fiabilidad detectado, optimizando siempre la relación Riesgo/Beneficio para minimizar las pérdidas potenciales y maximizar el recorrido de las ganancias.
            """,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=AnalisisPatron,
            ),
        )

        resultado = json.loads(response.text)
        accion = resultado["decision_accion"]
        patron = resultado["nombre_del_patron"]
        explicacion = resultado["explicacion_tecnica"]
        confianza = resultado["fiabilidad"]
        take_profit = resultado["take_profit"]
        stop_loss = resultado["stop_loss"]
        trailing_stop = resultado["trailing_stop_activation"]
        valor_entrada = resultado["precio_entrada"]

        return accion, patron, confianza, explicacion, take_profit, stop_loss, trailing_stop, valor_entrada
    else:
        parametros.error = "No hay datos para analizar"
