import configuracion.parametros as parametros
import traceback
import numpy as np
import pandas as pd
import mplfinance as mpf
from extraccion.velas import extraer_velas
from tvDatafeed import Interval


# ===========================================================================
# 📈 MOTOR GRAFICO - REAL TIME PARA MAC OS (NATIVO ASINCRONO)
# ===========================================================================
def loop_render_grafico(frame, fig, ax):
    """Refresca la GUI de manera segura interactuando directamente con Matplotlib"""
    try:
        datos_vela = parametros.datos_graficos["datos_velas"].copy()
        hora_vela = parametros.datos_graficos["hora_vela"]
        operacion = parametros.datos_graficos["operacion"]
        
        # Generar set de prueba inicial para que el gráfico no nazca vacío
        if datos_vela.empty:
            return
            
        ax.clear() # Limpieza de primitivas viejas para evitar superposición
        apf = []
        
        if hora_vela is not None and hora_vela in datos_vela.index:
            compra_lista = [np.nan] * len(datos_vela)
            venta_lista = [np.nan] * len(datos_vela)
            pos_idx = datos_vela.index.get_loc(hora_vela)
            
            if "COMPRA" in operacion:
                compra_lista[pos_idx] = datos_vela.loc[hora_vela, 'Low'] - 2.0
                apf.append(mpf.make_addplot(compra_lista, type='scatter', markersize=150, marker='^', color='green', ax=ax))
            elif "VENTA" in operacion:
                venta_lista[pos_idx] = datos_vela.loc[hora_vela, 'High'] + 2.0
                apf.append(mpf.make_addplot(venta_lista, type='scatter', markersize=150, marker='v', color='red', ax=ax))
                
        # Pasar el eje explícito a mplfinance para evitar congelamientos en Mac
        if apf:
            mpf.plot(datos_vela, type='candle', ax=ax, addplot=apf, style='charles', datetime_format='%H:%M')
        else:
            mpf.plot(datos_vela, type='candle', ax=ax, style='charles', datetime_format='%H:%M')
            
        fig.canvas.draw_idle() # Redibujo eficiente optimizado para backend TkAgg
    except Exception as e:
        parametros.error += traceback.format_exc() + "\n"
        pass

def extraer_datos_velas():
    parametros.lista_velas_acumuladas = extraer_velas(Interval.in_5_minute)
    parametros.historico_velas = pd.DataFrame(parametros.lista_velas_acumuladas)
    parametros.datos_graficos["datos_velas"] = parametros.historico_velas
    parametros.historico_velas.index = pd.date_range(start="2026-01-01 09:30", periods=len(parametros.historico_velas), freq=f"{parametros.TEMPORALIDAD_MINUTOS}min")
