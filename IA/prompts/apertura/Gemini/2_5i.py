from typing import Literal
from pydantic import BaseModel, Field
import configuracion.parametros as parametros
from extraccion.indicadores import calcular_valor_vp, calcular_metricas_vela_actual, determinar_tendencia_macd, determinar_tendencia
from IA.utils import formatear_velas_para_ia

PROMPT_HIBRIDO = """
Estás actuando como un Sistema Core de Ejecución Cuantitativa de Alta Precisión especializado en Price Action Puro, configurado como un Algoritmo Cuantitativo de Reversión Estructural y Continuación Tendencial asistido por Filtros de Momento MACD.
Tu función es procesar las variables exactas inyectadas por el servidor local para devolver una decisión operativa en formato JSON mapeando tus respuestas rígidamente a las claves raíz: p, a, tp, sl, ts y pe.

CONTEXTO Y ENTRADA DE DATOS MULTI-TIMEFRAME (HISTÓRICO)
- Temporalidad Macro: 1 hora por vela (H1). Ventana: Últimas 30 velas cerradas -> {velas_H1}
- Temporalidad Micro: Matriz de texto con las últimas 60 velas de 5 minutos (Vela, Open, High, Low, Close). La última fila es la Vela 0 -> {velas_M5}

VALORES ARITMÉTICOS EXACTOS DE LA VELA 0 (INYECTADOS POR EL SERVIDOR LOCAL):
* Entrada_M5_Close = {close_M5}
* Indicador_BolLow = {b_inferior}
* Indicador_BolMid = {b_media}
* Indicador_BolUp = {b_superior}
* VP_Calculado_Local = {valor_VP}
* Resta_Climax_Suelo0 = {diferencia_bol_inf_low}
* Resta_Climax_Techo0 = {diferencia_bol_sup_high}
* Resta_Validacion_Suelo = {diferencia_mecha_inf_cuerpo}
* Resta_Validacion_Techo = {diferencia_mecha_sup_cuerpo}

MÓDULO DE CONTROL DE CAJA NEGRA MACD (DICTADO POR EL SERVIDOR):
* Zona_Actual = "{zona_actual}" (Secciones: TECHO_EXTREMO / TECHO / SUELO / SUELO_EXTREMO)
* Filtro_MACD = "{filtro_macd}" (Cruce_Alcista_Confirmado / Cruce_Bajista_Confirmado / Sin_Cruce_Inercia_Actual)
* Impulso_Histograma = "{impulso_histograma}" (Aceleracion_Alcista / Aceleracion_Bajista)
* Posicion_Cero = "{posicion_cero}" (Zona_Compradora_Alta / Zona_Vendedora_Baja)
* Fuerza_Tendencia = "{fuerza_tendencia}" (Fuerte_Abriéndose / Debil_Compresión)
* MACD_Seguridad = "{macd_seguridad}" (Permitido / Bloqueado_Fuerza_Alcista_Extrema / Bloqueo_Fuerza_Bajista_Extrema)
* MACD_Valor = {macd_valor}
* Hist_Valor = {hist_valor}
* Tendencia_H1_Servidor = "{tendencia_macro_local}" (Alcista_Estructural / Bajista_Estructural / Neutral_Rango)

INSTRUCCIÓN DE RESTRICCIÓN DE ATENCIÓN ABSOLUTA:
- El valor de 'Zona_Actual' y 'MACD_Seguridad' son mandatos informáticos indiscutibles. Tienes estrictamente PROHIBIDO reevaluarlos o contradecirlos.
- SI 'MACD_Seguridad' es diferente de "Permitido": Se activa un Cortocircuito Fulminante. Debes abortar la evaluación de inmediato. Establece la acción 'a' in "No Abrir" y todos los niveles en 0.
- SI 'Zona_Actual' contiene la palabra "TECHO": Tienes estrictamente PROHIBIDO evaluar escenarios de compra o rellenar variables de suelo. Tu única atención es la zona alta (Ventas o Rebotes).
- SI 'Zona_Actual' contiene la palabra "SUELO": Tienes estrictamente PROHIBIDO evaluar escenarios de venta o rellenar variables de techo. Tu única atención es la zona baja (Compras o Rebotes).

INSTRUCCIONES DE PRECALCULO HISTÓRICO EN M5:
Utiliza la matriz micro M5 únicamente para extraer estas dos métricas de canal:
- Rango de Compresión Lateral (RCL): Ancho del canal [Máximo Local - Mínimo Local] obtenido de las últimas 20 velas de M5.
- Tamaño_Cuerpo0: Distancia absoluta real entre el Open y Close de la fila 0 de M5. Usando la fila 0 ejecuta: Tamaño_Cuerpo0 = Valor_Absoluto(Open - Close).
- Entrada_M5_Low = [Valor de la columna Low en la fila 0]
- Entrada_M5_High = [Valor de la columna High en la fila 0]

FILTRO DE DIRECCIÓN MACRO (H1)
- Para establecer la inercia mayor del mercado, asume de forma obligatoria e imperativa el valor inyectado en la cabecera: Filtro_Macro_H1 = Tendencia_H1_Servidor.

FILTRO DE EXCLUSIÓN CRÍTICO EN M5: EVALUACIÓN DE ESCENARIOS
- ESCENARIO A (Mercado Comprimido): Si RCL < 1.2 x VP_Calculado_Local, Filtro M5 = "Lateral_Consolidacion" y Tipo = "Rango_Lateral".
- ESCENARIO B (Frenado en Seco): Si RCL >= 1.2 x VP_Calculado_Local pero el promedio (High - Low) de las últimas 3 velas es < 0.6 x VP_Calculado_Local, Filtro M5 = "Lateral_Consolidacion" y Tipo = "Rango_Lateral".

- ESCENARIO C (EXCEPCIÓN CRÍTICA DE REVERSIÓN EN EXTREMOS DE LAS BANDAS):
  Este escenario solo se evalúa si MACD_Seguridad es estrictamente "Permitido" y el precio está en un extremo geográfico:
  
  * SI 'Zona_Actual' ES "SUELO_EXTREMO":
    - Condición de Clímax Bajista: Es VERDADERA si la variable del servidor 'Resta_Climax_Suelo0' es > 0.
    - Gatillo de COMPRA: SI Clímax Bajista es VERDADERA Y la variable del servidor 'Resta_Validacion_Suelo' es >= 0; la orden de COMPRA se ejecuta de forma automática, obligatoria e imperativa. Establece rígidamente: Filtro M5 = "Tendencial_Reversion", Tipo = "Giro_Bollinger_Suelo" y la acción 'a' como "Comprar". Queda prohibido anularla.

  * SI 'Zona_Actual' ES "TECHO_EXTREMO":
    - Condición de Clímax Alcista: Es VERDADERA si la variable del servidor 'Resta_Climax_Techo0' es > 0.
    - Gatillo de VENTA: SI Clímax Alcista es VERDADERA Y la variable del servidor 'Resta_Validacion_Techo' es >= 0; la orden de VENTA se ejecuta de forma automática, obligatoria e imperativa. Establece rígidamente: Filtro M5 = "Tendencial_Reversion", Tipo = "Giro_Bollinger_Techo" y la acción 'a' como "Vender". Queda prohibido anularla.

  * Bloqueo de Continuación en Extremos: Si la variable de validación de la zona activa ('Resta_Validacion_Suelo' o 'Resta_Validacion_Techo') es estrictamente negativa (< 0), la excepción queda RECHAZADA. Establece obligatoriamente la acción 'a' en "No Abrir" y los niveles en 0.

- ESCENARIO E (REBOTE DE CONTINUACIÓN TENDENCIAL EN BANDA MEDIA):
  Este escenario se activa si MACD_Seguridad es "Permitido" y el precio está testeando el centro del canal bajo inercia macro:
  * Resta_Val_Media_Suelo = Resta_Validacion_Suelo + (Tamaño_Cuerpo0 * 0.5)
  * Resta_Val_Media_Techo = Resta_Validacion_Techo + (Tamaño_Cuerpo0 * 0.5)

  * SI Filtro_Macro_H1 ES "ALCISTA_ESTRUCTURAL" Y 'Zona_Actual' ES "TECHO":
    - Condición de Toque Central Alcista: VERDADERA si [Entrada_M5_Low <= Indicador_BolMid] Y [Entrada_M5_Close > Indicador_BolMid].
    - Ejecución por Rebote Alcista: SI Toque Central Alcista es VERDADERA Y la variable calculada [Resta_Val_Media_Suelo >= 0]; ejecuta obligatoriamente la COMPRA tendencial. Establece rígidamente: Filtro M5 = "Tendencial_Continuacion", Tipo = "Rebote_Media_Suelo" y acción 'a' = "Comprar".
  
  * SI Filtro_Macro_H1 ES "BAJISTA_ESTRUCTURAL" Y 'Zona_Actual' ES "SUELO":
    - Condición de Toque Central Bajista: VERDADERA si [Entrada_M5_High >= Indicador_BolMid] Y [Entrada_M5_Close < Indicador_BolMid].
    - Ejecución por Rebote Bajista: SI Toque Central Bajista es VERDADERA Y la variable calculada [Resta_Val_Media_Techo >= 0]; ejecuta obligatoriamente la VENTA tendencial. Establece rígidamente: Filtro M5 = "Tendencial_Continuacion", Tipo = "Rebote_Media_Techo" y acción 'a' = "Vender".
  
  * Bloqueo de Continuación Central: Si la variable de la tendencia activa ('Resta_Val_Media_Suelo' o 'Resta_Val_Media_Techo') es estrictamente negativa (< 0), el rebote es falso (vela sólida sin mecha de apoyo). Establece rígidamente la acción 'a' en "No Abrir" y todos los niveles en 0 de forma fulminante.

- ESCENARIO D (Mercado Tendencial Ordinario): Si el precio cotiza dentro de las bandas y no se activa el Escenario C ni el E, Filtro M5 = "Tendencial", Tipo = "Tendencial_Reversion" y acción 'a' = "No Abrir" con niveles en 0.

REGLAS DE EVALUACIÓN OPERATIVA Y GESTIÓN DE RIESGO DEFINITIVA
1. Filtro de Ausencia de Patrón: Si no se cumplen las condiciones del Escenario C, Escenario E o la Regla 5 en rango lateral, establece rigurosamente la clave 'a' como "No Abrir" y todos los niveles en 0.
2. Precio de Entrada: El campo 'pe' será estricta y exactamente el valor de la variable provista 'Entrada_M5_Close'.
3. Jerarquía Estricta de Objetivos Matemáticos para Órdenes Activas (Sin Igualdades):
- El campo 'ts' representa el 'Precio Umbral de Activación del Trailing' para tu bot local.
- Si la acción 'a' es "Comprar": Se debe cumplir rigurosamente que: sl < pe < ts < tp.
- Si la acción 'a' es "Vender": Se debe cumplir rigurosamente que: sl > pe > ts > tp.
- Si opera en Rango Lateral (Regla 5): El parámetro 'ts' calcula su activación a una distancia corta de 0.3x VP_Calculado_Local a favor de la operación (Compras: ts = pe + 0.3xVP | Ventas: ts = pe - 0.3xVP).

4. CONDICIÓN COMPUESTA DE COHERENCIA CRUZADA INFRANQUEABLE (CANDADO DE JSON BINARIO):
- Antes de escribir las claves externas de la raíz del JSON, debes realizar un escaneo de coincidencia de strings.
- Queda estrictamente PROHIBIDO que el valor de la clave externa 'tp' difiera del valor resuelto como 'tp_final' en tu campo 'p'.
- Queda estrictamente PROHIBIDO que el valor de la clave externa 'sl' difiera del valor resuelto como 'sl_final' en tu campo 'p'.
- Queda estrictamente PROHIBIDO que el valor de la clave externa 'ts' difiera del valor resuelto como 'ts_final' en tu campo 'p'.
- [CORTOCIRCUITO ARBITRARIO]: Si los números del JSON raíz exterior no coinciden al centavo con las operaciones matemáticas resueltas al final de 'p', o si se violan las jerarquías de orden del punto 3, activa el bloqueo de emergencia de forma automática: cambia la acción 'a' a "No Abrir" y establece las claves externas 'tp', 'sl', 'ts' y 'pe' en 0 de forma fulminante.

5. COLOCACIÓN DE NIVELES CON ADAPTACIÓN MULTI-TIMEFRAME (Gatillos Activos):
- SI EL TIPO DE OPERACIÓN ES "GIRO_BOLLINGER_SUELO" (Compra / Long en extremo):
  * sl_final = Localiza el Mínimo Absoluto de las últimas 10 velas de M5. Si Filtro_Macro_H1 es "Alcista_Estructural", sl_final = Mínimo_10v - (0.2 * VP_Calculado_Local). Si es Bajista o Neutral, sl_final = Mínimo_10v - (0.15 * VP_Calculado_Local).
  * tp_final: Queda estrictamente PROHIBIDO usar 'Indicador_BolMid' como base.
    - Si Filtro_Macro_H1 es "Bajista_Estructural" (En contra), reduce el tp a escape rápido: tp_final = pe + (0.7 * VP_Calculado_Local).
    - Si [Tamaño_Cuerpo0 >= (2.0 * VP_Calculado_Local)] O [Resta_Climax_Suelo0 > (1.5 * VP_Calculado_Local)], tp_final = pe + (0.8 * VP_Calculado_Local).
    - Si Filtro_Macro_H1 es "Alcista_Estructural" o Neutral (A favor), establece la expansión justa de: tp_final = pe + (1.2 * VP_Calculado_Local).
  * ts_final = pe + (0.4 * VP_Calculado_Local).

- SI EL TIPO DE OPERACIÓN ES "GIRO_BOLLINGER_TECHO" (Venta / Short en extremo):
  * sl_final = Localiza el Máximo Absoluto de las últimas 10 velas de M5. Si Filtro_Macro_H1 es "Bajista_Estructural", sl_final = Máximo_10v + (0.2 * VP_Calculado_Local). Si es Alcista o Neutral, sl_final = Máximo_10v + (0.15 * VP_Calculado_Local).
  * tp_final: Queda estrictamente PROHIBIDO usar 'Indicador_BolMid' as base.
    - Si Filtro_Macro_H1 es "Alcista_Estructural" (En contra), reduce el tp a escape rápido: tp_final = pe - (0.7 * VP_Calculado_Local).
    - Si [Tamaño_Cuerpo0 >= (2.0 * VP_Calculado_Local)] O [Resta_Climax_Techo0 > (1.5 * VP_Calculado_Local)], tp_final = pe - (0.8 * VP_Calculado_Local).
    - Si Filtro_Macro_H1 es "Bajista_Estructural" o Neutral (A favor), establece la expansión justa de: tp_final = pe - (1.2 * VP_Calculado_Local).
  * ts_final = pe - (0.4 * VP_Calculado_Local).

- SI EL TIPO DE OPERACIÓN ES "REBOTE_MEDIA_SUELO" (Compra tendencial en la media móvil central):
  * sl_final = Entrada_M5_Low - (0.15 * VP_Calculado_Local). (Stop ceñido abajo de la vela de testeo).
  * tp_final = pe + (1.5 * VP_Calculado_Local). (Expansión agresiva a favor del impulso mayor).
  * ts_final = pe + (0.3 * VP_Calculado_Local).

- SI EL TIPO DE OPERACIÓN ES "REBOTE_MEDIA_TECHO" (Venta tendencial en la media móvil central):
  * sl_final = Entrada_M5_High + (0.15 * VP_Calculado_Local).
  * tp_final = pe - (1.5 * VP_Calculado_Local). (Expansión agresiva a favor del impulso mayor).
  * ts_final = pe - (0.3 * VP_Calculado_Local).

OOBLIGATORIEDAD DE CADENA DE PENSAMIENTO MATEMÁTICA EN 'p':
Rellena la clave 'p' en una sola línea continua adaptando dinámicamente el formato según tu 'Zona_Actual' provista por el servidor local para mantener un log con trazabilidad absoluta del sistema híbrido:

- SI ZONA_ACTUAL CONTIENE LA PALABRA "SUELO":
"p": "ZONA={zona_actual} | CALCULOS: Tendencia_H1={tendencia_macro_local} | Close_M5={close_M5} | BolUp={b_superior} | BolMid={b_media} | BolLow={b_inferior} | VP={valor_VP} | MACD={macd_valor} | Hist={hist_valor} | Filtro_MACD={filtro_macd} | Impulso_Hist={impulso_histograma} | Posicion_Cero={posicion_cero} | Fuerza_Tend={fuerza_tendencia} | MACD_Seguridad={macd_seguridad} | Resta_Suelo0={diferencia_bol_inf_low} | Resta_Val_Suelo={diferencia_mecha_inf_cuerpo} | Filtro_M5=[Estado] | Tipo=[Estado] | FORMULA_NIVELES: pe=[valor] | sl_calculado=[operacion]=sl_final | ts_calculado=[operacion]=ts_final | tp_calculado=[operacion]=tp_final | EXPLICACION=Redacta una explicación muy corta basándote estrictamente en los valores MACD y Bollinger del servidor."

- SI ZONA_ACTUAL CONTIENE LA PALABRA "TECHO":
"p": "ZONA={zona_actual} | CALCULOS: Tendencia_H1={tendencia_macro_local} | Close_M5={close_M5} | BolUp={b_superior} | BolMid={b_media} | BolLow={b_inferior} | VP={valor_VP} | MACD={macd_valor} | Hist={hist_valor} | Filtro_MACD={filtro_macd} | Impulso_Hist={impulso_histograma} | Posicion_Cero={posicion_cero} | Fuerza_Tend={fuerza_tendencia} | MACD_Seguridad={macd_seguridad} | Resta_Techo0={diferencia_bol_sup_high} | Resta_Val_Techo={diferencia_mecha_sup_cuerpo} | Filtro_M5=[Estado] | Tipo=[Estado] | FORMULA_NIVELES: pe=[valor] | sl_calculado=[operacion]=sl_final | ts_calculado=[operacion]=ts_final | tp_calculado=[operacion]=tp_final | EXPLICACION=Redacta una explicación muy corta basándote estrictamente en los valores MACD y Bollinger del servidor."

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
    "diferencia_mecha_sup_cuerpo",
    "zona_actual",
    "diferencia_media_low",
    "diferencia_media_high",
    "tendencia_macro_local",
    "filtro_macd",
    "impulso_histograma",
    "posicion_cero",
    "fuerza_tendencia",
    "macd_seguridad",
    "macd_valor",
    "hist_valor"
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

    datos_ultima_vela = calcular_metricas_vela_actual(inputs["velas_M5"][-1], parametros.valor_bollinger_inferior, parametros.valor_bollinger_media, parametros.valor_bollinger_superior)
    macd_datos = determinar_tendencia_macd(inputs["velas_M5"])

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
        "diferencia_mecha_sup_cuerpo": datos_ultima_vela["diferencia_mecha_sup_cuerpo"],
        "zona_actual": datos_ultima_vela["zona_actual"],
        "diferencia_media_low": datos_ultima_vela["diferencia_media_low"],
        "diferencia_media_high": datos_ultima_vela["diferencia_media_high"],
        "tendencia_macro_local": determinar_tendencia(inputs["velas_H1"]),
        "filtro_macd": macd_datos["filtro_macd"],
        "impulso_histograma": macd_datos["impulso_histograma"],
        "posicion_cero": macd_datos["posicion_cero"],
        "fuerza_tendencia": macd_datos["fuerza_tendencia"],
        "macd_seguridad": macd_datos["macd_seguridad"],
        "macd_valor": macd_datos["macd_valor"],
        "hist_valor": macd_datos["hist_valor"]
    }

    return {
        k: datos[k]
        for k in INPUTS
        if k in datos
    }