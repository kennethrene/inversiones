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
    datos_en_texto = formatear_velas_para_ia(velas)

    if velas != None and len(velas) > 0 :
        response = client.models.generate_content(
            model=parametros.MODELO_IA,
            contents=f"""
            Estás actuando como un Sistema Core de Ejecución Cuantitativa y Gestión de Riesgos de Alta Precisión. Tu función es procesar en el segundo cero del inicio de una nueva vela un arreglo cronológico de precios, calcular internamente métricas estadísticas, de volatilidad y la pendiente de la banda central, validar confluencias bajo reglas algebraicas estrictas y devolver una decisión operativa de apertura unívoca.

            ### CONTEXTO Y ENTRADA DE DATOS
            - Temporalidad: 5 minutos por vela (M5).
            - Ventana de observación: Últimas 60 velas cerradas (ordenadas cronológicamente de la más antigua a la más reciente). La última vela define el precio actual del mercado.
            - Datos de Precios suministrados: 
            * Serie temporal OHLC: {datos_en_texto}

            ### INSTRUCCIONES DE PRECALCULO OPERATIVO E INDICADORES INTERNOS
            Antes de evaluar cualquier patrón, debes realizar un análisis estadístico estricto sobre el arreglo para calcular tus métricas de referencia:
            1. Banda Central Actual (Media Móvil): Calcula el precio promedio de cierre de las últimas 20 velas del set de datos (Velas 41 a 60).
            2. Banda Central Previa (Punto de Comparación): Calcula el precio promedio de cierre de las 20 velas anteriores que finalizan 5 velas atrás (Velas 36 a 55).
            3. Pendiente / Inclinación de la Tendencia: Resta [Banda Central Actual - Banda Central Previa]:
            - Pendiente Alcista Fuerte: Si el resultado es positivo y es mayor a 0.5x de tu "Vela Promedio" (VP).
            - Pendiente Bajista Fuerte: Si el resultado es negativo y su valor absoluto es mayor a 0.5x de tu "Vela Promedio" (VP).
            - Pendiente Plana / Neutra: Si el resultado se mantiene en un rango comprimido intermedio, indicando falta de fuerza tendencial.
            4. Rango de Volatilidad de Bandas: Define la Banda Superior en el máximo local de las últimas 20 velas y la Banda Inferior en el mínimo local de las últimas 20 velas.
            5. Estimación de Volatilidad Base (VP): Calcula el tamaño promedio (Máximo - Mínimo) de las últimas 10 velas de todo el arreglo.

            ### REGLAS ALGORÍTMICAS DE VALIDACIÓN DE ENTRADAS CON FILTRO DE INCLINACIÓN

            1. GEOMETRÍA RÍGIDA (Doble Techo/Suelo, HCH):
            - Exige una tolerancia máxima de ±0.05% de diferencia matemática en los extremos.
            - Restricción de Pendiente: Prohíbe operar patrones de reversión (Doble Techo o HCH) si la Pendiente de la Banda Central sigue clasificada como "Alcista Fuerte", ya que la inercia del mercado anula el patrón. Exige que la pendiente sea Neutra/Plana para validar el giro.

            2. CONTINUACIÓN (Banderas, Cuñas):
            - Exige compresión matemática del rango antes de la ruptura.
            - Confluencia de Pendiente obligatoria: Solo se permite una entrada en "Comprar" en banderas si la Pendiente es "Alcista Fuerte". Solo se permite "Vender" en cuñas/banderas si la Pendiente es "Bajista Fuerte". Si la pendiente es plana, descarta el patrón de continuación.

            3. CONFLUENCIA DE RECHAZO Y BANDAS DE BOLLINGER INTERNAS:
            - Ignora por completo patrones de rechazo en zonas medias.
            - COMPRA: El patrón de rechazo alcista debe tocar la Banda Inferior calculada Y la Pendiente debe ser Neutra o Alcista. Prohibido comprar si la Pendiente es "Bajista Fuerte" (no operes contra el flujo).
            - VENTA: El patrón de rechazo bajista debe tocar la Banda Superior calculada Y la Pendiente debe ser Neutra o Bajista. Prohibido vender si la Pendiente es "Alcista Fuerte".

            4. FILTRO DE FALSOS ROMPIMIENTOS (Fakeouts):
            - Si la última vela perforó tu Banda Superior o Inferior pero regresó y CERRÓ dentro del rango previo dejando una mecha larga, clasifícalo como "Fakeout".
            - Gatillo de Reversión: Si ocurre en la Banda Inferior con pendiente plana/neutra, la acción es "Comprar". Si ocurre en la Banda Superior con pendiente plana/neutra, es "Vender". El Stop Loss se coloca en el extremo exacto de la mecha.

            5. FILTRO DE TENDENCIA LATERAL (Compresión de Bandas):
            - Si la distancia total entre tu Banda Superior e Inferior calculada es menor a 2.5 veces tu VP, O la Pendiente es estrictamente "Plana / Neutra", el mercado está en consolidación.
            - Prohíbe operaciones de ruptura. Permite únicamente operaciones de reversión rápida a la media en los extremos exactos de las bandas externas buscando la banda central. Si el precio está cerca de la banda central, la acción obligatoria es "Mantener".

            ### REGLAS DE TRAILING STOP Y PROTECCIÓN DE BENEFICIOS (REALISTA)
            1. ACTIVACIÓN DEL TRAILING STOP: Establece `trailing_stop_activation` a una distancia matemática de EXACTAMENTE 1.2 veces tu "Vela Promedio" (VP) a favor de la operación desde el precio de entrada.
            2. PRECIO DE PROTECCIÓN INICIAL Y SEGUIMIENTO:
            - Al tocar el `trailing_stop_activation`, el Stop Loss debe moverse a una zona segura: [Precio de Entrada + 0.3x VP] en Compras, o [Precio de Entrada - 0.3x VP] en Ventas, asegurando un beneficio base real.
            - A partir de ahí, la distancia de seguimiento por trailing será de 1.2x VP.

            ### REGLAS ESTRICTAS DE EVALUACIÓN OPERATIVA Y PLANIFICACIÓN DE AUDITORÍA
            1. Precio de Entrada: Será exactamente el precio de CIERRE de la última vela (mercado instantáneo).
            2. Direcciones permitidas: "Comprar", "Vender", "Mantener".
            3. Consistencia de Signos:
            - Si "Comprar": `take_profit` y `trailing_stop_activation` > `precio_entrada`. `stop_loss` < `precio_entrada`.
            - Si "Vender": `take_profit` y `trailing_stop_activation` < `precio_entrada`. `stop_loss` > `precio_entrada`.
            4. Take Profit Objetivo: Distancia de entre 1.5x y 2.0x VP, o hazlo coincidir con la Banda de Bollinger opuesta si el mercado está en fase lateral.
            5. Cálculo Dinámico de Ventana de Auditoría (`velas_espera_validacion`): Número entero de 1 al 12:
            - Asigna de 1 a 2 velas ante alta volatilidad o ruptura inminente de bandas.
            - Asigna de 3 a 6 velas si se opera con Pendiente Fuerte (Alcista/Bajista) a favor de la tendencia.
            - Asigna de 6 a 12 velas si la Pendiente es estrictamente Plana/Neutra.
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
        puntos_control = resultado["puntos_control_patron"]

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

        response = client.models.generate_content(
            model=parametros.MODELO_IA,
            contents=f"""
            Estás actuando como un Auditor Cuantitativo de Riesgos y Administrador de Posiciones en Tiempo Real. Tu única función es evaluar una operación abierta previamente, analizar el desarrollo del precio a través de una nueva serie temporal de 60 velas M5 cruzando los datos con los cálculos matemáticos y cualitativos del análisis original, y dictaminar si la posición debe mantenerse, cerrarse inmediatamente o ajustar sus parámetros de riesgo.

            ### 1. DATOS DE LA POSICIÓN ABIERTA ACTUALMENTE Y CÁLCULOS DEL PRIMER PROMPT
            - Dirección original: {parametros.datos_mapeados['Operacion']}
            - Precio de entrada original: {precio_apertura_ajustado}
            - Take Profit original: {take_profit_ajustado}
            - Stop Loss original: {stop_loss_ajustado}
            - Trailing Stop original: {trailing_stop_ajustado}
            - Beneficio Neto actual: {parametros.datos_mapeados['Beneficio Neto']}
            - Patrón identificado previamente: {parametros.datos_mapeados["Patron"]}
            - Justificación técnica previa: {parametros.explicacion_decision}

            ### 2. NUEVA ENTRADA DE DATOS (M5 - 60 VELAS ACTUALIZADAS)
            - Serie temporal OHLC actual (la última fila es la vela actual '0' recién cerrada y define el precio de mercado actual):
            {datos_en_texto}

            ### 3. INSTRUCCIONES DE PRECALCULO OPERATIVO E INDICADORES INTERNOS
            Antes de evaluar cualquier regla, debes realizar un análisis estadístico estricto sobre el arreglo de datos para calcular tus métricas de referencia:
            1. Banda Central Actual (Media Móvil): Calcula el precio promedio de cierre de las últimas 20 velas del set de datos (Velas 41 a 60).
            2. Banda Central Previa (Punto de Comparación): Calcula el precio promedio de cierre de las 20 velas anteriores que finalizan 5 velas atrás (Velas 36 a 55).
            3. Pendiente / Inclinación de la Tendencia: Resta [Banda Central Actual - Banda Central Previa]:
            - Pendiente Alcista Fuerte: Si el resultado es positivo y es mayor a 0.5x de tu "Vela Promedio" (VP).
            - Pendiente Bajista Fuerte: Si el resultado es negativo y su valor absoluto es mayor a 0.5x de tu "Vela Promedio" (VP).
            - Pendiente Plana / Neutra: Si el resultado se mantiene en un rango comprimido intermedio, indicando falta de fuerza tendencial.
            4. Rango de Volatilidad de Bandas: Define la Banda Superior en el máximo local de las últimas 20 velas y la Banda Inferior en el mínimo local de las últimas 20 velas.
            5. Estimación de Volatilidad Base (VP): Calcula el tamaño promedio (Máximo - Mínimo) de las últimas 10 velas de todo el arreglo.

            ### 4. REGLAS ALGORÍTMICAS DE VALIDACIÓN DE ENTRADAS CON FILTRO DE INCLINACIÓN (PARA AUDITORÍA)
            Utiliza estas reglas de la estrategia raíz para verificar si el precio actual ha violado las condiciones de validez estructural de la operación activa:

            1. GEOMETRÍA RÍGIDA (Doble Techo/Suelo, HCH):
            - Exige una tolerancia máxima de ±0.05% de diferencia matemática en los extremos.
            - Restricción de Pendiente: Si la operación original es una reversión (Doble Techo o HCH) pero la Pendiente de la Banda Central calculada sigue clasificada como "Alcista Fuerte" o "Bajista Fuerte" en contra de la operación, la inercia anula el patrón. La estructura es inválida.

            2. CONTINUACIÓN (Banderas, Cuñas):
            - Exige compresión matemática del rango antes de la ruptura.
            - Confluencia de Pendiente obligatoria: Una posición de COMPRA en bandera solo es válida si la Pendiente es "Alcista Fuerte". Una posición de VENTA en cuña/bandera solo es válida si la Pendiente es "Bajista Fuerte". Si la pendiente se aplanó, la continuación perdió validez.

            3. CONFLUENCIA DE RECHAZO Y BANDAS DE BOLLINGER INTERNAS:
            - Ignora por completo patrones de rechazo en zonas medias.
            - COMPRA: El patrón de rechazo alcista debe tocar la Banda Inferior calculada Y la Pendiente debe ser Neutra o Alcista. Es inválido si la Pendiente es "Bajista Fuerte".
            - VENTA: El patrón de rechazo bajista debe tocar la Banda Superior calculada Y la Pendiente debe ser Neutra o Bajista. Es inválido si la Pendiente es "Alcista Fuerte".

            4. FILTRO DE FALSOS ROMPIMIENTOS (Fakeouts Inversos de Salida):
            - Si la última vela perforó tu Banda Superior o Inferior pero regresó y CERRÓ dentro del rango previo dejando una mecha larga, clasifícalo como "Fakeout".
            - Aplicación en Auditoría: Si este Fakeout ocurre en la banda opuesta a tu operación activa (ej. estás comprado y hay un Fakeout bajista en la Banda Superior), utilízalo como señal de salida forzada. La estructura original fue vulnerada y debes proteger el capital.

            5. FILTRO DE TENDENCIA LATERAL (Compresión de Bandas):
            - Si la distancia total entre tu Banda Superior e Inferior calculada es menor a 2.5 veces tu VP, O la Pendiente es estrictamente "Plana / Neutra", el mercado está en consolidación.
            - En este escenario se prohíben rupturas. Solo son válidas operaciones de reversión rápida a la media en los extremos exactos de las bandas externas buscando la banda central. Si el precio se estanca cerca de la banda central, la orden activa perdió su momentum.

            ### 5. ALGORITMO DE AUDITORÍA OPERATIVA (DECISIÓN DE REEVALUACIÓN)
            Cruza los hallazgos de las secciones 3 y 4 con el [Beneficio Neto actual] para determinar el dictamen final de `reevaluacion`:

            1. REGLA PARA 'Cerrar' (Liquidación Inmediata a Mercado):
            - Si la regla de Geometría Rígida, Continuación o Rechazo ha sido declarada INVÁLIDA por un cambio violento en la Pendiente de la Banda Central en tu contra, dicta 'Cerrar'.
            - Si se activa un Fakeout Inverso en la banda opuesta según el punto 4 de la sección anterior, dicta 'Cerrar' inmediatamente para asegurar el [Beneficio Neto actual] positivo antes del retroceso.
            - Si el precio ha alcanzado el 80% del recorrido hacia tu [Take Profit original] pero el mercado entra en Compresión de Bandas (Tendencia Lateral), dicta 'Cerrar' para tomar ganancias manuales y liberar margen.

            2. REGLA PARA 'Ajustar' (Modificación de Niveles Pasivos):
            - Si el [Beneficio Neto actual] es positivo y el precio avanzó a favor superando el [Precio de entrada original] por una distancia de 1.0x VP, pero aún no activa mecánicamente el [Trailing Stop original], dicta 'Ajustar'. Recomienda elevar el `stop_loss` al precio de entrada (Breakeven) + un colchón de 0.3x VP.
            - Si la posición está en una fase de Pendiente Plana / Neutra (Tendencia Lateral) por más de 7 velas sin fuerza para alcanzar el [Take Profit original], dicta 'Ajustar' y reduce tu Take Profit acercándolo al precio de Cierre actual para forzar una salida exitosa.

            3. REGLA PARA 'Mantener' (Sin Cambios en el Broker):
            - Si las confluencias que originaron la posición siguen siendo 100% válidas, las bandas se expanden a favor y la Pendiente ratifica la dirección original de la orden, dicta 'Mantener'. Los precios objetivo permanecen intactos.

            ### 6. REGLAS PARA CAMPOS DE RETORNO Y CONSISTENCIA PYDANTIC
            - `reevaluacion`: Campo crítico de control operativo. Debe ser estrictamente uno de estos tres literales: "Mantener", "Cerrar" o "Ajustar", aplicando las reglas de la sección 5.
            - `precio_entrada`: Debe ser EXACTAMENTE el precio de 'Close' de la última vela (Vela 0) del set de datos provisto.
            - `velas_espera_validacion`: Calcula un entero entre 1 y 10. Si dictas 'Ajustar' o el mercado está muy volátil, reduce el valor a 1 o 2 velas.
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
        puntos_control = resultado["puntos_control_patron"]

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

