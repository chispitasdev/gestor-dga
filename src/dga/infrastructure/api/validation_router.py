"""Router FastAPI para validacion y reportes de tesis (Cap. 5)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from src.dga.domain.exceptions import TransformerNotFoundError
from src.dga.infrastructure.api.dependencies import (
    sample_service,
    validation_service,
)
from src.dga.infrastructure.api.schemas import (
    DatasetSummaryResponse,
    EvaluationResponse,
    GasStatisticsResponse,
    ModelComparisonResponse,
    ValidationReportResponse,
)
from src.dga.infrastructure.api.converters import unified_to_response
from src.dga.infrastructure.api.schemas import ComparisonResponse

router = APIRouter(prefix="/api/validation", tags=["Validacion"])


@router.get("/dataset-summary", response_model=DatasetSummaryResponse)
def dataset_summary() -> DatasetSummaryResponse:
    """Calcula resumen estadistico de todas las muestras."""
    samples = sample_service.list_samples()
    ds = validation_service.build_dataset_summary(samples)
    return DatasetSummaryResponse(
        total_samples=ds.total_samples,
        date_range=[ds.date_range[0], ds.date_range[1]] if ds.date_range else None,
        fault_distribution=ds.fault_distribution,
        gas_stats=[
            GasStatisticsResponse(
                gas_name=gs.gas_name,
                min=gs.min, max=gs.max, mean=gs.mean,
                std=gs.std, median=gs.median,
            )
            for gs in ds.gas_stats
        ],
        n_transformers=ds.n_transformers,
    )


@router.get(
    "/model-comparison", response_model=list[ModelComparisonResponse]
)
def model_comparison() -> list[ModelComparisonResponse]:
    """Evalua y compara los 4 modelos de IA."""
    try:
        rows, _ = validation_service.evaluate_all_models()
        return [
            ModelComparisonResponse(
                model_name=r.model_name,
                accuracy=r.accuracy,
                macro_precision=r.macro_precision,
                macro_recall=r.macro_recall,
                macro_f1=r.macro_f1,
                weighted_f1=r.weighted_f1,
            )
            for r in rows
        ]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/concordance/transformer/{transformer_id}",
    response_model=ComparisonResponse,
)
def concordance(transformer_id: int) -> ComparisonResponse:
    """Analisis de concordancia normativo vs IA para un transformador."""
    try:
        samples = sample_service.list_samples_by_transformer(transformer_id)
    except TransformerNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    summary = validation_service.concordance_analysis(samples)
    return ComparisonResponse(
        total=summary.total,
        agreements=summary.agreements,
        disagreements=summary.disagreements,
        agreement_pct=summary.agreement_pct,
        details=[unified_to_response(d) for d in summary.details],
    )


@router.get("/full-report", response_model=ValidationReportResponse)
def full_report() -> ValidationReportResponse:
    """Genera el reporte completo de validacion para la tesis."""
    samples = sample_service.list_samples()
    if not samples:
        raise HTTPException(
            status_code=400,
            detail="No hay muestras en la base de datos.",
        )

    try:
        report = validation_service.full_validation(samples)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    best_model = None
    if report.best_model_eval:
        ev = report.best_model_eval
        best_model = EvaluationResponse(
            model_name=ev.model_name,
            accuracy=ev.overall_accuracy,
            macro_precision=ev.macro_precision,
            macro_recall=ev.macro_recall,
            macro_f1=ev.macro_f1,
            weighted_f1=ev.weighted_f1,
        )

    concordance_resp = None
    if report.concordance:
        cs = report.concordance
        concordance_resp = ComparisonResponse(
            total=cs.total,
            agreements=cs.agreements,
            disagreements=cs.disagreements,
            agreement_pct=cs.agreement_pct,
            details=[unified_to_response(d) for d in cs.details],
        )

    ds = report.dataset_summary
    return ValidationReportResponse(
        dataset_summary=DatasetSummaryResponse(
            total_samples=ds.total_samples,
            date_range=(
                [ds.date_range[0], ds.date_range[1]]
                if ds.date_range
                else None
            ),
            fault_distribution=ds.fault_distribution,
            gas_stats=[
                GasStatisticsResponse(
                    gas_name=gs.gas_name,
                    min=gs.min, max=gs.max, mean=gs.mean,
                    std=gs.std, median=gs.median,
                )
                for gs in ds.gas_stats
            ],
            n_transformers=ds.n_transformers,
        ),
        model_comparisons=[
            ModelComparisonResponse(
                model_name=r.model_name,
                accuracy=r.accuracy,
                macro_precision=r.macro_precision,
                macro_recall=r.macro_recall,
                macro_f1=r.macro_f1,
                weighted_f1=r.weighted_f1,
            )
            for r in report.model_comparisons
        ],
        best_model=best_model,
        concordance=concordance_resp,
    )
