from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from extraccion.velas import extraer_velas_para_IA
import json
import configuracion.parametros as parametros
from typing import Literal, Optional
import configuracion.secrets as secrets
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
    datos_en_texto = json.dumps(velas)

    if velas != None and len(velas) > 0 :
        response = client.models.generate_content(
            model=parametros.MODELO_IA,
            contents=f"""
            Estás actuando como un sistema automatizado de gestión de riesgos y monitoreo de operaciones en tiempo real de alta precisión cuantitativa.
    
            Analiza rigurosamente la siguiente serie temporal de precios OHLC ordenada cronológicamente:
            {datos_en_texto}

            Reglas estrictas para estructurar la respuesta:
            REGLAS ALGORÍTMICAS DE VALIDACIÓN POR TIPO DE PATRÓN:
            1. GEOMETRÍA RÍGIDA (Doble Techo/Suelo, HCH): Exige simetría matemática rigurosa en los Highs y Lows de los picos y valles. Registra los valores exactos en `puntos_control_patron`. Si no hay simetría real o el precio rompe la línea de cuello de forma inversa, desestima el patrón y actúa para mitigar riesgo.
            2. CONTINUACIÓN (Banderas, Cuñas): Exige una disminución progresiva del volumen durante la formación del canal. La ruptura solo es válida si el precio de CIERRE de la vela queda fuera de la estructura acompañado de un aumento de volumen. Si lateraliza más de 15 velas sin romper, invalida el patrón.
            3. RECHAZO Y ESTRELLAS (Martillos, Martillos Invertidos, Estrellas Fugaces, Estrellas del Atardecer/Amanecer, Envolventes): 
                Ignora estos patrones por completo si ocurren en rangos medios o zonas muertas. Solo son válidos si la mecha de rechazo (superior en estrellas fugaces/martillos invertidos; inferior en martillos) es al menos el doble del tamaño del cuerpo real de la vela y ocurre directamente sobre un nivel macro de Soporte, Resistencia o Fibonacci. Para patrones de tres velas (como la Estrella del Atardecer), exige rigurosamente que la tercera vela cierre cubriendo al menos el 50% de la primera vela para confirmar la reversión.
            4. FILTRO DE FALSOS ROMPIMIENTOS (Fakeouts): Si una vela perfora un soporte/resistencia pero regresa y CIERRA dentro del rango dejando una mecha larga, clasifícalo como Fakeout. En este escenario, prioriza la acción de 'Cerrar' o ajustar el Stop Loss inmediatamente al extremo opuesto.
            5. FILTRO DE TENDENCIA LATERAL (Rangos y Consolidación): Analiza si los máximos y mínimos de las últimas velas se mantienen dentro de un canal horizontal estrecho con compresión de volatilidad y volumen plano o descendente. Si el precio está en una tendencia lateral sin una ruptura confirmada, prohíbe abrir operaciones basadas en patrones de tendencia. En este escenario, la recomendación operativa debe ser 'Mantener', a menos que se identifique una estrategia clara de rebote en los extremos exactos del rango (Soporte/Resistencia del canal).

            REGLAS ESTRICTAS DE EVALUACIÓN:
            1. Identifica el 'precio_entrada' óptimo basándote en la última estructura de precios analizada para maximizar la probabilidad de acierto.
            2. Si la acción recomendada es 'Comprar', calcula el 'take_profit' y el 'trailing_stop_activation' por encima de este precio de entrada, y el 'stop_loss' por debajo.
            3. Si la acción recomendada es 'Vender', realiza los cálculos inversos de manera matemática y precisa.
            4. Identifica el nombre técnico formal del patrón de velas o chartista presente en los datos y determina la decisión operativa final.
            5. Ajusta los niveles de 'take_profit', 'stop_loss' y 'trailing_stop_activation' proporcionalmente según el nivel de fiabilidad detectado, optimizando siempre la relación Riesgo/Beneficio para minimizar las pérdidas potenciales y maximizar el recorrido de las ganancias.
            6. Calcula en el campo velas_espera_validacion la cantidad óptima de velas que el sistema debe esperar para volver a ejecutar este script para revalidar la decisión tomada. Básate en la volatilidad actual y en la distancia de los precios objetivo; por ejemplo, si el precio está muy cerca del Stop Loss o Take Profit, el número de velas debe ser bajo.
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
        velas_espera_validacion = resultado["velas_espera_validacion"]

        return accion, patron, confianza, explicacion, take_profit, stop_loss, trailing_stop, valor_entrada, velas_espera_validacion
    else:
        parametros.error = "No hay datos para analizar"

def reevaluar_operacion():
    velas = extraer_velas_para_IA(parametros.activo_actual, Interval.in_5_minute)
    datos_en_texto = json.dumps(velas)

    if velas != None and len(velas) > 0 :
        # Ajustar valores para TradingView (cuyos valores son mas bajos que XTB)
        precio_apertura_ajustado = float(parametros.datos_mapeados['Precio Apertura'].replace(" ", "")) - float(parametros.diferencia_precio)
        take_profit_ajustado = float(parametros.TAKE_PROFIT) - float(parametros.diferencia_precio)
        stop_loss_ajustado = float(parametros.STOP_LOSS)  - float(parametros.diferencia_precio)
        trailing_stop_ajustado = float(parametros.TRAILING_STOP) - float(parametros.diferencia_precio)

        response = client.models.generate_content(
            model=parametros.MODELO_IA,
            contents=f"""
            Estás actuando como un sistema automatizado de gestión de riesgos y monitoreo de operaciones en tiempo real.
            
            Tu objetivo es evaluar si una posición de trading abierta previamente sigue siendo válida o si las nuevas velas de precio ({datos_en_texto}) exigen proteger el capital de forma inmediata.

            DATOS DE LA POSICIÓN ABIERTA ACTUALMENTE:
            - Dirección original: {parametros.datos_mapeados['Operacion']}
            - Precio de entrada: {precio_apertura_ajustado}
            - Take Profit actual: {take_profit_ajustado}
            - Stop Loss actual: {stop_loss_ajustado}
            - Trailing Stop actual: {trailing_stop_ajustado}
            - Estado de rendimiento actual: {parametros.datos_mapeados['Beneficio Neto']}
            - Patrón identificado: {parametros.datos_mapeados["Patron"]}

            REGLAS ALGORÍTMICAS DE VALIDACIÓN POR TIPO DE PATRÓN:
            1. GEOMETRÍA RÍGIDA (Doble Techo/Suelo, HCH, HCH Invertido): Exige simetría matemática rigurosa en los Highs y Lows de los picos y valles. Registra los valores exactos en `puntos_control_patron`. Si no hay simetría real o el precio rompe la línea de cuello de forma inversa, desestima el patrón y actúa para mitigar riesgo.
            2. CONTINUACIÓN (Banderas, Cuñas): Exige una disminución progresiva del volumen durante la formación del canal. La ruptura solo es válida si el precio de CIERRE de la vela queda fuera de la estructura acompañado de un aumento de volumen. Si lateraliza más de 15 velas sin romper, invalida el patrón.
            3. RECHAZO Y ESTRELLAS (Martillos, Martillos Invertidos, Estrellas Fugaces, Estrellas del Atardecer/Amanecer, Envolventes): 
                Ignora estos patrones por completo si ocurren en rangos medios o zonas muertas. Solo son válidos si la mecha de rechazo (superior en estrellas fugaces/martillos invertidos; inferior en martillos) es al menos el doble del tamaño del cuerpo real de la vela y ocurre directamente sobre un nivel macro de Soporte, Resistencia o Fibonacci. Para patrones de tres velas (como la Estrella del Atardecer), exige rigurosamente que la tercera vela cierre cubriendo al menos el 50% de la primera vela para confirmar la reversión.
            4. FILTRO DE FALSOS ROMPIMIENTOS (Fakeouts): Si una vela perfora un soporte/resistencia pero regresa y CIERRA dentro del rango dejando una mecha larga, clasifícalo como Fakeout. En este escenario, prioriza la acción de 'Cerrar' o ajustar el Stop Loss inmediatamente al extremo opuesto.
            5. FILTRO DE TENDENCIA LATERAL (Rangos y Consolidación): Analiza si los máximos y mínimos de las últimas velas se mantienen dentro de un canal horizontal estrecho con compresión de volatilidad y volumen plano o descendente. Si el precio está en una tendencia lateral sin una ruptura confirmada, prohíbe abrir operaciones basadas en patrones de tendencia. En este escenario, la recomendación operativa debe ser 'Mantener', a menos que se identifique una estrategia clara de rebote en los extremos exactos del rango (Soporte/Resistencia del canal).

            REGLAS ESTRICTAS DE EVALUACIÓN:
            1. Analiza si las nuevas velas muestran una invalidación del patrón original, un cambio de tendencia repentino, pérdida de volumen o divergencias peligrosas.
            2. Determina la 'reevaluacion' bajo los siguientes criterios:
            - 'Mantener': Si el precio se mueve a favor o la estructura sigue siendo técnicamente sólida. Los niveles actuales se quedan igual.
            - 'Cerrar': Si hay señales claras de reversión en contra, velas de rechazo fuerte en zonas clave, o si la ganancia actual corre un riesgo alto de borrarse.
            - 'Ajustar': Si el precio ha avanzado a favor y permite asegurar ganancias subiendo el Stop Loss (Break-even / Profit-lock) o ajustando el Take Profit debido a una nueva resistencia/soporte.
            3. Si la decisión es 'AJUSTAR_NIVELES', calcula matemáticamente los nuevos parámetros de salida basándote estrictamente en la nueva acción del precio. Si la decisión es otra, devuelve estos campos como null.
            4. Sé extremadamente conservador: ante la menor duda de reversión de tendencia con pérdidas potenciales, prioriza 'Cerrar' o asegurar ganancias.
            7. Calcula en el campo velas_espera_validacion la cantidad óptima de velas que el sistema debe esperar para volver a ejecutar este script para revalidar la decisión tomada. Básate en la volatilidad actual y en la distancia de los precios objetivo; por ejemplo, si el precio está muy cerca del Stop Loss o Take Profit, el número de velas debe ser bajo.
            """,
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

        return accion, patron, confianza, explicacion, take_profit, stop_loss, trailing_stop, valor_entrada, velas_espera_validacion
    else:
        parametros.error = "No hay datos para analizar"

