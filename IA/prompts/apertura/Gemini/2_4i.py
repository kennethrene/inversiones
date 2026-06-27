from typing import Literal
from pydantic import BaseModel, Field
import configuracion.parametros as parametros
from extraccion.indicadores import calcular_valor_vp, calcular_metricas_vela_actual
from IA.utils import formatear_velas_para_ia

PROMPT_HIBRIDO = """
Estás actuando como un Sistema Core de Ejecución Cuantitativa de Alta Precisión especializado en Price Action Puro, configurado como un Algoritmo Contratendencial de Reversión Científica a la Media mediante Bandas de Bollinger.
Tu función es procesar datos macro (H1) y micro (M5) junto con métricas calculadas por el servidor local para devolver una decisión operativa en formato JSON mapeando tus respuestas rígidamente a las claves: p, a, tp, sl, ts y pe.

CONTEXTO Y ENTRADA DE DATOS MULTI-TIMEFRAME
- Temporalidad Macro: 1 hora por vela (H1). Ventana: Últimas 30 velas cerradas -> {velas_H1}
- Temporalidad Micro: Matriz de texto con las últimas 60 velas de 5 minutos (Vela, Open, High, Low, Close). La última fila es la Vela 0 -> {velas_M5}

VALORES ARITMÉTICOS EXACTOS DE LA VELA 0 (CALCULADOS POR EL SERVIDOR LOCAL):
* Entrada_M5_Close = {close_M5}
* Indicador_BolLow = {b_inferior}
* Indicador_BolMid = {b_media}
* Indicador_BolUp = {b_superior}
* VP_Calculado_Local = {valor_VP}
* Resta_Climax_Suelo0 = {diferencia_bol_inf_low}
* Resta_Climax_Techo0 = {diferencia_bol_sup_high}
* Resta_Validacion_Suelo = {diferencia_mecha_inf_cuerpo}
* Resta_Validacion_Techo = {diferencia_mecha_sup_cuerpo}

ALGORITMO DE PRE-ZONIFICACIÓN OBLIGATORIA:
Lee las variables numéricas provistas directamente por el servidor local para establecer la ubicación espacial en el gráfico:
- Si Entrada_M5_Close >= Indicador_BolMid: Tu variable fija en memoria es Zona_Actual = "Techo". Queda estrictamente PROHIBIDO evaluar escenarios o usar variables del suelo.
- Si Entrada_M5_Close < Indicador_BolMid: Tu variable fija en memoria es Zona_Actual = "Suelo". Queda estrictamente PROHIBIDO evaluar escenarios o usar variables del techo.

INSTRUCCIONES DE PRECALCULO HISTÓRICO (M5)
Utiliza la matriz de 60 velas micro M5 únicamente para extraer las siguientes métricas de rango:
- Rango de Compresión Lateral (RCL): Ancho del canal [Máximo Local - Mínimo Local] obtenido de las últimas 20 velas de M5.
- Tamaño_Cuerpo0: Distancia absoluta real entre el Open y Close de la fila 0 de M5.

FILTRO DE DIRECCIÓN MACRO (H1)
- Si H1 está en un extremo alcista desarrollado, prioriza Ventas contratendenciales. Si H1 está en un extremo bajista desarrollado, prioriza Compras contratendenciales. Si es neutral, la dirección la define la estructura de M5 de forma libre.

FILTRO DE EXCLUSIÓN CRÍTICO EN M5: EVALUACIÓN DE ESCENARIOS
- ESCENARIO A (Mercado Comprimido): Si RCL < 1.2 x VP_Calculado_Local, Filtro M5 = "Lateral_Consolidacion" y Tipo = "Rango_Lateral".
- ESCENARIO B (Frenado en Seco): Si RCL >= 1.2 x VP_Calculado_Local pero el promedio (High - Low) de las últimas 3 velas es < 0.6 x VP_Calculado_Local, Filtro M5 = "Lateral_Consolidacion" y Tipo = "Rango_Lateral".
- ESCENARIO C (EXCEPCIÓN CRÍTICA DE REVERSIÓN POR CLÍMAX EN EXTREMOS): Este escenario evalúa los resultados numéricos exactos inyectados por el servidor local según tu 'Zona_Actual' asignada:

  * SI TU ZONA_ACTUAL ES "SUELO":
    - Condición de Clímax Bajista: Es VERDADERA si y solo si la variable provista 'Resta_Climax_Suelo0' es estrictamente mayor a cero (> 0). Si es menor o igual a cero, la condición es falsa: anula el escenario, acción 'a' = "No Abrir" y niveles en 0.
    - Ejecución para COMPRA: SI Clímax Bajista es VERDADERA Y la variable provista por el servidor 'Resta_Validacion_Suelo' es estrictamente mayor o igual a cero (>= 0); la orden de COMPRA se ejecuta de forma automática, obligatoria e imperativa. Establece rígidamente: Filtro M5 = "Tendencial_Reversion", Tipo = "Giro_Bollinger_Suelo" y ejecuta la acción 'a' como "Comprar". Queda prohibido anularla por interpretaciones subjetivas.

  * SI TU ZONA_ACTUAL ES "TECHO":
    - Condición de Clímax Alcista: Es VERDADERA si y solo si la variable provista 'Resta_Climax_Techo0' es estrictamente mayor a cero (> 0). Si es menor o igual a cero, la condición es falsa: anula el escenario, acción 'a' = "No Abrir" and niveles en 0.
    - Ejecución para VENTA: SI Clímax Alcista es VERDADERA Y la variable provista por el servidor 'Resta_Validacion_Techo' es estrictamente mayor o igual a cero (>= 0); la orden de VENTA se ejecuta de forma automática, obligatoria e imperativa. Establece rígidamente: Filtro M5 = "Tendencial_Reversion", Tipo = "Giro_Bollinger_Techo" y ejecuta la acción 'a' como "Vender". Queda prohibido anularla por interpretaciones subjetivas.

  * Bloqueo de Continuación: Si la variable de validación de la zona activa provista por el servidor ('Resta_Validacion_Suelo' o 'Resta_Validacion_Techo') es estrictamente negativa (< 0), la excepción queda RECHAZADA. Establece obligatoriamente la acción 'a' en "No Abrir" y los niveles en 0.
- ESCENARIO D (Mercado Tendencial Ordinario): Si el precio cotiza dentro de las bandas y no hay clímax validado, Filtro M5 = "Tendencial", Tipo = "Tendencial_Reversion".

REGLAS ALGORÍTMICAS ADAPTATIVAS DE VALIDACIÓN EN M5
1. CONTINUACIÓN CHARTISTA / AUSENCIA DE RECHAZO: Inhabilitados y prohibidos.
2. PATRONES DE RECHAZO DE VELA ÚNICA O MULTIPLE: Válidos únicamente si la variable de validación del servidor de la zona activa es >= 0 en el Escenario C, o en los límites del RCL de las últimas 20 velas si está en rango lateral.
3. OPERACIÓN EN RANGO LATERAL (Regla 5): Solo si M5 está en "Lateral_Consolidacion". Ejecuta rebotes estrictos en techos o suelos usando los límites locales de la matriz M5.

REGLAS DE EVALUACIÓN OPERATIVA Y GESTIÓN DE RIESGO DEFINITIVA
1. Filtro de Ausencia de Patrón: Si no se cumplen las condiciones de giro del Escenario C o la Regla 5 en rango lateral, establece rigurosamente la clave 'a' como "No Abrir" y todos los niveles en 0.
2. Precio de Entrada: El campo 'pe' será estricta y exactamente el valor de la variable provista 'Entrada_M5_Close'. Queda prohibido alucinar un precio de entrada diferente.
3. Jerarquía Estricta de Objetivos Matemáticos para Órdenes Activas (Sin Igualdades):
- El campo 'ts' representa el 'Precio Umbral de Activación del Trailing' para tu bot.
- Si la acción 'a' es "Comprar" (Giro Alcista en Suelo): Se debe cumplir rigurosamente que: sl < pe < ts < tp. El umbral 'ts' queda ubicado por ENCIMA de la entrada y el 'tp' es el más alto.
- Si la acción 'a' es "Vender" (Giro Bajista en Techo): Se debe cumplir rigurosamente que: sl > pe > ts > tp. El umbral 'ts' queda ubicado por DEBAJO de la entrada y el 'tp' es el más bajo.
- Si se opera en Rango Lateral (Regla 5): Se aplican las mismas jerarquías de niveles. El parámetro 'ts' calcula su activación a una distancia corta de 0.3x VP_Calculado_Local a favor de la operación (Compras: ts = pe + 0.3xVP | Ventas: ts = pe - 0.3xVP).

4. COLOCACIÓN DE NIVELES CON COBRO EQUILIBRADO SEGÚN ZONA (Escenario C):
- SI TU ZONA_ACTUAL ES "SUELO" (Gatillo de Compra / Long):
  * sl en Compra (Protección Estricta M5): Escanea la matriz M5 hacia atrás. Localiza el Mínimo Absoluto exacto (punta de la mecha de capitulación) de las últimas 10 velas. Coloca el sl obligatoriamente POR DEBAJO de ese mínimo a una distancia exacta de: sl = Mínimo_10v - (0.2 * VP_Calculado_Local).
  * tp en Compra (Salida Moderada): Queda estrictamente PROHIBIDO usar 'Indicador_BolMid' como base. Calcula el objetivo sumando un recorrido de volatilidad fijo al precio de entrada (pe):
    - CASO CRÍTICO / INERCIA EXTREMA: SI [Tamaño_Cuerpo0 >= (2.0 * VP_Calculado_Local)] O SI [Resta_Climax_Suelo0 > (1.5 * VP_Calculado_Local)], establece de forma exacta: tp = pe + (0.8 * VP_Calculado_Local).
    - CASO ESTÁNDAR / MODERADO: SI el movimiento es normal y saludable, establece de forma exacta: tp = pe + (1.2 * VP_Calculado_Local).

- SI TU ZONA_ACTUAL ES "TECHO" (Gatillo de Venta / Short):
  * sl en Venta (Protección Estricta M5): Escanea la matriz M5 hacia atrás. Localiza el Máximo Absoluto exacto (punta de la mecha de euforia) de las últimas 10 velas. Coloca el sl obligatoriamente POR ENCIMA de ese máximo a una distancia exacta de: sl = Máximo_10v + (0.2 * VP_Calculado_Local).
  * tp en Venta (Salida Moderada): Queda estrictamente PROHIBIDO usar 'Indicador_BolMid' como base. Calcula el objetivo restando un recorrido de volatilidad fijo al precio de entrada (pe):
    - CASO CRÍTICO / INERCIA EXTREMA: SI [Tamaño_Cuerpo0 >= (2.0 * VP_Calculado_Local)] O SI [Resta_Climax_Techo0 > (1.5 * VP_Calculado_Local)], establece de forma exacta: tp = pe - (0.8 * VP_Calculado_Local).
    - CASO ESTÁNDAR / MODERADO: SI el movimiento es normal y saludable, establece de forma exacta: tp = pe - (1.2 * VP_Calculado_Local).

- Parámetros Comunes de Activación Defensiva:
  * ts (Umbral de Activación del Trailing Stop): Se colocará a una distancia exacta de 0.4x VP_Calculado_Local a favor de la tendencia desde pe: Compras (ts = pe + 0.4xVP) | Ventas (ts = pe - 0.4xVP).
  * Validación RR: Si el Ratio Riesgo/Beneficio es < 1:1, cambia la acción 'a' a "No Abrir" de forma inmediata y formatea niveles en 0. Las órdenes son estáticas y estables; prohibido salidas anticipadas por tiempo.

5. Bloqueo de Alucinación y Validación de Coherencia Cruzada: Los valores finales de las claves independientes del JSON ('tp', 'sl', 'ts', 'pe') deben coincidir exactamente con los resultados numéricos de las operaciones aritméticas resueltas en el campo 'p'. Si la matemática viola las desigualdades estrictas de la jerarquía del punto 3, o si existe una diferencia mayor a 0.01, el sistema activará un bloqueo de emergencia inmediato: cambia la acción 'a' a "No Abrir" y establece los niveles en 0 de forma fulminante.

OBLIGATORIEDAD DE CADENA DE PENSAMIENTO MATEMÁTICA EN 'p':
Rellena la clave 'p' en una sola línea continua adaptando dinámicamente el formato según tu 'Zona_Actual' provista por el servidor local:

- SI ZONA_ACTUAL ES "SUELO":
"p": "ZONA=Suelo | CALCULOS: VP={valor_VP} | Resta_Suelo0={diferencia_bol_inf_low} | Resta_Val_Suelo={diferencia_mecha_inf_cuerpo} | Filtro_M5=[Estado] | Tipo=[Estado] | FORMULA_NIVELES: pe=[valor] | sl_calculado=[operacion]=sl_final | ts_calculado=[operacion]=ts_final | tp_calculado=[operacion]=tp_final | EXPLICACION_HUMANA=Redacta aquí una explicación corta basándote estrictamente en los valores de las variables numéricas provistas por el servidor."

- SI ZONA_ACTUAL ES "TECHO":
"p": "ZONA=Techo | CALCULOS: VP={valor_VP} | Resta_Techo0={diferencia_bol_sup_high} | Resta_Val_Techo={diferencia_mecha_sup_cuerpo} | Filtro_M5=[Estado] | Tipo=[Estado] | FORMULA_NIVELES: pe=[valor] | sl_calculado=[operacion]=sl_final | ts_calculado=[operacion]=ts_final | tp_calculado=[operacion]=tp_final | EXPLICACION_HUMANA=Redacta aquí una explicación corta basándote estrictamente en los valores de las variables numéricas provistas por el servidor."

"""

