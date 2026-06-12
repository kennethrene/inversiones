(function probarBuscador() {
    let botonesEncontrados = [];

    // 1. Intentar búsqueda global estándar
    let normales = document.querySelectorAll("button[data-testid='close-button']");
    if (normales.length > 0) {
        console.log(`🔍 Se encontraron ${normales.length} botones en el DOM estándar.`);
        normales.forEach(btn => botonesEncontrados.push(btn));
    }

    // 2. Perforar el Shadow DOM de todos los elementos personalizados de xStation
    let todos = document.querySelectorAll("*");
    todos.forEach(el => {
        if (el.shadowRoot) {
            let internos = el.shadowRoot.querySelectorAll("button[data-testid='close-button']");
            if (internos.length > 0) {
                console.log(`⚠️ Botón detectado DENTRO del Shadow DOM del elemento: <${el.tagName.toLowerCase()}>`);
                internos.forEach(btn => {
                    // Guardamos solo los botones que tengan dimensiones físicas reales (visibles)
                    if (btn.offsetWidth > 0 || btn.offsetHeight > 0) {
                        botonesEncontrados.push(btn);
                    }
                });
            }
        }
    });
   
    // Devolvemos la lista para que puedas interactuar con ella en la consola
    return botonesEncontrados;
})();

"activo": btn.closest(".header-info").querySelector("[data-testid='instrument-name'] .pds-element-name-value__element-name").innerText.trim()


resultado = (function obtener() {
    
    let botonesValidos = [];        let botones = new Map();        let todosLosBotones = document.querySelectorAll("button[data-testid='close-button']");                
    todosLosBotones.forEach(btn => {            if (btn.offsetWidth > 0 || btn.offsetHeight > 0) { botonesValidos.push(btn); }        });                
    if (botonesValidos.length === 0) {            let elementosGlobales = document.querySelectorAll("*");            
                                      elementosGlobales.forEach(el => {                
                                          if (el.shadowRoot) {                    
                                              let btnShadow = el.shadowRoot.querySelectorAll("button[data-testid='close-button']");                    
                                              if (btnShadow.length > 0) {                        btnShadow.forEach(btn => {
        if (btn && (btn.offsetWidth > 0 || btn.offsetHeight > 0) &&
            btn.closest(".header-info").querySelector("[data-testid='instrument-name'] .pds-element-name-value__element-name") != null) {
                botonesValidos.push(btn);
                activo = btn.closest(".header-info").querySelector("[data-testid='instrument-name'] .pds-element-name-value__element-name").innerText.trim();
                botones.set(activo, btn);
                }
                });
                }
                }
                });        }                let datosOperaciones = [];        
                botonesValidos.forEach(btn => {            
                    let fila = btn.closest("tr") || btn.closest("[role='row']") || btn.parentElement.parentElement;            
                    if (fila) {                let textos = fila.innerText.split('\\').map(t => t.trim()).filter(t => t.length > 0);                
                               datosOperaciones.push(textos);            
                               }        });                
                               if (botonesValidos.length > 0) 
                               { window.ultimoBotonCierre = botonesValidos[0]; window.botonesCerrar = botonesValidos; window.botonesCerrar = botones;}        
                               return { "total": botonesValidos.length, "detalles": datosOperaciones };
}
)();


(function obtener() {
    if (window.botonesCerrar && window.botonesCerrar.get('US500')) { 
        window.botonesCerrar.get('US500').click()
    } else {
        console.log("No se puede");
    }
}
)();