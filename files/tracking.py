import csv
import os
import time
import config
import traceback

def guardar_estadistica(evento):
    """
    Guarda una fila de datos en un archivo CSV para seguimiento estadístico.
    """
    archivo = "estadisticas_bot.csv"
    
    # Definir los encabezados de las columnas
    encabezados = ["Fecha-Hora", "Evento", "Activo", "Lote", "Precio Compra", "Precio Venta", "EMA 35", "EMA 50", "RSI", "MACD", "Beneficio %", "Beneficio Neto", "Operación Ganada", "Log" , "Motivo Cierre"]
    
    # Obtener el tiempo exacto usando tu formato
    fecha_hora = time.strftime('%Y-%m-%d %H:%M:%S')
    
    # Verificar si el archivo ya existe para saber si escribimos el encabezado
    existe_archivo = os.path.exists(archivo)
    
    try:
        # Abrimos en modo 'a' (añadir contenido al final sin borrar lo anterior)
        with open(archivo, mode='a', newline='', encoding='utf-8') as f:
            escritor = csv.writer(f)
            
            # Si es un archivo nuevo, creamos la primera fila con los títulos
            if not existe_archivo:
                escritor.writerow(encabezados)
                
            # Escribimos los datos de la operación actual
            escritor.writerow([
                fecha_hora,           # [0] Fecha-Hora
                evento,               # [1] Evento
                config.activo_actual, # [2] Activo
                config.valor_lote,    # [3] Lote
                config.valor_compra,  # [4] Precio Compra
                config.valor_venta,   # [5] Precio Venta
                config.valor_ema_35,  # [6] EMA 35
                config.valor_ema_50,  # [7] EMA 50
                config.valor_rsi,     # [8] RSI
                config.valor_macd,    # [9] MACD
                "",                   # [10] Beneficio % (Vacio al abrir)
                "",                   # [11] Beneficio Neto (Vacio al abrir)
                "Pendiente",          # [12] Operación Ganada (Estado inicial)
                config.log_operacion, # [13] Log
                ""                    # [14] Motivo Cierre (Vacio al abrir)
            ])
            
        print(f"💾 [SISTEMA]: Datos guardados en estadísticas para {evento} en {config.activo_actual}.")
    except Exception as e:
        config.error = traceback.format_exc()

def actualizar_ultima_operacion(datos, ganada, motivo):
    """
    Lee el archivo estadístico, modifica la última fila para agregar 
    el resultado en dólares y el evento, y vuelve a guardar el archivo.
    """
    archivo = "estadisticas_bot.csv"
    
    if not os.path.exists(archivo):
        print("❌ ERROR: No existe el archivo de estadísticas para actualizar.")
        return

    try:
        # 1. Leer todas las filas existentes en memoria
        with open(archivo, mode='r', newline='', encoding='utf-8') as f:
            filas = list(csv.reader(f))
        
        if len(filas) < 2: # Solo está el encabezado o está vacío
            print("⚠️ ADVERTENCIA: No hay operaciones registradas para actualizar.")
            return
            
        # 2. Modificar la última fila (filas[-1])
        # Asumiendo que tu tabla original tiene 9 columnas, modificamos o añadimos datos al final
        # Si la fila tiene el tamaño estándar, le añadimos el resultado
        ultima_fila = filas[-1]
        
        ultima_fila[10] = datos['Beneficio %']
        ultima_fila[11] = datos['Beneficio Neto']
        ultima_fila[12] = ganada
        ultima_fila[14] = motivo
        
        # 3. Volver a escribir todo el archivo con la fila actualizada
        with open(archivo, mode='w', newline='', encoding='utf-8') as f:
            escritor = csv.writer(f)
            escritor.writerows(filas)
            
        print(f"💾 [ESTADÍSTICAS]: Última fila actualizada con éxito")
        
    except Exception as e:
        config.error = traceback.format_exc()
