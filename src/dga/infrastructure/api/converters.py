"""Funciones auxiliares para convertir entidades de dominio a schemas de respuesta."""

from __future__ import annotations

from src.dga.domain.models.sample import Sample
from src.dga.domain.models.transformer import Transformer
from src.dga.application.services.normative_diagnosis_service import (
    NormativeDiagnosisResult,
)
from src.dga.application.services.unified_diagnosis_service import (
    UnifiedDiagnosisResult,
)
from src.dga.infrastructure.api.schemas import (
    GasReadingResponse,
    MethodResultResponse,
    NormativeDiagnosisResponse,
    SampleResponse,
    TransformerResponse,
    UnifiedDiagnosisResponse,
)


def transformer_to_response(t: Transformer) -> TransformerResponse:
    """Convierte entidad Transformer a schema de respuesta."""
    return TransformerResponse(id=t.id, name=t.name)  # type: ignore[arg-type]


def sample_to_response(s: Sample) -> SampleResponse:
    """Convierte entidad Sample a schema de respuesta."""
    gr = s.gas_reading
    return SampleResponse(
        id=s.id,  # type: ignore[arg-type]
        sample_code=s.sample_code,
        transformer_id=s.transformer_id,
        extraction_date=s.extraction_date,
        diagnosis_date=s.diagnosis_date,
        gas_reading=GasReadingResponse(
            h2=gr.h2, ch4=gr.ch4, c2h6=gr.c2h6, c2h4=gr.c2h4,
            c2h2=gr.c2h2, co=gr.co, co2=gr.co2, o2=gr.o2, n2=gr.n2,
        ),
    )


def normative_to_response(
    result: NormativeDiagnosisResult,
) -> NormativeDiagnosisResponse:
    """Convierte NormativeDiagnosisResult a schema de respuesta."""
    return NormativeDiagnosisResponse(
        consensus_fault=result.consensus_fault.name,
        agreement_pct=result.agreement_pct,
        vote_counts=result.vote_counts,
        methods=[
            MethodResultResponse(
                method_name=mr.method_name,
                fault_type=mr.fault_type.name,
                description=mr.description,
            )
            for mr in result.results
        ],
    )


def unified_to_response(
    result: UnifiedDiagnosisResult,
) -> UnifiedDiagnosisResponse:
    """Convierte UnifiedDiagnosisResult a schema de respuesta."""
    ai_probs = None
    if result.ai_probabilities:
        ai_probs = {ft.name: prob for ft, prob in result.ai_probabilities.items()}

    return UnifiedDiagnosisResponse(
        sample_id=result.sample.id,  # type: ignore[arg-type]
        sample_code=result.sample.sample_code,
        normative_consensus=result.normative.consensus_fault.name,
        normative_agreement_pct=result.normative.agreement_pct,
        normative_methods=[
            MethodResultResponse(
                method_name=mr.method_name,
                fault_type=mr.fault_type.name,
                description=mr.description,
            )
            for mr in result.normative.results
        ],
        ai_fault=result.ai_fault.name if result.ai_fault else None,
        ai_probabilities=ai_probs,
        agree=result.agree,
    )
