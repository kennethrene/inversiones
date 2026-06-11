HORAS_CACHE = 2

TIPO_PROMPT = {
    "Patrones": {
        "activo": True,
        "version_apertura": "1_1",
        "version_reevaluacion": "1_1",
        "version_esquema": "1_0",
        "apertura": "PROMPT_PATRONES",        
        "reevaluacion": "PROMPT_PATRONES_REEVALUACION"
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
    },
    "DeepSeek": {
        "activo": False,
        "cache": False,
        "modelos": [
            {
                "activo": True,
                "modelo": "deepseek-chat"
            }
        ]
    },
    "Claude": {
        "activo": False,
        "cache": False,
        "modelos": [
            {
                "activo": False,
                "modelo": "claude-3-5-sonnet-20241022"
            },
            {
                "activo": False,
                "modelo": "claude-3-haiku-20240307"
            },
            {
                "activo": True,
                "modelo": "claude-sonnet-4-6"
            }
        ]
    }
}

explicacion_decision = ""
proximas_instrucciones = "Ninguna"