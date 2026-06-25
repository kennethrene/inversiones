import re
import pandas as pd
from selenium.webdriver.common.by import By
from extraccion.velas import extraer_velas
import configuracion.parametros as parametros
from ui.grafico import extraer_datos_velas

# ===========================================================================
# EXTRACCIÓN DE DATOS FILTRADOS POR COLUMNA DESDE EL DOM
# ===========================================================================
def extraer_datos_operacion(lista_cruda):
    """
    Procesa la lista plana de strings reales de xStation eliminando espacios
    invisibles y aislando las cadenas puras para cada columna del bot.
    """
    # Si por desajuste del bucle principal pasara la matriz de detalles completa, extraemos la primera fila
    if len(lista_cruda) > 0 and isinstance(lista_cruda[0], list):
        lista_cruda = lista_cruda[0]

    filtrados = [
        str(elemento).replace('\xa0', ' ').strip() 
        for elemento in lista_cruda[0].split('\n') 
        if str(elemento).strip()
    ]
   
    if len(filtrados) >= 2:
        parametros.datos_mapeados["Activo"] = filtrados[0]  # Cambiado para tomar solo 'US30'
        parametros.datos_mapeados["Tipo"] = filtrados[1]    # Cambiado para tomar solo 'CFD'
        
    for i in range(len(filtrados) - 1):
        texto_actual = filtrados[i].lower()
        siguiente_texto = filtrados[i+1]
        
        if "volumen" == texto_actual:
            parametros.datos_mapeados["Volumen"] = siguiente_texto
        elif "valor del contrato" in texto_actual:
            parametros.datos_mapeados["Valor Contrato"] = siguiente_texto
        elif "precio actual" in texto_actual:
            parametros.datos_mapeados["Precio Actual"] = siguiente_texto
        elif "precio medio de apertura" in texto_actual:
            parametros.datos_mapeados["Precio Apertura"] = siguiente_texto
        elif "beneficio neto %" in texto_actual:
            parametros.datos_mapeados["Beneficio %"] = siguiente_texto
        elif "beneficio neto" == texto_actual:
            parametros.datos_mapeados["Beneficio Neto"] = siguiente_texto
            
    # BÚSQUEDA EXHAUSTIVA DE RESPALDO SI EL MAPEO INDEPENDIENTE SE CORRE
    if parametros.datos_mapeados["Beneficio %"] == "N/D" or "%" not in str(parametros.datos_mapeados["Beneficio %"]):
        for elemento in filtrados:
            if "%" in elemento and ("-" in elemento or re.search(r'\d', elemento)):
                parametros.datos_mapeados["Beneficio %"] = elemento
                break


def obtener_datos_operaciones():
    return """
    return (() => {
        let botonesValidos = [];
        let botones = new Map();
        let todosLosBotones = document.querySelectorAll("button[data-testid='close-button']");
        
        todosLosBotones.forEach(btn => {
            if (btn && (btn.offsetWidth > 0 || btn.offsetHeight > 0)) { 
                botonesValidos.push(btn); 
            }
        });
        
        if (botonesValidos.length === 0) {
            let elementosGlobales = document.querySelectorAll("*");
            elementosGlobales.forEach(el => {
                if (el && el.shadowRoot) {
                    let btnShadow = el.shadowRoot.querySelectorAll("button[data-testid='close-button']");
                    if (btnShadow.length > 0) {
                        btnShadow.forEach(btn => {
                            if (btn && (btn.offsetWidth > 0 || btn.offsetHeight > 0)) {
                                let headerInfo = btn.closest(".header-info");
                                // Validación crítica: Evita el error 'querySelector' of null
                                if (headerInfo) {
                                    let instrumentNameElement = headerInfo.querySelector("[data-testid='instrument-name'] .pds-element-name-value__element-name");
                                    if (instrumentNameElement != null) {
                                        botonesValidos.push(btn);
                                        let activo = instrumentNameElement.innerText.trim();
                                        botones.set(activo, btn);
                                    }
                                }
                            }
                        });
                    }
                }
            });
        }
        
        let datosOperaciones = [];
        botonesValidos.forEach(btn => {
            let fila = btn.closest("tr") || btn.closest("[role='row']") || (btn.parentElement ? btn.parentElement.parentElement : null);
            if (fila) {
                // Doble escape \\\\n para que Python no rompa el salto de línea de JavaScript
                let textos = fila.innerText.split('\\\\n').map(t => t.trim()).filter(t => t.length > 0);
                datosOperaciones.push(textos);
            }
        });
        
        if (botonesValidos.length > 0) { 
            window.ultimoBotonCierre = botonesValidos[0]; 
            window.botonesCerrarLista = botonesValidos; 
            window.botonesCerrarMapa = botones;
        }
        
        return { "total": botonesValidos.length, "detalles": datosOperaciones };
    })();
    """

# ===========================================================================
# ESCANEO CON PERFORADOR SHADOW DOM Y GESTIÓN DE MATRICES
# ===========================================================================
def obtener_datos_compra_venta(segundo_actual, con_grafico, driver):
    # Capturar los datos de compra, venta y lote (proporcion a comprar) de la pestaña actual
    botones_vender = driver.find_elements(By.CSS_SELECTOR, "#sellButton, [id='sellButton']")
    botones_comprar = driver.find_elements(By.CSS_SELECTOR, "#buyButton, [id='buyButton']")
    botones_lote = driver.find_elements(By.CSS_SELECTOR, "span.ui-spinner-amount-value, input[name='stepperInput'], [id='volumeInput']")
    activos = driver.find_elements(By.CLASS_NAME, "chart-panel-symbol-title")
    activo_detectado = None
    
    for boton in botones_vender:
        if boton.is_displayed() and boton.is_enabled():
            if (segundo_actual != parametros.ultimo_segundo_procesado):
                parametros.ultimo_valor_venta = parametros.valor_venta
            parametros.valor_venta = boton.get_attribute("textContent").strip()
            parametros.boton_vender = boton
            break
    for boton in botones_comprar:
        if boton.is_displayed() and boton.is_enabled():
            if (segundo_actual != parametros.ultimo_segundo_procesado):
                parametros.ultimo_valor_compra = parametros.valor_compra
            parametros.valor_compra = boton.get_attribute("textContent").strip()
            parametros.boton_comprar = boton
            break
    for vol in botones_lote:
        if vol.is_displayed():
            texto_vol = vol.get_attribute("value") if vol.tag_name == "input" else vol.get_attribute("textContent").strip()
            if texto_vol:
                parametros.valor_lote = texto_vol.replace("USD", "").strip()
                break
    for activo in activos:
        if activo.is_displayed():
            texto_bruto = activo.get_attribute("textContent")
            if texto_bruto:
                activo_detectado = texto_bruto.replace("CFD", "").strip()
                break
    
    if activo_detectado != parametros.activo_actual:
        parametros.activo_actual = activo_detectado
        parametros.promedio_volumen = 0
        parametros.promedio_volumen_sin_actual = 0.0
        parametros.historico_macd = []
        parametros.historico_rsi = []
        parametros.historico_volumen = []
        parametros.lista_velas_acumuladas = []

        if con_grafico:
            extraer_datos_velas()
