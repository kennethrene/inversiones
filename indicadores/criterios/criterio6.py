import configuracion.parametros as parametros

# Criterio rápido: Subidas y bajadas muy rápidas
def ejecutar_criterio():    
    if parametros.ultimo_valor_compra != None \
        and abs(float(parametros.valor_compra) - float(parametros.ultimo_valor_compra)) > float(parametros.movimiento_abrupto[parametros.activo_actual]) \
        and float(parametros.valor_compra) > float(parametros.ultimo_valor_compra):
                            
            parametros.log_operacion = f" ℹ️  Comprando por criterio rápido: Movimiento abrupto {abs(float(parametros.valor_compra) - float(parametros.ultimo_valor_compra))} supera el requerido {parametros.movimiento_abrupto[parametros.activo_actual]}"
            parametros.datos_mapeados["Criterio Apertura"] = "Criterio rápido"
            return "Comprar"
    if parametros.ultimo_valor_venta != None \
        and abs(float(parametros.valor_venta) - float(parametros.ultimo_valor_venta)) > float(parametros.movimiento_abrupto[parametros.activo_actual]) \
        and float(parametros.valor_venta) < float(parametros.ultimo_valor_venta):
        
            parametros.log_operacion = f" ℹ️  Vendiendo por criterio rápido: Movimiento abrupto {abs(float(parametros.valor_venta) - float(parametros.ultimo_valor_venta)) } supera el requerido {parametros.movimiento_abrupto[parametros.activo_actual]}"
            parametros.datos_mapeados["Criterio Apertura"] = "Criterio rápido"
            return "Vender"

    return None