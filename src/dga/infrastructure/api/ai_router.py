"""Router FastAPI para el motor de inteligencia artificial."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from src.dga.domain.models.gas_reading import GasReading
from src.dga.infrastructure.api.dependencies import ai_service
from src.dga.infrastructure.api.schemas import (
    AIClassificationResponse,
    EvaluationResponse,
    GasReadingSchema,
    ModelSummary,
    TrainingResponse,
)

router = APIRouter(prefix="/api/ai", tags=["Inteligencia Artificial"])


@router.post("/train", response_model=TrainingResponse)
def train_models() -> TrainingResponse:
    """Entrena los 4 modelos de IA con todas las muestras del repositorio.

    Guarda el mejor modelo en disco automaticamente.
    """
    try:
        result = ai_service.train(save=True)
        return TrainingResponse(
            best_model=result.best_model.name,
            best_accuracy=result.best_model.cv_accuracy,
            models=[
                ModelSummary(
                    name=m.name,
                    accuracy=m.cv_accuracy,
                    std=m.cv_std,
                )
                for m in result.models
            ],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/classify", response_model=AIClassificationResponse)
def classify(body: GasReadingSchema) -> AIClassificationResponse:
    """Clasifica una lectura de gases con el modelo entrenado."""
    reading = GasReading(
        h2=body.h2, ch4=body.ch4, c2h6=body.c2h6,
        c2h4=body.c2h4, c2h2=body.c2h2, co=body.co,
        co2=body.co2, o2=body.o2, n2=body.n2,
    )
    try:
        fault, probs = ai_service.classify_with_proba(reading)
        return AIClassificationResponse(
            fault_type=fault.name,
            probabilities={ft.name: round(p, 4) for ft, p in probs.items()},
        )
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/classify/batch", response_model=list[AIClassificationResponse]
)
def classify_batch(
    body: list[GasReadingSchema],
) -> list[AIClassificationResponse]:
    """Clasifica multiples lecturas en lote."""
    readings = [
        GasReading(
            h2=b.h2, ch4=b.ch4, c2h6=b.c2h6,
            c2h4=b.c2h4, c2h2=b.c2h2, co=b.co,
            co2=b.co2, o2=b.o2, n2=b.n2,
        )
        for b in body
    ]
    try:
        faults = ai_service.classify_batch(readings)
        return [
            AIClassificationResponse(fault_type=f.name) for f in faults
        ]
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/evaluate", response_model=list[EvaluationResponse])
def evaluate_models() -> list[EvaluationResponse]:
    """Evalua los 4 modelos con validacion cruzada."""
    try:
        results = ai_service.evaluate_all()
        return [
            EvaluationResponse(
                model_name=ev.model_name,
                accuracy=ev.overall_accuracy,
                macro_precision=ev.macro_precision,
                macro_recall=ev.macro_recall,
                macro_f1=ev.macro_f1,
                weighted_f1=ev.weighted_f1,
            )
            for ev in results
        ]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/status")
def model_status() -> dict:
    """Verifica si hay un modelo entrenado disponible."""
    return {
        "has_model": ai_service.has_model(),
        "model_path": str(ai_service.model_path()),
    }
