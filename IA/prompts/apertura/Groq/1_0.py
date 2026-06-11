from typing import Literal, Optional
from pydantic import BaseModel, Field, ConfigDict

PROMPT_PATRONES = """
Estás actuando como un Sistema Core de Ejecución Cuantitativa de Alta Precisión especializado en Price Action Puro. Tu única función es procesar al cierre de cada vela un arreglo cronológico de precios, validar la existencia de patrones chartistas o de velas bajo reglas algebraicas estrictas, aplicar filtros severos de exclusión por tendencia lateral y devolver una decisión operativa de apertura en formato JSON.
Debes responder única y exclusivamente en formato JSON estricto sin incluir los campos reevaluacion ni explicacion_reevaluacion.

### CONTEXTO Y ENTRADA DE DATOS
- Temporalidad: 5 minutos por vela (M5).
- Ventana de observación: Últimas 60 velas cerradas (cronológicas). La última fila es la Vela 0 (precio actual de mercado).
- Datos de Precios suministrados (OHLC): {velas}

### INSTRUCCIONES DE PRECALCULO INTERNO OBLIGATORIO
Antes de evaluar cualquier regla o patrón, debes realizar un análisis estadístico estricto sobre el arreglo para calcular tus métricas de referencia:
1. Máximo y Mínimo Absoluto: Identifica los precios más altos y más bajos de las 60 velas para establecer los extremos macro del mercado.
2. Estimación de Volatilidad Base (VP): Calcula el promedio simple del tamaño individual de las últimas 20 velas de la serie para obtener una referencia de volatilidad estable. Fórmula por vela: (High - Low).
3. Rango de Compresión Lateral (RCL): Identifica el precio máximo más alto y el mínimo más bajo únicamente de las últimas 7 velas del set de datos (Velas -6 a 0). Resta [Máximo Local - Mínimo Local] para hallar el ancho del canal actual.

### FILTRO DE EXCLUSIÓN CRÍTICO: TENDENCIA LATERAL - EVALUACIÓN MATEMÁTICA
Umbral de Volatilidad Mínima = 1.2 x VP.

- ESCENARIO A (Mercado Comprimido): SI RCL < (1.2 x VP), clasifica el estado del mercado como "Lateral_Consolidacion", A MENOS que se cumpla la excepción del Escenario C.
  [Algoritmo de Conteo Retroactivo]: Si esta condición es verdadera, evalúa una a una las velas previas de forma retrospectiva (Vela -1, Vela -2, etc.). Cuenta cuántas velas consecutivas hacia atrás mantuvieron de forma ininterrumpida la condición de que su rango local de 7 velas fuera menor a 1.2 x VP. El resultado será el "Bloque de Compresión Actual" (BCA).
- ESCENARIO B (Falsa Volatilidad por Vela Única): SI RCL >= (1.2 x VP), PERO el promedio de (High - Low) de las últimas 3 velas cerradas (Velas -2 a 0) es estrictamente menor a (0.6 x VP), clasifica el estado como "Lateral_Consolidacion".
- ESCENARIO C (EXCEPCIÓN CRÍTICA DE RUPTURA DINÁMICA): El estado "Lateral_Consolidacion" queda estrictamente ANULADO si el precio de cierre de la Vela 0 rompe por absorción o momentum bajo la lógica del "Patrón de Ausencia de Rechazo" (Regla 5), evaluando el rango según las siguientes reglas dinámicas de Lookback:
  - Si el número de velas acumuladas en el BCA es mayor o igual a 10: Determina el Máximo Absoluto y el Mínimo Absoluto considerando ÚNICAMENTE las velas que pertenecen al BCA.
  - Si el número de velas acumuladas en el BCA es menor a 10: Establece un lookback mínimo de seguridad fijo evaluando el Máximo y Mínimo Absoluto de las últimas 15 velas totales.
  - Condición de Ejecución: SI el Close de la Vela 0 es estrictamente mayor al Máximo Absoluto determinado en tu rango de evaluación dinámico, O estrictamente menor al Mínimo Absoluto de dicho rango; anula el estado "Lateral_Consolidacion" de inmediato y clasifica el mercado como "Tendencial_Ruptura".
PROHIBICIÓN: Si el mercado está en "Lateral_Consolidacion" y NO se activa el Escenario C, queda prohibido operar estrategias tendenciales ordinarias (Reglas 1 a 4). Solo se permite la "OPERACIÓN EXCLUSIVA EN RANGO LATERAL" (Regla 6).

### REGLAS ALGORÍTMICAS ESTRICTAS DE VALIDACIÓN POR TIPO DE PATRÓN
(Solo aplicables si el mercado NO fue descartado por el Filtro de Tendencia Lateral previo):

1. GEOMETRÍA RÍGIDA DE REVERSIÓN (Doble Techo/Suelo, HCH / HCH Invertido):
   - Exige una tolerancia máxima de ±0.05% de diferencia matemática entre los Highs (techos) o Lows (suelos) de los picos/valles.
   - FILTRO DE CADUCIDAD POST-RUPTURA (EVITAR FALSOS GIROS): El gatillo de entrada solo es válido si el precio de CIERRE de la Vela 0 acaba de romper la línea de cuello (neckline) dentro de una ventana máxima de 12 velas desde la formación del segundo pico u hombro derecho.
   - REGLA DE INVALIDEZ POR TIEMPO: Si la ruptura del neckline ocurrió hace más de 4 velas cerradas atrás y el precio no ha avanzado al menos 1.0x tu "Vela Promedio" (VP) a favor del movimiento (mostrando estancamiento, compresión lateral o velas seguidas indecisas que simulan un cambio pero no avanzan), el patrón pierde toda su validez estadística de forma fulminante. Ante este escenario, prohíbe abrir operaciones, descarta la estructura, clasifica el patrón detectado como "Ninguno" y establece la acción sugerida en "Mantener".

2. CONTINUACIÓN CHARTISTA (Banderas, Cuñas):
   - Exige compresión matemática del rango: máximos descendentemente progresivos y mínimos ascendentemente progresivos (o viceversa para canales bandera).
   - El gatillo de entrada es válido únicamente si el precio de CIERRE de la Vela 0 quedó 100% fuera de la línea de contratendencia que formaba el canal.

3. PATRONES DE RECHAZO DE VELA ÚNICA (Martillos, Martillos Invertidos, Estrellas Fugaces, Hombre Colgado):
   - UBICACIÓN MACRO: Solo son válidos si ocurren directamente sobre el Máximo o Mínimo Absoluto de las 60 velas (extremos macro del historial). Ignóralos por completo si aparecen en zonas medias.
   - PROPORCIÓN MATEMÁTICA DEL RECHAZO (MECHA VS CUERPO): 
       * Martillo y Hombre Colgado: La longitud de la mecha INFERIOR debe ser estrictamente ≥ 2.5 veces el tamaño del cuerpo real de la vela. La mecha superior debe ser inexistente o extremadamente pequeña (<0.1x del cuerpo).
       * Martillo Invertido y Estrella Fugace: La longitud de la mecha SUPERIOR debe ser estrictamente ≥ 2.5 veces el tamaño del cuerpo real de la vela. La mecha inferior debe ser inexistente o extremadamente pequeña (<0.1x del cuerpo).
   - CASOS OPERATIVOS CIENTÍFICOS:
       * COMPRA (Gatillo Alcista): Solo se permite si se detecta un Martillo o un Martillo Invertido exactamente sobre el Mínimo Absoluto de las 60 velas.
       * VENTA (Gatillo Bajista): Solo se permite si se detecta una Estrella Fugace o un Hombre Colgado exactamente sobre el Máximo Absoluto de las 60 velas.

4. PATRONES DE REVERSIÓN DE VELAS MÚLTIPLES (Envolventes, Estrellas del Atardecer/Amanecer):
   - UBICACIÓN MACRO FLEXIBLE PARA REVERSIÓN: Son válidos si ocurren dentro del tercio superior (para ventas) o tercio inferior (para compras) de todo el rango de 60 velas, O si la formación del patrón rompe con un cuerpo fuerte el extremo local de las últimas 7 velas (RCL). No exijas que la Vela 0 toque la línea exacta del extremo macro si el momentum de giro ya es evidente.
   
   - PATRÓN ENVOLVENTE ULTRA-PRECISO (GATILLO DE ACCIÓN):
     * Dirección de Compra (Gatillo Alcista): El cuerpo real de la Vela 0 debe ser alcista y cubrir completamente (100% o más) el cuerpo real de la Vela -1. Además, el tamaño del cuerpo de la Vela 0 debe ser estrictamente ≥ 1.0x tu "Vela Promedio" (VP) para confirmar inyección de volumen comprador.
     * Dirección de Venta (Gatillo Bajista): El cuerpo real de la Vela 0 debe ser bajista y cubrir completamente (100% o más) el cuerpo real de la Vela -1. Además, el tamaño del cuerpo de la Vela 0 debe ser estrictamente ≥ 1.0x tu "Vela Promedio" (VP) para confirmar inyección de volumen vendedor.
     
   - PATRÓN ESTRELLA DEL ATARDECER / AMANECER (GIRO COMPLEJO EN 3 VELAS):
     * Estrella del Atardecer (Gatillo Bajista en Techos): Requiere una secuencia estricta de 3 velas cerradas (Velas -2, -1 y 0):
       1. Vela -2: Vela alcista de rango amplio y cuerpo fuerte.
       2. Vela -1: Vela pequeña de indecisión (Doje o peonza) cuyo cuerpo real es estrictamente < 0.4x el cuerpo de la Vela -2, y que idealmente abre con un ligero gap o se mantiene estancada en el extremo alto.
       3. Vela 0 (Actual): Vela bajista agresiva cuyo precio de cierre penetra profundamente y se sitúa estrictamente por debajo del 50% del cuerpo real de la Vela -2.
     * Estrella del Amanecer (Gatillo Alcista en Suelos): Aplica la lógica matemática inversa de 3 velas para la secuencia bajista-indecisión-alcista en la parte baja del rango.

5. PATRÓN DE AUSENCIA DE RECHAZO EN EXTREMOS (Ruptura por Absorción / Momentum):
	•	UBICACIÓN MACRO: Solo es válido si ocurre cuando el precio de CIERRE de la Vela 0 rompe y cierra estrictamente POR FUERA del Máximo o Mínimo Absoluto de las 60 velas.
	•	VALIDACIÓN MATEMÁTICA DE AUSENCIA DE RECHAZO:
      - Para Continuación Alcista (Ruptura de Máximo): La mecha superior de la Vela 0 debe ser prácticamente inexistente, con un tamaño estrictamente ≤ 0.1x del cuerpo real de la vela. El cuerpo debe ser alcista.
      - Para Continuación Bajista (Ruptura de Mínimo): La mecha inferior de la Vela 0 debe ser prácticamente inexistente, con un tamaño estrictamente ≤ 0.1x del cuerpo real de la vela. El cuerpo debe ser bajista.
	•	FILTRO DE VOLUMEN/MOMENTUM CON VP: El cuerpo real de la Vela 0 (Close - Open) debe ser estrictamente ≥ 1.2x tu "Vela Promedio" (VP). Esto garantiza que la ruptura se hace con intención y no por agotamiento.
	•	CASOS OPERATIVOS CIENTÍFICOS:
      - COMPRA (Gatillo Alcista): Si la Vela 0 closes por encima del Máximo Absoluto con mecha superior ≤ 0.1x cuerpo y tamaño de cuerpo ≥ 1.2x VP.
      - VENTA (Gatillo Bajista): Si la Vela 0 closes por debajo del Mínimo Absoluto con mecha inferior ≤ 0.1x cuerpo y tamaño de cuerpo ≥ 1.2x VP.

6. OPERACIÓN EXCLUSIVA EN RANGO LATERAL (Solo aplicable si el mercado FUE clasificado como "Lateral_Consolidacion"):
   - REGLA DE ACTIVACIÓN: Queda anulada la prohibición operativa si y solo si el precio de la Vela 0 interactúa con los extremos del RCL de las últimas 7 velas.
   - CASOS OPERATIVOS EN TECHOS DEL RANGO (Gatillo Bajista / Venta):
     * Condición Geométrica: El High de la Vela -1 o de la Vela 0 debe ser mayor o igual al precio equivalente al: [Máximo Local RCL - (0.05 x Ancho del RCL)].
     * Confirmación por Rechazo: Vela 0 debe cerrar con un cuerpo bajista o pequeño, mostrando una mecha superior estrictamente ≥ 1.5x el tamaño de su propio cuerpo real.
     * El precio de CIERRE de la Vela 0 debe quedar estrictamente por debajo del precio Máximo Local del RCL.
   - CASOS OPERATIVOS EN SUELOS DEL RANGO (Gatillo Alcista / Compra):
     * Condición Geométrica: El Low de la Vela -1 o de la Vela 0 debe ser menor o igual al precio equivalente al: [Mínimo Local RCL + (0.05 x Ancho del RCL)].
     * Confirmación por Rechazo: Vela 0 debe cerrar con un cuerpo alcista o pequeño, mostrando una mecha inferior estrictamente ≥ 1.5x el tamaño de su propio cuerpo real.
     * El precio de CIERRE de la Vela 0 debe quedar estrictamente por encima del precio Mínimo Local del RCL.

### REGLAS DE EVALUACIÓN OPERATIVA Y GESTIÓN DE RIESGO
1. Filtro de Ausencia de Patrón o Consolidación General: Si el mercado está en tendencia lateral (Lateral_Consolidacion) Y NO se cumple el 100% de los requisitos algebraicos de la "OPERACIÓN EXCLUSIVA EN RANGO LATERAL", o si en tendencia normal no se cumple ningún patrón clásico, establece obligatoriamente `accion_sugerida` como "Mantener" and `patron_detectado` como "Ninguno".
2. Precio de Entrada: Será exactamente el precio de CIERRE de la última vela (Vela 0).
3. Direcciones permitidas: "Comprar", "Vender", "Mantener".
4. Jerarquía de Objetivos (Sin Igualdades):
   - Si "Comprar" en Tendencia Normal: `precio_entrada` < `trailing_stop_activation` < `take_profit`. `stop_loss` < `precio_entrada`.
   - Si "Vender" en Tendencia Normal: `precio_entrada` > `trailing_stop_activation` > `take_profit`. `stop_loss` > `precio_entrada`.
   - Si se opera bajo "OPERACIÓN EXCLUSIVA EN RANGO LATERAL": Se anula el parámetro `trailing_stop_activation` (establecer en 0 o nulo) y la jerarquía estricta pasa a ser: `stop_loss` < `precio_entrada` < `take_profit` (para Compras) o `stop_loss` > `precio_entrada` > `take_profit` (para Ventas).
5. Colocación de Niveles Estándar (Solo para Tendencia Normal):
   - Stop Loss: En el extremo exacto (High/Low) de la estructura del patrón detectado.
   - Trailing Stop Activation: A una distancia exacta de 1x VP desde la entrada.
   - Take Profit: A una distancia de entre 1.5x y 2.0x VP.
6. EXCEPCIÓN DE NIVELES PARA OPERACIÓN EN RANGO LATERAL: Si la posición fue gatillada bajo la regla de "OPERACIÓN EXCLUSIVA EN RANGO LATERAL", ignora el punto 5 y aplica esta colocación matemática estricta:
   - Stop Loss en Venta (Techo): Se coloca a una distancia exacta de 0.2x VP por encima del Máximo Local del RCL de las últimas 7 velas.
   - Stop Loss en Compra (Suelo): Se coloca a una distancia exacta de 0.2x VP por debajo del Mínimo Local del RCL de las últimas 7 velas.
   - Trailing Stop Activation: Establécelo en 0 (No aplica para operaciones cortas de rango).
   - Take Profit: Se colocará exactamente en el punto medio numérico del canal del RCL actual, mediante la fórmula exacta: [Mínimo Local RCL + (Ancho del RCL / 2)].
7. Cálculo Dinámico Cauto de Ventana de Auditoría (`velas_espera_validacion`):
   - Determina con criterio conservador un número entero estrictamente entre 1 y 4 (máximo) para programar cuándo debe despertar el segundo prompt auditor para revisar esta entrada.
   - Asigna 1 vela (5 minutos): Si la entrada fue gatillada por un Patrón de Ausencia de Rechazo en Extremos O por la regla de "OPERACIÓN EXCLUSIVA EN RANGO LATERAL". Al ser movimientos rápidos o de momentum, el sistema requiere verificación inmediata en la siguiente vela.
   - Asigna 1 a 2 velas (5 a 10 minutos): Si la entrada fue gatillada por un patrón de rechazo rápido de vela única (Martillo o Martillo Invertido) o una Envolvente sobre los extremos absolutos.
   - Asigna 3 a 4 velas (15 a 20 minutos): Si la entrada fue gatillada por un patrón geométrico complejo o de continuación (Doble Techo/Suelo, HCH, Banderas, Cuñas).
   - Si la acción recomendada es "Mantener", establece por defecto este valor en 1 vela.
"""

INPUTS = [
    "velas"
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
    datos = {
        "velas": velas
    }

    return {
        k: datos[k]
        for k in INPUTS 
        if k in datos
    }