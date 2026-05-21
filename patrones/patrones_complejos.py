import pandas as pd
import config
import patrones.identificar_patrones as identificar_patrones

# ESTRUCTURAS COMPLEJAS Y ESCÁNER COMBINATORIO (50 y 60 VELAS)
def analizar_patrones():
    nombre_patron = "Ninguno"
    tendencia_alcista = False
    tendencia_bajista = False

    if len(identificar_patrones.num_velas_disponibles) >= 50:
        maximos = identificar_patrones.num_velas_disponibles['High'].tail(len(identificar_patrones.num_velas_disponibles)).astype(float).tolist()
        minimos = identificar_patrones.num_velas_disponibles['Low'].tail(len(identificar_patrones.num_velas_disponibles)).astype(float).tolist()

        # Extractor de picos (Guardando el ÍNDICE 'i' para poder buscar el valle)
        for i in range(1, len(maximos) - 1):
            if maximos[i] >= maximos[i-1] and maximos[i] >= maximos[i+1] and len(maximos) < 60:
                identificar_patrones.picos_indices.append(i)  # Guardamos la posición de la vela del pico
            elif len(maximos) >= 60:
                # Permitimos >= para tolerar "mesetas" o dobles techos milimétricos en velas contiguas
                if maximos[i] >= maximos[i-1] and maximos[i] >= maximos[i+1]:
                    if maximos[i] > maximos[i-1] or maximos[i] > maximos[i+1]:
                        # Evitamos duplicar si el pico anterior registrado ya tenía este mismo valor
                        if not identificar_patrones.picos_indices or maximos[i] != maximos[identificar_patrones.picos_indices[-1]]:
                            identificar_patrones.picos_indices.append(i)    

        # Buscamos mínimos locales donde la vela actual sea menor que la anterior y la siguiente
        for i in range(1, len(minimos) - 1):
            if minimos[i] <= minimos[i-1] and minimos[i] <= minimos[i+1] and len(maximos) < 60:
                identificar_patrones.suelos_indices.append(i)  # Guardamos la posición/índice del suelo
            elif len(maximos) >= 60:
                # Permitimos el operador igual para tolerar que el precio toque el suelo en velas contiguas
                if minimos[i] <= minimos[i-1] and minimos[i] <= minimos[i+1]:                    
                    # FILTRO DE REBOTE: Exigimos que realmente el precio venga cayendo o suba después (evita líneas rectas)
                    if minimos[i] < minimos[i-1] or minimos[i] < minimos[i+1]:                        
                        # 3. FILTRO DE DUPLICADOS: Si ya hay suelos guardados, verificamos que este nuevo suelo
                        # no tenga el mismo precio que el anterior en la lista (evita duplicar la misma zona/meseta)
                        if not identificar_patrones.suelos_indices or minimos[i] != minimos[identificar_patrones.suelos_indices[-1]]:
                            identificar_patrones.suelos_indices.append(i)

    if len(identificar_patrones.num_velas_disponibles) >= 60:
        # El Hombro-Cabeza-Hombro requiere al menos 3 picos para ser evaluado
        # Debe ser tendencia bajista previa y el MACD debe mostrar debilidad alcista
        if not identificar_patrones.es_tendencia_bajista and identificar_patrones.macd_debil_alcista and len(identificar_patrones.picos_indices) >= 3:            
            # Tomamos los últimos 3 picos detectados en el gráfico
            pos_pico_hombro_izq = identificar_patrones.picos_indices[-3]
            pos_pico_cabeza = identificar_patrones.picos_indices[-2]
            pos_pico_hombro_der = identificar_patrones.picos_indices[-1]  # El pico más reciente en tiempo real
            
            pico_hombro_izq = maximos[pos_pico_hombro_izq]
            pico_cabeza = maximos[pos_pico_cabeza]
            pico_hombro_der = maximos[pos_pico_hombro_der]

            # REGLA 1: La cabeza debe ser estrictamente más alta que ambos hombros
            cabeza_es_alta = (pico_cabeza >= pico_hombro_izq * (1 + config.PORCENTAJE_FILTRO_CABEZA)) and \
                            (pico_cabeza >= pico_hombro_der * (1 + config.PORCENTAJE_FILTRO_CABEZA))
                            
            # REGLA 2: Los dos hombros deben tener una altura similar entre sí
            hombros_simetricos = abs(pico_hombro_izq - pico_hombro_der) < (pico_hombro_izq * config.PORCENTAJE_TOLERANCIA_HOMBROS)
            
            if cabeza_es_alta and hombros_simetricos:
                # REGLA 3: Verificar la Línea de Cuello (Valle entre Hombro Izq y Cabeza)
                valles_1 = minimos[pos_pico_hombro_izq:pos_pico_cabeza]
                valles_2 = minimos[pos_pico_cabeza:pos_pico_hombro_der]
                
                if valles_1 and valles_2:
                    cuello_1 = min(valles_1)
                    cuello_2 = min(valles_2)
                    
                    # Si el precio actual (Vela 12) ya rompió el promedio de la línea de cuello hacia abajo
                    linea_cuello_promedio = (cuello_1 + cuello_2) / 2
                    
                    if identificar_patrones.vela3_valor_cerro < linea_cuello_promedio:
                        tendencia_bajista, nombre_patron = True, "Hombro Cabeza Hombro"

        # El HCH Invertido REQUIERE una tendencia bajista previa, un MACD debilitándose en ventas,
        # y al menos 3 suelos/valles identificados.
        if identificar_patrones.es_tendencia_bajista and identificar_patrones.macd_debil_bajista and len(identificar_patrones.suelos_indices) >= 3:
            # Tomamos los últimos 3 suelos detectados en el gráfico (del pasado al presente)
            pos_suelo_hombro_izq = identificar_patrones.suelos_indices[-3]
            pos_suelo_cabeza = identificar_patrones.suelos_indices[-2]
            pos_suelo_hombro_der = identificar_patrones.suelos_indices[-1]  # El suelo más reciente en tiempo real
            
            suelo_hombro_izq = minimos[pos_suelo_hombro_izq]
            suelo_cabeza = minimos[pos_suelo_cabeza]
            suelo_hombro_der = minimos[pos_suelo_hombro_der]
            
            # REGLA 1: La cabeza debe ser estrictamente más profunda (más baja) que ambos hombros
            cabeza_es_profunda = (suelo_cabeza <= suelo_hombro_izq * (1 - config.PORCENTAJE_FILTRO_CABEZA)) and \
                                (suelo_cabeza <= suelo_hombro_der * (1 - config.PORCENTAJE_FILTRO_CABEZA))
                            
            # REGLA 2: Los dos hombros deben tener una profundidad similar entre sí
            hombros_simetricos = abs(suelo_hombro_izq - suelo_hombro_der) < (suelo_hombro_izq * config.PORCENTAJE_TOLERANCIA_HOMBROS)
            
            if cabeza_es_profunda and hombros_simetricos:
                # REGLA 3: Verificar la Línea de Cuello (Picos máximos entre Hombro Izq y Cabeza)
                picos_1 = maximos[pos_suelo_hombro_izq:pos_suelo_cabeza]
                picos_2 = maximos[pos_suelo_cabeza:pos_suelo_hombro_der]
                
                if picos_1 and picos_2:
                    cresta_1 = max(picos_1)
                    cresta_2 = max(picos_2)
                    
                    # La línea de cuello es el promedio de las dos crestas intermedias
                    linea_cuello_promedio = (cresta_1 + cresta_2) / 2
                    
                    # Gatillo de Entrada: El cierre de la última vela (Vela 12) rompe el cuello hacia arriba
                    if identificar_patrones.vela3_valor_cerro > linea_cuello_promedio:
                        tendencia_alcista, nombre_patron = True, "Hombro Cabeza Hombro Invertido"

    # ESTRUCTURAS COMPLEJAS Y ESCÁNER COMBINATORIO (50 VELAS)
    if len(identificar_patrones.num_velas_disponibles) >= 50 and nombre_patron == "Ninguno":
        # Verificamos tus filtros de entorno (No debe ser bajista general y el MACD debe mostrar debilidad alcista)
        if not identificar_patrones.es_tendencia_bajista and identificar_patrones.macd_debil_alcista and len(identificar_patrones.picos_indices) >= 2:
            # El segundo pico (y) DEBE SER EL ÚLTIMO DETECTADO en la gráfica para operar en tiempo real
            pos_segundo_pico = identificar_patrones.picos_indices[-1]
            pico_2 = maximos[pos_segundo_pico]
            
            # Buscamos hacia atrás un pico previo (x) que coincida en altura
            for pos_primer_pico in identificar_patrones.picos_indices[:-1]:
                pico_1 = maximos[pos_primer_pico]
                
                # Filtro 1: Tu regla de tolerancia de altura
                if abs(pico_1 - pico_2) < (pico_1 * config.PORCENTAJE_TOLERANCIA_DOBLE_TS):
                    # Filtro 2: SOLUCIÓN AL VALLE (Buscamos el mínimo más bajo EN MEDIO de ambos picos)
                    minimos_intermedios = minimos[pos_primer_pico:pos_segundo_pico]
                    valle_central = min(minimos_intermedios) #if minimos_intermedios else pico_1
                    
                    # El valle debe haber caído un porcentaje mínimo respecto al primer pico
                    if valle_central <= pico_1 * (1 - config.PORCENTAJE_CAIDA_VALLE):
                        tendencia_bajista, nombre_patron = True, "Doble Techo"
                        break # Rompe el bucle, encontramos el patrón real

        # El Doble Suelo REQUIERE tendencia bajista previa y que el impulso vendedor disminuya
        if identificar_patrones.es_tendencia_bajista and identificar_patrones.macd_debil_bajista and len(identificar_patrones.suelos_indices) >= 2:            
            # El segundo suelo (y) DEBE SER EL ÚLTIMO DETECTADO en la gráfica para operar en tiempo real
            pos_segundo_suelo = identificar_patrones.suelos_indices[-1]
            suelo_2 = minimos[pos_segundo_suelo]
            
            # Buscamos hacia atrás un suelo previo (x) para emparejarlo
            for pos_primer_suelo in identificar_patrones.suelos_indices[:-1]:
                suelo_1 = minimos[pos_primer_suelo]
                
                # Filtro 1: Regla de tolerancia de simetría (alturas similares en el suelo)
                if abs(suelo_1 - suelo_2) < (suelo_1 * config.PORCENTAJE_TOLERANCIA_DOBLE_TS):
                    
                    # Filtro 2: EL PICO CENTRAL / CRESTA (Buscamos el máximo más alto EN MEDIO de ambos suelos)
                    maximos_intermedios = maximos[pos_primer_suelo:pos_segundo_suelo]
                    cresta_central = max(maximos_intermedios) if maximos_intermedios else suelo_1
                    
                    # La cresta debe haber subido un porcentaje mínimo respecto al primer suelo (forma de W)
                    if cresta_central >= suelo_1 * (1 + config.PORCENTAJE_REBOTE_CRESTA):
                        tendencia_alcista, nombre_patron = True, "Doble Suelo"
                        break # Encontrado, salimos del bucle para ejecutar la compra
    
    return tendencia_alcista, tendencia_bajista, nombre_patron