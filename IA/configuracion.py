HORAS_CACHE = 2

TIPO_PROMPT = {
    "Patrones": {
        "activo": True,
        "apertura": "PROMPT_PATRONES",        
        "reevaluacion": "PROMPT_PATRONES_REEVALUACION"
    }
}

MODELO_IA = {
    "Gemini": {
        "activo": True,
        "cache": False,
        "version_apertura": "1_1",
        "version_reevaluacion": "1_1",
        "version_apertura_cache": "1_0",
        "version_reevaluacion_cache": "1_0",
        "modelos": [
            {
                "activo": True,
                "modelo": "gemini-3.1-flash-lite"
            },
            {
                "activo": False,
                "modelo": "gemini-3.5-flash"
            },
            {
                "activo": False,
                "modelo": "gemini-2.5-flash"
            }
        ]
    },
    "Groq": {
        "activo": False,
        "cache": False,
        "version_apertura": "1_0",
        "version_reevaluacion": "1_0",
        "version_apertura_cache": "1_0",
        "version_reevaluacion_cache": "1_0",
        "modelos": [
            {
                "activo": False,
                "modelo": "llama-3.1-8b-instant"
            },
            {
                "activo": False,
                "modelo": "llama-3.3-70b-versatile"
            },
            {
                "activo": True,
                "modelo": "meta-llama/llama-4-scout-17b-16e-instruct"
            }
        ]
    }
}

explicacion_decision = ""
proximas_instrucciones = "Ninguna"