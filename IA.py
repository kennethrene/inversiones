from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from extraccion.velas import extraer_velas_para_IA
import json
import configuracion.parametros as parametros
import configuracion.prompts as prompts
import configuracion.secrets as secrets
from typing import Literal, Optional, Dict, Any
from tvDatafeed import Interval

class PuntosControl(BaseModel):
    primer_pico: Optional[float] = Field(None, description="Precio del primer pico o suelo.")
    segundo_pico: Optional[float] = Field(None, description="Precio del segundo pico o suelo.")
    linea_cuello: Optional[float] = Field(None, description="Precio de la línea de cuello (neckline).")
    zona_soporte: Optional[float] = Field(None, description="Precio del soporte del rango lateral si aplica.")
    zona_resistencia: Optional[float] = Field(None, description="Precio de la resistencia del rango lateral si aplica.")

class AnalisisPatron(BaseModel):
    decision_accion: Literal["Comprar", "Vender", "Mantener"] = Field(
        ..., 
        description="La acción recomendada basada exclusivamente en el análisis de los datos."
    )
    reevaluacion: Literal["Mantener", "Cerrar", "Ajustar"] = Field(
        ..., 
        description=(
            "La acción operativa recomendada basada en los nuevos datos. "
            "'Mantener': La estructura sigue igual. "
            "'Cerrar': Cerrar posición inmediatamente en el mercado para mitigar riesgo o asegurar ganancia. "
            "'Ajustar': Modificar stop_loss, take_profit y trailing stop debido a la nueva acción del precio."
        )
    )
    nombre_del_patron: str = Field(
        ..., 
        description="Nombre técnico formal del patrón de velas o gráfico detectado (ej. 'Martillo', 'Envolvente Alcista', 'Hombro Cabeza Hombro', etc.). Si no hay un patrón claro, indicar 'Ninguno'."
    )
    explicacion_tecnica: str = Field(
        ..., 
        description="Breve justificación de por qué se identifica ese patrón analizando los precios."
    )
    explicacion_reevaluacion: str = Field(
        ..., 
        description="Justificación técnica detallada de la reevaluación. Debe explicar por qué la nueva acción del precio valida, invalida o altera la estructura inicial, especificando qué patrones, soportes, resistencias o anomalías visualizadas en las nuevas velas fundamentan la decisión."
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
    velas_espera_validacion: int = Field(
        ...,
        ge=1,  # Restringe que el valor sea mínimo 1 vela
        le=10, # Opcional: restringe un máximo lógico (ej. 50 velas) para evitar respuestas absurdas
        description=(
            "Número entero de velas adicionales que el sistema debe esperar antes de ejecutar la próxima validación. Este tiempo se calcula en función de la "
            "temporalidad actual y la distancia hacia el take_profit o stop_loss, estimando cuánto tardará el precio en confirmar si la decisión fue correcta."
        )
    )
    puntos_control_patron: Optional[PuntosControl] = Field(
        None,
        description=(
            "Obligatorio para patrones complejos (Doble Techo/Suelo, Hombro-Cabeza-Hombro). "
            "Debe mapear los precios exactos de las velas donde se forman los picos, "
            "suelos y la línea de cuello (neckline) para validar la simetría rigurosa del patrón."
        )
    )

client = genai.Client(api_key=secrets.GOOGLE_IA)

def ejecutar_operacion():
    velas = extraer_velas_para_IA(parametros.activo_actual, Interval.in_5_minute)
    datos_en_texto = formatear_velas_para_ia(velas)

    banco_de_datos_bot = {
        "datos": datos_en_texto
    }

    mapa_prompts = obtener_prompts_estrategia_activa(parametros.TIPO_PROMPT)
    inputs_filtrados = {k: banco_de_datos_bot[k] for k in mapa_prompts["inicial_inputs"] if k in banco_de_datos_bot}
    prompt_plantilla = getattr(prompts, mapa_prompts["inicial"])
    prompt = prompt_plantilla.format(**inputs_filtrados)

    if velas != None and len(velas) > 0 :
        response = client.models.generate_content(
            model=parametros.MODELO_IA,
            contents=prompt,
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
        velas_espera_validacion = resultado["velas_espera_validacion"]
        
        if "puntos_control_patron" in resultado:
            puntos_control = resultado["puntos_control_patron"]
        else:
            puntos_control = []

        return accion, patron, confianza, explicacion, take_profit, stop_loss, trailing_stop, valor_entrada, velas_espera_validacion, puntos_control
    else:
        parametros.error = "No hay datos para analizar"

def reevaluar_operacion():
    velas = extraer_velas_para_IA(parametros.activo_actual, Interval.in_5_minute)
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

        response = client.models.generate_content(
            model=parametros.MODELO_IA,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=AnalisisPatron,
            ),
        )

        resultado = json.loads(response.text)
        accion = resultado["reevaluacion"]
        patron = resultado["nombre_del_patron"]
        explicacion = resultado["explicacion_reevaluacion"]
        confianza = resultado["fiabilidad"]
        take_profit = resultado["take_profit"]
        stop_loss = resultado["stop_loss"]
        trailing_stop = resultado["trailing_stop_activation"]
        valor_entrada = resultado["precio_entrada"]
        velas_espera_validacion = resultado["velas_espera_validacion"]
        
        if "puntos_control_patron" in resultado:
            puntos_control = resultado["puntos_control_patron"]
        else:
            puntos_control = []

        return accion, patron, confianza, explicacion, take_profit, stop_loss, trailing_stop, valor_entrada, velas_espera_validacion, puntos_control
    else:
        parametros.error = "No hay datos para analizar"

def formatear_velas_para_ia(datos):
    # Crear el encabezado para guiar la lectura del modelo
    lineas = ["Vela,Open,High,Low,Close"]
    
    # Obtener el total de velas en el arreglo
    total_velas = len(datos)
    
    for i in range(total_velas):
        # Calculamos el índice inverso para que la IA sepa el orden cronológico.
        # La vela más antigua será la Vela -59 y la que acaba de cerrar será la Vela 0.
        indice_ia = -(total_velas - 1 - i)
        
        open_p  = datos[i]['Open']
        high_p  = datos[i]['High']
        low_p   = datos[i]['Low']
        close_p = datos[i]['Close']
        
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
