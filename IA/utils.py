from typing import Dict, Any, Optional
import configuracion.parametros as parametros

def formatear_velas_para_ia(datos, indicador):
    # Crear el encabezado para guiar la lectura del modelo
    if indicador is not None and indicador == "Bollinger":
        lineas = ["Vela,Open,High,Low,Close"]
        #Bollinger no requiere agregar columnas. Dejo esta parte como ejemplo para futuros indicadores que si lo requieran.
        #lineas = ["Vela,Open,High,Low,Close,BolLow,BolMid,BolUp"]
    else:
        lineas = ["Vela,Open,High,Low,Close"]
    
    # Obtener el total de velas en el arreglo
    total_velas = len(datos)
    
    for i in range(total_velas):
        # Calculamos el índice inverso para que la IA sepa el orden cronológico.
        # La vela más antigua será la Vela -59 y la que acaba de cerrar será la Vela 0.
        indice_ia = -(total_velas - 1 - i)
        
        open_p  = round(float(datos[i]['Open']), 2)
        high_p  = round(float(datos[i]['High']), 2)
        low_p   = round(float(datos[i]['Low']), 2)
        close_p = round(float(datos[i]['Close']), 2)

        if indicador is not None and indicador == "Bollinger":
            low_bol   = round(float(datos[i]['Lower']), 2)
            mid_bol   = round(float(datos[i]['Middle']), 2)
            up_bol   = round(float(datos[i]['Upper']), 2)

            lineas.append(f"{indice_ia},{open_p},{high_p},{low_p},{close_p}")
            
            # Vela actual (osea... la anterior a la que se está formando)
            if indice_ia == 0:
                parametros.valor_bollinger_superior = up_bol
                parametros.valor_bollinger_media = mid_bol
                parametros.valor_bollinger_inferior = low_bol
        else:        
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
        "apertura": datos_estrategia["apertura"],
        "reevaluacion": datos_estrategia["reevaluacion"],
        "indicadores": datos_estrategia["indicadores"],
        "indicador": datos_estrategia["indicador"],
        "version_apertura": datos_estrategia["version_apertura"],
        "version_apertura_cache": datos_estrategia["version_apertura_cache"],
        "version_reevaluacion": datos_estrategia["version_reevaluacion"],
        "version_reevaluacion_cache": datos_estrategia["version_reevaluacion_cache"]
    }

def obtener_modelo_ia_activo(configuracion: dict) -> Optional[tuple[str, str, bool]]:
    # 1. Buscar la IA que tenga "activo": True
    for nombre_ia, datos_ia in configuracion.items():
        if datos_ia.get("activo"):
            # 2. Buscar el modelo que tenga "activo": True dentro de esa IA
            for item_modelo in datos_ia.get("modelos", []):
                if item_modelo.get("activo"):
                    return  nombre_ia, \
                            item_modelo["modelo"], \
                            datos_ia.get("cache", False)
    return None