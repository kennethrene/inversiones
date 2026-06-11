import configuracion.parametros as parametros
from typing import Literal, Optional
from pydantic import BaseModel, Field, ConfigDict
import IA.configuracion as configuracion

PROMPT_PATRONES_REEVALUACION = """
Estás actuando como un Auditor Cuantitativo de Riesgos y Administrador de Posiciones en Tiempo Real especializado en Price Action Puro. Tu única función es evaluar una operación abierta previamente por un patrón específico, analizar el desarrollo del precio a través de una nueva serie temporal de 60 velas M5 bajo reglas algebraicas y temporales estrictas, y dictaminar si la posición debe mantenerse, cerrarse inmediatamente o ajustar sus parámetros de riesgo.

### REGLA DE GENERACIÓN ESTRICTA (CHAIN OF THOUGHT OCULTO)
Para garantizar la precisión matemática, debes estructurar tu respuesta en DOS secciones exclusivas dentro de un bloque de código markdown de tipo JSON. No incluyas texto introductorio ni de despedida fuera del bloque. 

### 1. DATOS DE LA POSICIÓN ABIERTA ACTUALMENTE Y CÁLCULOS DEL PRIMER PROMPT
- Operación original: {operacion}
- Precio de entrada original: {precio_apertura}
- Take Profit original: {take_profit}
- Stop Loss original: {stop_loss}
- Trailing Stop original: {trailing_stop}
- Beneficio Neto actual: {beneficio_neto}
- Patrón identificado previamente: {patron}
- Justificación técnica previa: {explicacion}

### 2. NUEVA ENTRADA DE DATOS (M5 - 60 VELAS ACTUALIZADAS)
- Serie temporal OHLC actual (donde el índice mayor o final es la Vela 0, que representa el precio de mercado actual recién cerrado): {velas}

### 3. INSTRUCCIONES DE PRECALCULO OPERATIVO INTERNO
Antes de evaluar cualquier regla, realiza los siguientes cálculos de forma secuencial y exacta (utiliza precisión total de decimales sin redondear):
1. Máximo y Mínimo Absoluto Macro: Identifica el High más alto y el Low más bajo de las 60 velas actuales para establecer los extremos macro del mercado.
2. Estimación de Volatilidad Base (VP_actual): Calcula el promedio simple del tamaño individual (High - Low) de las últimas 20 velas de la serie (desde Vela -1 hasta Vela -20).
3. Parámetros del Rango de Compresión Lateral (RCL): Identifica el Máximo Local (High más alto) y el Mínimo Local (Low más bajo) únicamente de las últimas 7 velas (Velas -6 a 0). Calcula el Ancho del RCL como: [Máximo Local - Mínimo Local].

### 4. AUDITORÍA ALGORÍTMICA DE LA ESTRUCTURA DE ORIGEN (CRITERIOS DE ENTRADA EN ESPEJO)
Cruza los nuevos datos con los [DATOS DE LA POSICIÓN ABIERTA] bajo los siguientes criterios estrictos para determinar la validez de la hipótesis inicial:

1. FILTRO DE CADUCIDAD TEMPORAL POST-RUPTURA (CRÍTICO):
   - Si la posición se abrió basándose en un patrón de Geometría Rígida (Doble Techo/Suelo, HCH) pero el precio actual (Vela 0) lleva más de 4 velas oscilando cerca del precio de entrada sin avanzar al menos 1.0x VP_actual a favor del movimiento, la hipótesis ha caducado. Dicta 'Cerrar' inmediatamente para mitigar el riesgo de un giro violento.

2. INVALIDEZ POR TENDENCIA LATERAL EXTREMA:
   - EXCEPCIÓN: Si el patrón de origen es "OPERACIÓN EXCLUSIVA EN RANGO LATERAL", ignora por completo este filtro de invalidez lateral.
   - ESCENARIO A (Compresión Base): Si el Rango de Compresión Lateral (RCL) de las últimas 7 velas es menor a 1.2 veces tu VP_actual (RCL < 1.2x VP_actual), el mercado ha entrado en una consolidación muerta. Si tu patrón de origen era de Continuación o Geometría Rígida, dicta 'Cerrar' inmediatamente.
     * [Algoritmo de Conteo Retroactivo]: Evalúa de forma retrospectiva (Vela -1, Vela -2, etc.) cuántas velas consecutivas previas mantuvieron de forma ininterrumpida la condición de que su rango local de 7 velas fuera menor a 1.2 x VP_actual para determinar el Bloque de Compresión Actual (BCA).
   - ESCENARIO B (Falsa Volatilidad por Vela Única): Si el RCL es mayor a 1.2x VP_actual, pero el tamaño promedio (High - Low) de las últimas 3 velas cerradas es menor a 0.6x VP_actual, el momentum actual se ha evaporado. Dicta 'Cerrar' de forma fulminante.
   - ESCENARIO C (Excepción por Ruptura Activa): El estado de invalidez lateral queda ANULADO si el precio de cierre de la Vela 0 rompe por absorción bajo la lógica del "Patrón de Ausencia de Rechazo" (Regla 5 del prompt de apertura), evaluando el rango dinámico de Lookback (si BCA >= 10 velas, usa extremos del BCA; si BCA < 10 velas, usa extremos de las últimas 15 velas totales).

3. EVALUACIÓN DE DESTRUCCIÓN ESTRUCTURAL DE RANGOS Y VELAS:
   - Si el patrón de origen es "OPERACIÓN EXCLUSIVA EN RANGO LATERAL":
     * En COMPRA (Suelo): Si la Vela 0 cierra rompiendo estrictamente por debajo del Mínimo Local del RCL de las últimas 7 velas que defendía la estructura previa, dicta 'Cerrar' de forma fulminante.
     * En VENTA (Techo): Si la Vela 0 cierra rompiendo estrictamente por encima del Máximo Local del RCL de las últimas 7 velas que defendía la estructura previa, dicta 'Cerrar' de forma fulminante.

4. EVALUACIÓN DE PATRONES DE RECHAZO DE VELA ÚNICA O MÚLTIPLE EN EXTREMOS (TENDENCIA):
   - Si la posición se abrió bajo un patrón clásico en tendencia normal (Martillos, Envolventes, Estrellas):
     * En COMPRA: Si la Vela 0 cierra rompiendo de forma inversa el Mínimo Absoluto Macro de las 60 velas que defendía la estructura, o si aparece un patrón de rechazo bajista verificado (Estrella Fugace, Hombre Colgado, Envolvente Bajista o Estrella del Atardecer) en el Máximo Absoluto Macro o tercio superior del rango macro, dicta 'Cerrar'.
     * En VENTA: Si la Vela 0 cierra rompiendo de forma inversa el Máximo Absoluto Macro de las 60 velas que defendía la estructura, o si aparece un patrón de rechazo alcista verificado (Martillo, Martillo Invertido, Envolvente Alcista o Estrella del Amanecer) en el Mínimo Absoluto Macro o tercio inferior del rango macro, dicta 'Cerrar'.

5. AUDITORÍA ESPECÍFICA PARA EL PATRÓN DE AUSENCIA DE RECHAZO (Ruptura por Absorción / Momentum):
   - FILTRO DE FALLO INMEDIATO POR REVERSIÓN (CRÍTICO): Si la posición se abrió bajo el patrón "Ausencia de Rechazo en Extremos" y la Vela 0 cierra reingresando al rango previo (por debajo del Máximo Absoluto Macro en COMPRA, o por encima del Mínimo Absoluto Macro en VENTA), dicta 'Cerrar' inmediatamente a mercado.
   - FILTRO DE AGOTAMIENTO Y RECHAZO EN CONTRA: Si han pasado más de 2 velas desde la apertura de momentum y la Vela 0 cumple cualquiera de estas condiciones, dicta 'Cerrar' de forma fulminante:
     * Condición de Tamaño: El tamaño del cuerpo real de la Vela 0 es estrictamente < 0.5x VP_actual (pérdida de volumen de absorción).
     * Condición de Rechazo en COMPRA: La mecha superior de la Vela 0 es estrictamente ≥ 1.5x su propio cuerpo real.
     * Condición de Rechazo en VENTA: La mecha inferior de la Vela 0 es estrictamente ≥ 1.5x su propio cuerpo real.

### 5. ALGORITMO DE AUDITORÍA OPERATIVA (DECISIÓN DE REEVALUACIÓN)
Determina el dictamen final del campo `reevaluacion` aplicando estas directrices de gestión:

1. REGLA PARA 'Cerrar' (Liquidación Inmediata a Mercado):
   - Dicta 'Cerrar' si se activa cualquiera de las condiciones de invalidez por Caducidad Temporal, Tendencia Lateral Extrema, Destrucción Estructural o Fallo de Momentum/Fakeout detalladas en la sección 4.
   - Si el precio ha alcanzado el 80% del recorrido hacia tu [Take Profit original] pero la acción del precio se frena en seco formando un micro-rango lateral de 4 velas, dicta 'Cerrar' para tomar ganancias manuales.

2. REGLA PARA 'Ajustar' (Modificación de Niveles Pasivos con Enfoque Cauto):
   - Si la operación se desarrolla a favor de la tendencia bajo un patrón de TENDENCIA o MOMENTUM, y el precio avanzó superando la entrada por una distancia de al menos 1.0x VP_actual (pero aún no activa mecánicamente tu sistema de Trailing Stop original), dicta 'Ajustar'. Modifica el `stop_loss` al precio de entrada original (Breakeven) más un colchón a favor del movimiento de exactamente 0.3x VP_actual (sumar si es Compra, restar si es Venta).
   - RESTRICCIÓN DE CODICIA (SER CAUTO): Queda ESTRICTAMENTE PROHIBIDO alterar o expandir el [Take Profit original] de forma exagerada. El Take Profit original representa el objetivo estadístico real del patrón y debe permanecer intacto en su valor inicial.
   - AJUSTE REALISTA DEL TRAILING STOP: Si decides modificar el `trailing_stop_activation` debido a la nueva acción del precio, su nuevo valor debe ser un nivel técnico conservador (nunca superior a un ajuste adicional de +0.5x VP_actual respecto al nivel original).
   - AJUSTE ULTRA-RÁPIDO PARA AUSENCIA DE RECHAZO: Si el patrón de origen fue "Ausencia de Rechazo en Extremos" y la Vela 0 cierra a favor del movimiento logrando un beneficio de al menos 0.8x VP_actual, dicta 'Ajustar' de forma obligatoria. Eleva o baja el `stop_loss` al precio de entrada original (Breakeven) de forma inmediata.
   - REGLA DE RANGO LATERAL: Si el patrón de origen es "OPERACIÓN EXCLUSIVA EN RANGO LATERAL", queda estrictamente PROHIBIDO intentar ajustar o mover los niveles a Breakeven si no se ha alcanzado al menos el 70% del recorrido hacia el Take Profit original. Si se supera el 70% del recorrido, dicta 'Ajustar' y mueve el `stop_loss` al precio de entrada original de forma rígida.

3. REGLA PARA 'Mantener' (Sin Cambios en el Broker):
   - Si la estructura que gatilló el primer prompt sigue su curso limpio con velas de rango amplio a favor y no se detecta ninguna señal de estancamiento o patrón inverso, dicta 'Mantener'. Los precios objetivo permanecen intactos.

### 6. REGLAS PARA CAMPOS DE RETORNO Y CONSISTENCIA PYDANTIC
    - `decision_accion`: Recomendación de mercado basada exclusivamente en los datos actuales ("Comprar", "Vender", "Mantener"). Si estás auditando y la orden sigue vigente sin anomalías, establece "Mantener".
    - `reevaluacion`: Campo crítico de control operativo. Debe ser estrictamente uno de estos tres literales: "Mantener", "Cerrar" o "Ajustar", aplicando las reglas de la sección 5.
    - `precio_entrada`: Debe ser EXACTAMENTE el precio de 'Close' de la última vela (Vela 0) del set de datos provisto.
    - `velas_espera_validacion`: Determina con criterio cauto un número entero estrictamente entre 1 y 4 (máximo) para rellenar este campo:
        * Asigna 1 vela (5 minutos): Si dictas 'Ajustar' (para verificar inmediatamente el impacto de los nuevos niveles), si el precio actual está a menos de 0.5x VP_actual de tu Stop Loss o Take Profit, O SI EL PATRÓN DE ORIGEN ES "Ausencia de Rechazo en Extremos". Al ser operaciones de alta velocidad, el auditor debe despertar en la siguiente vela de forma obligatoria para reevaluar el momentum.
        * Asigna 2 velas (10 minutos): Si el precio se mueve de forma sana y ordenada a favor del movimiento.
        * Asigna 3 a 4 velas (15 a 20 minutos): Únicamente si el mercado se encuentra en una fase de Tendencia Lateral o Consolidación.
"""

