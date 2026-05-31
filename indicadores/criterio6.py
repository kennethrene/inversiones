import config.config as config

# Criterio rápido: Subidas y bajadas muy rápidas
def ejecutar_criterio():    
    if config.ultimo_valor_compra != None \
        and abs(float(config.valor_compra) - float(config.ultimo_valor_compra)) > float(config.movimiento_abrupto[config.activo_actual]) \
        and float(config.valor_compra) > float(config.ultimo_valor_compra):
                            
            config.log_operacion = f" ℹ️  Comprando por criterio rápido: Movimiento abrupto {abs(float(config.valor_compra) - float(config.ultimo_valor_compra))} supera el requerido {config.movimiento_abrupto[config.activo_actual]}"
            config.datos_mapeados["Criterio Apertura"] = "Criterio rápido"
            return "Comprar"
    if config.ultimo_valor_venta != None \
        and abs(float(config.valor_venta) - float(config.ultimo_valor_venta)) > float(config.movimiento_abrupto[config.activo_actual]) \
        and float(config.valor_venta) < float(config.ultimo_valor_venta):
        
            config.log_operacion = f" ℹ️  Vendiendo por criterio rápido: Movimiento abrupto {abs(float(config.valor_venta) - float(config.ultimo_valor_venta)) } supera el requerido {config.movimiento_abrupto[config.activo_actual]}"
            config.datos_mapeados["Criterio Apertura"] = "Criterio rápido"
            return "Vender"

    return None