INPUTS = [
    "velas_M5",
    "velas_H1",
    "b_superior",
    "b_media",
    "b_inferior",
    "close_M5",
    "valor_VP",
    "diferencia_bol_inf_low",
    "diferencia_bol_sup_high",
    "diferencia_mecha_inf_cuerpo",
    "diferencia_mecha_sup_cuerpo"
]

# p: Proceso matemático interno
# a: Acción
# pe: Precio de entrada
# tp: Take profit
# sl: Stop loss
# ts: Trailing stop
# v: Velas de espera
from typing import Literal
from pydantic import BaseModel, Field

class Esquema(BaseModel):
    p: str = Field(..., description="VP=X|RCL=Y|BCA=Z|Filtro=Estado|Tipo=Ruptura_Momentum/Rango_Lateral/Tendencial_Reversion")
    a: Literal["Comprar", "Vender", "No Abrir"] = Field(
        ..., 
        description="La acción operativa recomendada basada exclusivamente en las reglas algebraicas analizadas."
    )
    pe: float = Field(..., description="Precio de entrada al mercado (corresponde estrictamente al Close de la Vela 0).")
    tp: float = Field(..., description="Precio objetivo Take Profit (0 si la acción sugerida es 'No Abrir').")
    sl: float = Field(..., description="Precio límite Stop Loss (0 si la acción sugerida es 'No Abrir').")
    ts: float = Field(..., description="Precio de activación del Trailing Stop (0 si no aplica o la acción es 'No Abrir').")
    v: int = Field(
        ..., 
        ge=1, 
        le=4, 
        description="Número entero de velas (1 a 4) que el bot local debe esperar antes de lanzar la auditoría."
    )


