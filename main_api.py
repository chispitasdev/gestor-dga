"""Punto de entrada de la API REST (FastAPI) del sistema DGA.

Uso:
    fastapi dev main_api.py

Documentacion interactiva automatica:
    http://127.0.0.1:8000/docs     (Swagger UI)
    http://127.0.0.1:8000/redoc    (ReDoc)
"""

from __future__ import annotations

from fastapi import FastAPI

from src.dga.infrastructure.api.transformer_router import (
    router as transformer_router,
)
from src.dga.infrastructure.api.sample_router import router as sample_router
from src.dga.infrastructure.api.diagnosis_router import (
    router as diagnosis_router,
)
from src.dga.infrastructure.api.import_router import router as import_router
from src.dga.infrastructure.api.trend_router import router as trend_router
from src.dga.infrastructure.api.ai_router import router as ai_router
from src.dga.infrastructure.api.unified_router import (
    router as unified_router,
)
from src.dga.infrastructure.api.charts_router import router as charts_router
from src.dga.infrastructure.api.validation_router import (
    router as validation_router,
)

app = FastAPI(
    title="Sistema de Diagnostico DGA",
    description=(
        "API REST para el analisis de gases disueltos en aceite "
        "de transformadores de potencia. Implementa 6 metodos "
        "normativos internacionales y 4 modelos de Machine Learning."
    ),
    version="1.0.0",
)

# ── Registrar routers ──────────────────────────────────────────────
app.include_router(transformer_router)
app.include_router(sample_router)
app.include_router(diagnosis_router)
app.include_router(import_router)
app.include_router(trend_router)
app.include_router(ai_router)
app.include_router(unified_router)
app.include_router(charts_router)
app.include_router(validation_router)


@app.get("/", tags=["Root"])
def root() -> dict:
    """Endpoint raiz con informacion basica del sistema."""
    return {
        "sistema": "Diagnostico DGA",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "transformadores": "/api/transformers",
            "muestras": "/api/samples",
            "diagnostico_normativo": "/api/diagnosis",
            "importacion": "/api/import",
            "tendencias": "/api/trends",
            "inteligencia_artificial": "/api/ai",
            "diagnostico_unificado": "/api/unified",
            "graficos": "/api/charts",
            "validacion": "/api/validation",
        },
    }
