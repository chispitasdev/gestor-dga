"""Router FastAPI para diagnostico unificado (normativo + IA)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from src.dga.domain.exceptions import SampleNotFoundError
from src.dga.infrastructure.api.converters import unified_to_response
from src.dga.infrastructure.api.dependencies import (
    sample_service,
    unified_service,
)
from src.dga.infrastructure.api.schemas import (
    ComparisonResponse,
    UnifiedDiagnosisResponse,
)

router = APIRouter(prefix="/api/unified", tags=["Diagnostico Unificado"])


@router.get(
    "/sample/{sample_id}", response_model=UnifiedDiagnosisResponse
)
def diagnose_unified(sample_id: int) -> UnifiedDiagnosisResponse:
    """Diagnostica una muestra con normativo + IA."""
    try:
        sample = sample_service.get_sample(sample_id)
    except SampleNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    result = unified_service.diagnose(sample)
    return unified_to_response(result)


@router.get(
    "/batch/transformer/{transformer_id}",
    response_model=list[UnifiedDiagnosisResponse],
)
def diagnose_batch(
    transformer_id: int,
) -> list[UnifiedDiagnosisResponse]:
    """Diagnostico unificado de todas las muestras de un transformador."""
    from src.dga.domain.exceptions import TransformerNotFoundError

    try:
        samples = sample_service.list_samples_by_transformer(transformer_id)
    except TransformerNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    results = unified_service.diagnose_batch(samples)
    return [unified_to_response(r) for r in results]


@router.get(
    "/compare/transformer/{transformer_id}",
    response_model=ComparisonResponse,
)
def compare(transformer_id: int) -> ComparisonResponse:
    """Compara normativo vs IA para un transformador."""
    from src.dga.domain.exceptions import TransformerNotFoundError

    try:
        samples = sample_service.list_samples_by_transformer(transformer_id)
    except TransformerNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    summary = unified_service.compare(samples)
    return ComparisonResponse(
        total=summary.total,
        agreements=summary.agreements,
        disagreements=summary.disagreements,
        agreement_pct=summary.agreement_pct,
        details=[unified_to_response(d) for d in summary.details],
    )