def obtener_datos_filtro(inputs):
    velas_H1 = formatear_velas_para_ia(inputs["velas_H1"], None)
    velas_M5 = formatear_velas_para_ia(inputs["velas_M5"], inputs["indicador"])    

    datos_ultima_vela = calcular_metricas_vela_actual(inputs["velas_M5"][-1], parametros.valor_bollinger_inferior, parametros.valor_bollinger_media, parametros.valor_bollinger_inferior)

    datos = {
        "velas_M5": velas_M5,
        "velas_H1": velas_H1,
        "b_superior": parametros.valor_bollinger_superior,
        "b_media": parametros.valor_bollinger_media,
        "b_inferior": parametros.valor_bollinger_inferior,
        "close_M5": datos_ultima_vela["close_M5"],
        "valor_VP": calcular_valor_vp(inputs["velas_M5"]),
        "diferencia_bol_inf_low": datos_ultima_vela["diferencia_bol_inf_low"],
        "diferencia_bol_sup_high": datos_ultima_vela["diferencia_bol_sup_high"],
        "diferencia_mecha_inf_cuerpo": datos_ultima_vela["diferencia_mecha_inf_cuerpo"],
        "diferencia_mecha_sup_cuerpo": datos_ultima_vela["diferencia_mecha_sup_cuerpo"]
    }

    return {
        k: datos[k]
        for k in INPUTS 
        if k in datos
    }