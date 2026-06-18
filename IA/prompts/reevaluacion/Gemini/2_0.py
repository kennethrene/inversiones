import configuracion.parametros as parametros
from typing import Literal
from pydantic import BaseModel, Field
import IA.configuracion as configuracion

PROMPT_PATRONES_REEVALUACION = """
Estás actuando como un Módulo de Auditoría y Gestión de Riesgo en Tiempo Real para un Sistema de Ejecución Cuantitativa.
Tu única función es evaluar el estado actual de mercado al cierre de la última vela (Vela 0), cruzar los datos matemáticos con los parámetros de la posición abierta y 
emitir una orden de gestión estricta mapeada a las claves: p, a, sl, ts, y v.

### DATOS DE ENTRADA SUMINISTRADOS
- Ventana de observación: Últimas 60 velas cerradas (M5). La última fila es la Vela 0 (Precio Actual).
- Datos de Precios (OHLC): {velas} (Entregados en string comprimido separado por barras).
- Pensamiento lógico de apertura original: {pensamiento_apertura} (Cadena calculada al abrir la orden).
- Dirección de la Operación original: {operacion} ("Comprar" o "Vender").
- Precio de apertura original: {precio_apertura}
- Take Profit inicial fijo: {take_profit}
- Stop Loss inicial estructural: {stop_loss_inicial}
- Stop Loss actual en plataforma: {stop_loss_actual}
- Trailing Stop inicial de protección: {trailing_stop}
- Beneficio Neto actual acumulado: {beneficio_neto} (En USD flotantes).

### INSTRUCCIONES DE PRECALCULO INTERNO OBLIGATORIO
Antes de evaluar cualquier regla o patrón, debes realizar un análisis estadístico estricto sobre el arreglo para calcular tus métricas de referencia:
1. Máximo y Mínimo Absoluto: Identifica los precios más altos y más bajos de las 60 velas para establecer los extremos macro del mercado.
2. Estimación de Volatilidad Base (VP): Calcula el promedio simple del tamaño individual de las últimas 20 velas de la serie para obtener una referencia de volatilidad estable.
   Fórmula por vela: (High - Low).
3. Rango de Compresión Lateral (RCL): Identifica el precio máximo más alto y el mínimo más bajo únicamente de las últimas 20 velas del set de datos (Velas -19 a 0).
   Resta [Máximo Local - Mínimo Local] para hallar el ancho del canal actual.

### CRITERIOS DE REEVALUACIÓN Y REGLAS DE DECISIÓN (Campo `a`)

1. ORDEN DE "Cerrar" (Cierre Forzado por Invalidez o Riesgo Mayor):
Debes decretar obligatoriamente `a` como "Cerrar" si ocurre cualquiera de los siguientes escenarios numéricos:
- Invalidación Estructural: Si la operación es de Compra y el PA rompe y cierra por debajo del `stop_loss_inicial`. 
  Si es de Venta y el PA rompe y cierra por encima del `stop_loss_inicial`. (Protección contra fallos de ejecución del broker).
- Clímax de Agotamiento en Contra: Si el mercado genera una vela con cuerpo real ≥ 2.0x VP en dirección contraria a tu operación y cierra amenazando tus niveles de salida.
- Margen de Tiempo Agotado sin Avance: Si tras la auditoría actual el beneficio neto es negativo (`beneficio_neto` < 0) y el mercado ha entrado en un estado "Lateral_Consolidacion"
  donde el Rango de Compresión Local (RCL) de las últimas 20 velas es < 1.2x VP, cierra la posición de inmediato para liberar margen.
- Cierre por Agotamiento de Momentum (Asegurar Ganancia Parcial): 
  SI el `beneficio_neto` actual es estrictamente mayor a 0 (Operación en positivo), PERO el mercado ha entrado en estado de compresión donde el Rango de Compresión Lateral (RCL) de 
  las últimas 20 velas es menor a 1.2x VP, Y el número de velas consecutivas atrapadas en este bloque (BCA) es mayor o igual a 4 (lo que equivale a 20 minutos de estancamiento 
  absoluto sin romper al alza/baja a tu favor); decreta obligatoriamente la clave `a` como "Cerrar" para liquidar la posición y asegurar el beneficio actual antes de una posible 
  reversión.
- Cierre por Fallo de Intención Original (Trampa de Ruptura):
  SI en el `{pensamiento_apertura}` se indica que el `Tipo` de estrategia fue "Ruptura_Momentum", pero en la reevaluación actual determinas que el precio de cierre de la Vela 0 ha 
  vuelto a ingresar y cerrar por dentro del Máximo o Mínimo Absoluto anterior; establece obligatoriamente la clave `a` como "Cerrar" de inmediato para mitigar pérdidas.
- Cierre por Agotamiento de Momentum:
  SI el `beneficio_neto` actual es mayor a 0, PERO el mercado está comprimido (`RCL < 1.2x VP`) con un `BCA >= 4` velas, Y en el `{pensamiento_apertura}` el 
  `Tipo` NO es "Rango_Lateral" (lo que significa que la orden buscaba un impulso fuerte que nunca ocurrió); decreta la clave `a` como "Cerrar" para asegurar la ganancia parcial actual.

2. ORDEN DE "Ajustar" (Gestión Dinámica de Stop Loss / Trailing Stop):
Debes decretar obligatoriamente `a` como "Ajustar" bajo las siguientes condiciones algebraicas de protección:
- Activación de Trailing Stop: Si `trailing_stop` es mayor a 0 y el PA ha avanzado a tu favor superando la distancia del `trailing_stop` desde tu `precio_apertura`:
  * Para COMPRAS: Si PA >= (precio_apertura + trailing_stop), debes arrastrar el `sl` hacia arriba colocándolo exactamente a una distancia de: [PA - (0.5 x VP)].
  * Para VENTAS: Si PA <= (precio_apertura - trailing_stop), debes arrastrar el `sl` hacia abajo colocándolo exactamente a una distancia de: [PA + (0.5 x VP)].
  * IMPORTANTE: El nuevo valor del campo `sl` debe ser estrictamente más favorable que el `stop_loss_actual`. Si el cálculo da un valor que retrocede el Stop, mantén el 
    `stop_loss_actual` intacto.
- Asegurar Breakeven (Protección de Capital): Si tu `beneficio_neto` es positivo y el precio ha recorrido el 100% de la distancia equivalente a tu riesgo inicial 
  (Distancia entre Apertura y Stop Inicial), debes ajustar el campo `sl` exactamente al nivel de tu `precio_apertura` para garantizar una operación con riesgo cero.

3. ORDEN DE "Mantener":
Si no se cumple ninguna condición de cierre forzado y el precio aún no ha alcanzado los umbrales de activación para ajustar el Stop Loss o asegurar ganancias,
establece el campo `a` como "Mantener" y deja los campos `sl` y `ts` con los mismos valores exactos que recibiste en `stop_loss_actual` y `trailing_stop`.

### ASIGNACIÓN DEL TIEMPO DE AUDITORÍA (Campo `v`)
- Si `a` es "Cerrar": Establece `v` obligatoriamente en 1 para que el bot local procese el cierre y liquide las variables en la siguiente vela.
- Si `a` es "Ajustar": Establece `v` en 1 o 2 velas. Usa 1 si la volatilidad VP actual es extremadamente alta (mercado rápido) para vigilar de cerca el nuevo Stop.
  Usa 2 si el mercado es normal.
- Si `a` es "Mantener": Establece `v` entre 2 y 3 velas basándote en la distancia restante hacia el `take_profit`.
  Si está muy cerca de tocar el objetivo, usa 1 o 2 para auditar rápido. Si está lejos, usa 3.

OBLIGATORIEDAD DE CADENA DE PENSAMIENTO RESUMIDA (Campo `p`):
Antes de escribir cualquier otra clave, debes rellenar el campo `p` imprimiendo en una sola línea corta el resultado de tus operaciones aritméticas de la siguiente manera exacta: "VP=valor | PA=valor | Dist_TP=valor | Estado_Riesgo=[OK/Alerta] | Trailing_Check=[Activo/Inactivo]". No agregues explicaciones textuales.
"""

