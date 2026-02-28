"""Router FastAPI para generacion de graficos como imagenes PNG."""

from __future__ import annotations

import io

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from src.dga.domain.exceptions import TransformerNotFoundError
from src.dga.domain.models.gas_reading import GasReading
from src.dga.infrastructure.api.dependencies import (
    ai_service,
    sample_service,
    trend_service,
)
from src.dga.infrastructure.api.schemas import GasReadingSchema
from src.dga.infrastructure.charts.duval_triangle_chart import (
    plot_duval_triangle,
)
from src.dga.infrastructure.charts.trend_chart import (
    plot_gas_trends,
    plot_gas_trends_individual,
)
from src.dga.infrastructure.charts.model_charts import (
    plot_confusion_matrix,
    plot_model_comparison,
    plot_class_metrics,
)

router = APIRouter(prefix="/api/charts", tags=["Graficos"])


def _fig_to_png_response(fig) -> StreamingResponse:
    """Convierte una Figure de matplotlib a StreamingResponse PNG."""
    import matplotlib.pyplot as plt

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")


@router.post("/duval-triangle")
def duval_triangle_chart(body: list[GasReadingSchema]) -> StreamingResponse:
    """Genera el Triangulo de Duval 1 con las lecturas proporcionadas."""
    readings = [
        GasReading(
            h2=b.h2, ch4=b.ch4, c2h6=b.c2h6,
            c2h4=b.c2h4, c2h2=b.c2h2, co=b.co,
            co2=b.co2, o2=b.o2, n2=b.n2,
        )
        for b in body
    ]
    fig = plot_duval_triangle(readings)
    return _fig_to_png_response(fig)


@router.get("/duval-triangle/transformer/{transformer_id}")
def duval_triangle_by_transformer(
    transformer_id: int,
) -> StreamingResponse:
    """Genera el Triangulo de Duval con muestras de un transformador."""
    try:
        samples = sample_service.list_samples_by_transformer(transformer_id)
    except TransformerNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    readings = [s.gas_reading for s in samples]
    labels = [s.sample_code for s in samples]
    fig = plot_duval_triangle(readings, labels=labels)
    return _fig_to_png_response(fig)


@router.get("/trends/{transformer_id}")
def trends_chart(transformer_id: int) -> StreamingResponse:
    """Genera el grafico de tendencias combinado de un transformador."""
    try:
        samples = sample_service.list_samples_by_transformer(transformer_id)
    except TransformerNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    histories = trend_service.build_gas_history(samples)
    fig = plot_gas_trends(histories)
    return _fig_to_png_response(fig)


@router.get("/trends/{transformer_id}/individual")
def trends_individual_chart(
    transformer_id: int,
) -> StreamingResponse:
    """Genera subplots individuales de tendencias por gas."""
    try:
        samples = sample_service.list_samples_by_transformer(transformer_id)
    except TransformerNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    histories = trend_service.build_gas_history(samples)
    fig = plot_gas_trends_individual(histories)
    return _fig_to_png_response(fig)


@router.get("/model-comparison")
def model_comparison_chart() -> StreamingResponse:
    """Genera el grafico de comparacion de accuracy de los modelos."""
    try:
        result = ai_service.train(save=False)
        fig = plot_model_comparison(result)
        return _fig_to_png_response(fig)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/confusion-matrix")
def confusion_matrix_chart() -> StreamingResponse:
    """Genera la matriz de confusion del mejor modelo."""
    try:
        eval_results = ai_service.evaluate_all()
        if not eval_results:
            raise HTTPException(
                status_code=400, detail="No hay resultados de evaluacion."
            )
        fig = plot_confusion_matrix(eval_results[0])
        return _fig_to_png_response(fig)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/class-metrics")
def class_metrics_chart() -> StreamingResponse:
    """Genera el grafico de metricas por clase del mejor modelo."""
    try:
        eval_results = ai_service.evaluate_all()
        if not eval_results:
            raise HTTPException(
                status_code=400, detail="No hay resultados de evaluacion."
            )
        fig = plot_class_metrics(eval_results[0])
        return _fig_to_png_response(fig)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
