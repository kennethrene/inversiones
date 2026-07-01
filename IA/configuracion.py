HORAS_CACHE = 2

TIPO_PROMPT = {
    "Patrones": {
        "activo": False,
        "apertura": "PROMPT_PATRONES",
        "version_apertura": "2_4",
        "version_apertura_cache": "2_0",
        "reevaluacion": "PROMPT_PATRONES_REEVALUACION",
        "version_reevaluacion": "2_0",
        "version_reevaluacion_cache": "2_0",
        "indicadores": False,
        "indicador": ""
    },
    "Híbrido": {
        "activo": True,
        "apertura": "PROMPT_HIBRIDO",
        "version_apertura": "2_5i",
        "version_apertura_cache": "1_0i",
        "reevaluacion": "PROMPT_HIBRIDO_REEVALUACION",
        "version_reevaluacion": "1_0i",
        "version_reevaluacion_cache": "1_0i",
        "indicadores": True,
        "indicador": "Bollinger-MACD"
    }
}

MODELO_IA = {
    "Gemini": {
        "activo": True,
        "cache": False,
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