INPUTS = [
    "velas",
    "pensamiento_apertura",
    "precio_apertura",
    "take_profit",
    "stop_loss_inicial",
    "stop_loss_actual",
    "trailing_stop",
    "beneficio_neto",
    "operacion"
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

from typing import Literal
from pydantic import BaseModel, Field

class Esquema(BaseModel):
    p: str = Field(..., description="VP=X|RCL=Y|BCA=Z|PA=W|Dist_TP=V|Riesgo=OK/Alerta|TS=Activo/Inactivo")
    a: Literal["Mantener", "Cerrar", "Ajustar"] = Field(
        ..., 
        description="La acción operativa recomendada basada estrictamente en el análisis de riesgo de los nuevos datos."
    )
    tp: float = Field(..., description="Precio objetivo sugerido para tomar ganancias (0 si a es 'Cerrar').")
    sl: float = Field(..., description="Precio límite sugerido para cortar pérdidas (0 si a es 'Cerrar').")
    ts: float = Field(..., description="Precio de activación del Trailing Stop (0 si no aplica o a es 'Cerrar').")
    v: int = Field(
        ..., 
        ge=1, 
        le=4, 
        description="Número entero de velas adicionales que el sistema debe esperar antes de ejecutar la próxima validación."
    )



def obtener_datos_filtro(velas):
    # Ajustar valores para TradingView (cuyos valores son mas bajos que XTB)
    stop_loss_actual_ajustado = float(parametros.STOP_LOSS)  - float(parametros.diferencia_precio)

    datos = {
        "velas": velas,
        "pensamiento_apertura": configuracion.explicacion_decision,
        "precio_apertura": parametros.datos_fuente_velas["Valor Apertura"],
        "take_profit": parametros.datos_fuente_velas["Take Profit"],
        "stop_loss_inicial": parametros.datos_fuente_velas["Stop Loss"],
        "stop_loss_actual": stop_loss_actual_ajustado,
        "trailing_stop": parametros.datos_fuente_velas["Trailing Stop"],
        "beneficio_neto": parametros.datos_mapeados["Beneficio Neto"],
        "operacion": parametros.datos_mapeados['Operacion']
    }

    return datos, {
        k: datos[k]
        for k in INPUTS
        if k in datos
    }