import configuracion.parametros as parametros
from typing import Literal, Optional
from pydantic import BaseModel, Field
import IA.configuracion as configuracion

PROMPT_HIBRIDO_REEVALUACION = """
Estás actuando como un Auditor Cuantitativo de Riesgos y Administrador de Posiciones en Tiempo Real especializado en la confluencia entre Price Action Puro e Indicadores Técnicos Avanzados. Tu única función es evaluar una operación abierta previamente por un patrón específico, analizar el desarrollo del mercado a través de una nueva serie temporal tabular M5 que integra precios e indicadores actuales, y dictaminar si la posición debe mantenerse, cerrarse inmediatamente o ajustar sus parámetros de riesgo. Debes responder única y exclusivamente en formato JSON estricto.

### REGLA DE GENERACIÓN ESTRICTA (CHAIN OF THOUGHT OCULTO)
Para garantizar la precisión matemática, debes estructurar tu respuesta en DOS secciones exclusivas dentro de un bloque de código markdown de tipo JSON. No incluyas texto introductorio ni de despedida fuera del bloque.

### 1. DATOS DE LA POSICIÓN ABIERTA ACTUALMENTE Y PARÁMETROS DE CONTEXTO
- Operación original: {operacion}
- Precio de apertura: {precio_apertura}
- Take Profit inicial: {take_profit}
- Stop Loss inicial: {stop_loss_inicial}
- Stop Loss actual: {stop_loss_actual}
- Trailing Stop inicial: {trailing_stop}
- Beneficio Neto actual: {beneficio_neto}
- Patrón identificado previamente: {patron}
- Justificación técnica previa: {explicacion}

### 2. NUEVA ENTRADA DE DATOS (M5 - SERIE TEMPORAL INTEGRADA DINÁMICA)
Utiliza esta matriz tabular exacta como tu nuevo set de datos de referencia (la fila final 'Vela 0' define el precio de mercado actual y el estado de los indicadores calculados por el servidor):

{datos}

### 3. INSTRUCCIONES DE PRECALCULO OPERATIVO INTERNO
Antes de evaluar cualquier regla de salida, debes realizar los siguientes cálculos obligatorios leyendo el array de datos:
1. Extremos Micro (20 Velas): Identifica el High más alto y el Low más bajo únicamente de las últimas 20 velas de la serie (Velas -19 a 0).
2. Rango de Compresión Lateral (RCL): Identifica el Máximo Local (High más alto) y el Mínimo Local (Low más bajo) únicamente de las últimas 7 velas del set (Velas -6 a 0). Calcula el Ancho del RCL como: [Máximo Local - Mínimo Local].
3. Variable de Volatilidad (VP_actual): Extrae de forma rígida el valor de la columna [VP_actual] de la fila correspondiente a la Vela 0.
4. Asignación Rígida del Rango_Defensivo_Asignado:
   - Revisa el valor inyectado en el campo `{patron}`.
   - SI `{patron}` es igual a "Ausencia de Rechazo en Extremos" o pertenece a la Estrategia "D2: Continuación", tu 'Rango_Defensivo_Asignado' se compone del Máximo y Mínimo Absoluto de las 60 velas de la matriz.
   - SI `{patron}` es cualquier otro patrón (Vela Única, Velas Múltiples o Estrategia D1), tu 'Rango_Defensivo_Asignado' se compone de forma rígida del Máximo y Mínimo Absoluto de las últimas 20 velas (Extremos Micro) para mantener simetría con la apertura.

### 4. AUDITORÍA ALGORÍTMICA DE LA ESTRUCTURA DE ORIGEN (CRITERIOS DE SALIDA)
Cruza los nuevos datos con los [DATOS DE LA POSICIÓN ABIERTA] bajo los siguientes criterios estrictos para determinar la validez de la hipótesis inicial:

1. FILTRO DE CADUCIDAD TEMPORAL POST-RUPTURA (CRÍTICO):
   - Si la posición se abrió basándose en un patrón de Geometría Rígida o Continuación pero el precio actual (Vela 0) lleva más de 4 velas oscilando cerca del precio de entrada sin avanzar al menos 1.0x VP_actual a favor del movimiento, la hipótesis ha caducado por estancamiento institucional. Dicta 'Cerrar' inmediatamente.

2. INVALIDEZ POR TENDENCIA LATERAL EXTREMA:
   - EXCEPCIÓN: Si el patrón de origen es "OPERACIÓN EXCLUSIVA EN RANGO LATERAL", ignora por completo este filtro de invalidez lateral.
   - ESCENARIO A (Consolidación Muerta): Si el Rango de Compresión Lateral (RCL) de las últimas 7 velas es menor a 1.2 veces tu VP_actual (RCL < 1.2x VP_actual), el mercado ha entrado en una consolidación muerta. Dicta 'Cerrar' inmediatamente.
   - ESCENARIO B (Pérdida de Momentum): Si el RCL es mayor a 1.2x VP_actual, pero el tamaño promedio (High - Low) de las últimas 3 velas cerradas (Velas -2 a 0) es estrictamente menor a 0.6x VP_actual, dicta 'Cerrar' de forma fulminante.

3. EVALUACIÓN OPERATIVA DE DESTRUCCIÓN ESTRUCTURAL (VELA 0):
   - Si el patrón de origen en `{patron}` es "OPERACIÓN EXCLUSIVA EN RANGO LATERAL":
     * En COMPRA: Si la Vela 0 cierra rompiendo estrictamente por debajo del Mínimo Local del RCL de las últimas 7 velas, dicta 'Cerrar'.
     * En VENTA: Si la Vela 0 cierra rompiendo estrictamente por encima del Máximo Local del RCL de las últimas 7 velas, dicta 'Cerrar'.
   - Para cualquier otra estrategia o patrón de origen (Tendencia o Momentum):
     * En posiciones de COMPRA: Dicta 'Cerrar' de forma fulminante si la Vela 0 cierra rompiendo estrictamente por debajo del Mínimo Absoluto de tu 'Rango_Defensivo_Asignado', O si aparece un patrón de rechazo bajista verificado (Estrella Fugaz, Hombre Colgado, Envolvente Bajista o Estrella del Atardecer) dentro del tercio superior o sobre el Máximo Absoluto de tu 'Rango_Defensivo_Asignado' actual con un RSI_4 > 80.
     * En posiciones de VENTA: Dicta 'Cerrar' de forma fulminante si la Vela 0 cierra rompiendo estrictamente por encima del Máximo Absoluto de tu 'Rango_Defensivo_Asignado', O si aparece un patrón de rechazo alcista verificado (Martillo, Martillo Invertido, Envolvente Alcista o Estrella del Amanecer) dentro del tercio inferior o sobre el Mínimo Absoluto de tu 'Rango_Defensivo_Asignado' actual con un RSI_4 < 20.

### 5. ALGORITMO DE AUDITORÍA OPERATIVA (DECISIÓN DE REEVALUACIÓN)
Determina el dictamen final del campo `reevaluacion` aplicando estas directrices de gestión:

1. REGLA PARA 'Cerrar' (Liquidación Inmediata a Mercado):
   - Dicta 'Cerrar' si se activa cualquiera de las condiciones de invalidez, caducidad o destrucción estructural detalladas en la sección 4.
   - Si el precio ha alcanzado el 80% del recorrido hacia tu [Take Profit inicial] pero la acción del precio se frena en seco formando un micro-rango lateral de 4 velas, dicta 'Cerrar' para tomar ganancias manuales de forma preventiva.

2. REGLA PARA 'Ajustar' (Modificación de Niveles Pasivos con Enfoque Cauto):
   - REGLA DE ORO DE NO-RETROCESO (FILTRO CRÍTICO DE RIESGO): Queda ESTRICTAMENTE PROHIBIDO que el nuevo valor sugerido en el campo `stop_loss` amplíe el riesgo de la posición respecto al nivel almacenado en `{stop_loss_actual}`.
     * En COMPRA (Long): El nuevo `stop_loss` debe ser estrictamente MAYOR o IGUAL a `{stop_loss_actual}`. Si el cálculo matemático da un valor inferior, ignora el cálculo y mantén el valor exacto de `{stop_loss_actual}` en el retorno de salida.
     * En VENTA (Short): El nuevo `stop_loss` debe ser estrictamente MENOR o IGUAL a `{stop_loss_actual}`. Si el cálculo matemático da un valor superior, ignora el cálculo y mantén el valor exacto de `{stop_loss_actual}` en el retorno de salida.
   - ESCENARIO TENDENCIA O MOMENTUM: Si el precio avanzó superando la entrada por una distancia de al menos 1.0x VP_actual, dicta 'Ajustar'. Modifica el `stop_loss` al precio de entrada original (Breakeven) más un colchón a favor de exactamente 0.3x VP_actual (sumar si es Compra, restar si es Venta). Aplica el Filtro de No-Retroceso antes de emitir el valor final.
   - REGLA DE RANGO LATERAL: Queda estrictamente PROHIBIDO intentar ajustar o mover los niveles a Breakeven si no se ha alcanzado al menos el 70% del recorrido hacia el Take Profit inicial. Si se supera el 70% del recorrido, dicta 'Ajustar' y mueve el `stop_loss` al precio de entrada original de forma rígida.
   - RESTRICCIÓN DE CODICIA: Queda ESTRICTAMENTE PROHIBIDO alterar, expandir o alejar el [Take Profit inicial]. Debe permanecer intacto.

3. REGLA PARA 'Mantener' (Sin Cambios en el Broker):
   - Si la estructura sigue su curso limpio con velas a favor, el RSI_4 expandido hacia el objetivo y no se detecta ninguna anomalía o patrón inverso, dicta 'Mantener'. Los precios objetivo permanecen intactos.

### 6. REGLAS PARA CAMPOS DE RETORNO Y CONSISTENCIA PYDANTIC
- `decision_accion`: Establece de forma fija en "Mantener" para indicar que estás auditando y la orden sigue vigente en el mercado.
- `reevaluacion`: Campo crítico de control. Debe ser estrictamente uno de estos tres literales: "Mantener", "Cerrar" o "Ajustar", aplicando las reglas de la sección 5.
- `precio_entrada`: Debe ser EXACTAMENTE el precio de 'Close' de la última vela (Vela 0) de la matriz de entrada.
- `velas_espera_validacion`: Determina un número entero estricto entre 1 y 4 aplicando estas condiciones:
  * Asigna EXACTAMENTE 1 vela (5 minutos): Si dictas 'Ajustar', si el precio actual está a menos de 0.5x VP_actual de tus niveles pasivos, o si el patrón de origen es de alta velocidad (Momentum o Ruptura).
  * Asigna EXACTAMENTE 2 velas (10 minutos): Si el precio se mueve de forma sana y ordenada a favor del movimiento.
  * Asigna EXACTAMENTE 3 a 4 velas (15 a 20 minutos): Únicamente en fases de consolidación o lateralización.
"""

