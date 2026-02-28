"""Router FastAPI para analisis de tendencias de gases."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from src.dga.domain.exceptions import TransformerNotFoundError
from src.dga.infrastructure.api.dependencies import (
    sample_service,
    trend_service,
)
from src.dga.infrastructure.api.schemas import (
    GasHistoryResponse,
    GasRateResponse,
    TrendAnalysisResponse,
)

router = APIRouter(prefix="/api/trends", tags=["Tendencias"])


@router.get(
    "/history/{transformer_id}",
    response_model=list[GasHistoryResponse],
)
def gas_history(transformer_id: int) -> list[GasHistoryResponse]:
    """Retorna el historial temporal de cada gas de un transformador."""
    try:
        samples = sample_service.list_samples_by_transformer(transformer_id)
    except TransformerNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    histories = trend_service.build_gas_history(samples)
    return [
        GasHistoryResponse(
            gas_name=h.gas_name,
            gas_label=h.gas_label,
            dates=h.dates,
            values=h.values,
        )
        for h in histories
    ]


@router.get(
    "/rates/{transformer_id}",
    response_model=list[TrendAnalysisResponse],
)
def gas_rates(transformer_id: int) -> list[TrendAnalysisResponse]:
    """Calcula las tasas de generacion entre muestras consecutivas."""
    try:
        samples = sample_service.list_samples_by_transformer(transformer_id)
    except TransformerNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    if len(samples) < 2:
        return []

    analyses = trend_service.compute_all_rates(samples)
    return [
        TrendAnalysisResponse(
            sample_from_id=a.sample_from.id,  # type: ignore[arg-type]
            sample_to_id=a.sample_to.id,  # type: ignore[arg-type]
            days_between=a.days_between,
            gas_rates=[
                GasRateResponse(
                    gas_name=gr.gas_name,
                    gas_label=gr.gas_label,
                    previous_ppm=gr.previous_ppm,
                    current_ppm=gr.current_ppm,
                    delta_ppm=gr.delta_ppm,
                    days=gr.days,
                    rate_ppm_day=gr.rate_ppm_day,
                    is_increasing=gr.is_increasing,
                )
                for gr in a.gas_rates
            ],
            increasing_gases=a.increasing_gases,
            critical_gases=a.critical_gases,
        )
        for a in analyses
    ]
