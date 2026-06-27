from extraccion.velas import extraer_velas_con_bollinger
import numpy as np
from tvDatafeed import Interval


if __name__ == "__main__":
    resultado = extraer_velas_con_bollinger("US100", Interval.in_5_minute, 60)
    
    if resultado:
        print("\n=== ÚLTIMAS 5 VELAS CON BANDAS DE BOLLINGER ===")
        
        # Tomamos solo los últimos 5 elementos usando un slice [-5:]
        for vela in resultado[-5:]:
            print(
                f"Abre: {vela['Open']:.5f} | "
                f"Cierre: {vela['Close']:.5f} | "
                f"B. Inferior: {vela['Lower']:.5f} | "
                f"M. Móvil: {vela['Middle']:.5f} | "
                f"B. Superior: {vela['Upper']:.5f}"
            )

    