INPUTS = [
    "velas",
    "precio_apertura",
    "take_profit",
    "stop_loss", 
    "trailing_stop",
    "explicacion",
    "beneficio_neto",
    "patron",    
    "operacion"
]

class PuntosControlGroq(BaseModel):
    model_config = ConfigDict(extra="forbid")
    primer_pico: float = Field(0.0, description="Precio del primer pico o suelo.")
    segundo_pico: float = Field(0.0, description="Precio del segundo pico o suelo.")
    linea_cuello: float = Field(0.0, description="Precio de la línea de cuello (neckline).")
    zona_soporte: float = Field(0.0, description="Precio del soporte del rango lateral si aplica.")
    zona_resistencia: float = Field(0.0, description="Precio de la resistencia del rango lateral si aplica.")

class Esquema(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    reevaluacion: Optional[Literal["Mantener", "Cerrar", "Ajustar"]] = Field(
        "Mantener", 
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
    explicacion_reevaluacion: Optional[str] = Field(
        "", 
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
    puntos_control_patron: PuntosControlGroq = Field(
        ...,
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
   stop_loss_ajustado = float(parametros.STOP_LOSS)  - float(parametros.diferencia_precio)
   trailing_stop_ajustado = float(parametros.TRAILING_STOP) - float(parametros.diferencia_precio)

   datos = {
      "velas": velas,
      "precio_apertura": precio_apertura_ajustado,
      "take_profit": take_profit_ajustado,
      "stop_loss": stop_loss_ajustado,
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