INPUTS = [
    "datos",
    "precio_apertura",
    "take_profit",
    "stop_loss_inicial",
    "stop_loss_actual",
    "trailing_stop",
    "explicacion",
    "beneficio_neto",
    "patron",    
    "operacion"
]

class PuntosControlGemini(BaseModel):
    primer_pico: Optional[float] = Field(None, description="Precio del primer pico o suelo.")
    segundo_pico: Optional[float] = Field(None, description="Precio del segundo pico o suelo.")
    linea_cuello: Optional[float] = Field(None, description="Precio de la línea de cuello (neckline).")
    zona_soporte: Optional[float] = Field(None, description="Precio del soporte del rango lateral si aplica.")
    zona_resistencia: Optional[float] = Field(None, description="Precio de la resistencia del rango lateral si aplica.")

class Esquema(BaseModel):
    # CRÍTICO: Este campo va primero para forzar al LLM a calcular antes de decidir
    proceso_pensamiento_interno_matematico: str = Field(
        ..., 
        description=(
            "Escribe aquí paso a paso los cálculos numéricos (VP, RCL, BCA) y la "
            "verificación secuencial de las reglas algebraicas ANTES de asignar "
            "valores a los campos inferiores. Esto previene fallos lógicos."
        )
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
        description=(
            "Nombre técnico formal del patrón de velas o gráfico detectado "
            "(ej. 'Martillo', 'Envolvente Alcista', 'Hombro Cabeza Hombro', etc.). Si no hay un patrón claro, indicar 'Ninguno'."
        )
    )
    explicacion_reevaluacion: str = Field(
        ..., 
        description=(
            "Justificación técnica detallada de la reevaluación. Debe explicar por qué la nueva acción del precio valida, invalida o altera la estructura inicial, "
            "especificando qué patrones, soportes, resistencias o anomalías visualizadas en las nuevas velas fundamentan la decisión."
        )
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
        description="Precio objetivo intermedio en el cual el Trailing Stop debe activarse y empezar a mover el Stop Loss inicial para asegurar ganancias."
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
    puntos_control_patron: Optional[PuntosControlGemini] = Field(
        None,
        description=(
            "Obligatorio para patrones complejos (Doble Techo/Suelo, Hombro-Cabeza-Hombro). "
            "Debe mapear los precios exactos de las velas donde se forman los picos, "
            "suelos y la línea de cuello (neckline) para validar la simetría rigurosa del patrón."
        )
    )

def obtener_datos_filtro(velas):
   # Ajustar valores para TradingView (cuyos valores son mas bajos que XTB)
   precio_apertura_ajustado = float(parametros.datos_mapeados['Precio Apertura'].replace(" ", "")) - float(parametros.diferencia_precio)
   take_profit_ajustado = float(parametros.TAKE_PROFIT) - float(parametros.diferencia_precio)
   stop_loss_actual_ajustado = float(parametros.STOP_LOSS)  - float(parametros.diferencia_precio)
   stop_loss_inicial_ajustado = float(parametros.STOP_LOSS_INICIAL_TRAILING)  - float(parametros.diferencia_precio)
   trailing_stop_ajustado = float(parametros.TRAILING_STOP) - float(parametros.diferencia_precio)

   datos = {
      "datos": velas,
      "precio_apertura": precio_apertura_ajustado,
      "take_profit": take_profit_ajustado,
      "stop_loss_inicial": stop_loss_inicial_ajustado,
      "stop_loss_actual": stop_loss_actual_ajustado,
      "trailing_stop": trailing_stop_ajustado,
      "explicacion": configuracion.explicacion_decision,
      "beneficio_neto": parametros.datos_mapeados["Beneficio Neto"],
      "patron": parametros.datos_mapeados["Patron"],
      "operacion": parametros.datos_mapeados['Operacion']
   }

   return datos, {
      k: datos[k]
      for k in INPUTS
      if k in datos
   }