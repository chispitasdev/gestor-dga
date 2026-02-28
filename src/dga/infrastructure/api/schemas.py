"""Schemas Pydantic para validacion de requests y responses de la API.

Estos schemas actuan como adaptadores de entrada/salida HTTP.
Los dataclasses del dominio se mantienen intactos; aqui solo se
convierten datos JSON ↔ objetos de dominio.
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


# ================================================================== #
#  Transformadores
# ================================================================== #


class TransformerCreate(BaseModel):
    """Request para crear un transformador."""

    name: str = Field(..., min_length=1, description="Nombre del transformador")


class TransformerUpdate(BaseModel):
    """Request para actualizar un transformador."""

    name: str = Field(..., min_length=1, description="Nuevo nombre")


class TransformerResponse(BaseModel):
    """Response de un transformador."""

    id: int
    name: str


# ================================================================== #
#  Lecturas de gases
# ================================================================== #


class GasReadingSchema(BaseModel):
    """Schema para los 9 gases disueltos en ppm."""

    h2: float = Field(..., ge=0, description="Hidrogeno (ppm)")
    ch4: float = Field(..., ge=0, description="Metano (ppm)")
    c2h6: float = Field(..., ge=0, description="Etano (ppm)")
    c2h4: float = Field(..., ge=0, description="Etileno (ppm)")
    c2h2: float = Field(..., ge=0, description="Acetileno (ppm)")
    co: float = Field(..., ge=0, description="Monoxido de carbono (ppm)")
    co2: float = Field(..., ge=0, description="Dioxido de carbono (ppm)")
    o2: float = Field(0.0, ge=0, description="Oxigeno (ppm)")
    n2: float = Field(0.0, ge=0, description="Nitrogeno (ppm)")


# ================================================================== #
#  Muestras
# ================================================================== #


class SampleCreate(BaseModel):
    """Request para crear una muestra."""

    sample_code: str = Field(..., min_length=1, description="Codigo de muestra")
    transformer_id: int = Field(..., gt=0, description="ID del transformador")
    extraction_date: date = Field(..., description="Fecha de extraccion")
    h2: float = Field(..., ge=0)
    ch4: float = Field(..., ge=0)
    c2h6: float = Field(..., ge=0)
    c2h4: float = Field(..., ge=0)
    c2h2: float = Field(..., ge=0)
    co: float = Field(..., ge=0)
    co2: float = Field(..., ge=0)
    o2: float = Field(..., ge=0)
    n2: float = Field(..., ge=0)


class SampleUpdate(BaseModel):
    """Request para actualizar una muestra."""

    sample_code: str = Field(..., min_length=1)
    transformer_id: int = Field(..., gt=0)
    extraction_date: date
    diagnosis_date: date
    h2: float = Field(..., ge=0)
    ch4: float = Field(..., ge=0)
    c2h6: float = Field(..., ge=0)
    c2h4: float = Field(..., ge=0)
    c2h2: float = Field(..., ge=0)
    co: float = Field(..., ge=0)
    co2: float = Field(..., ge=0)
    o2: float = Field(..., ge=0)
    n2: float = Field(..., ge=0)


class GasReadingResponse(BaseModel):
    """Lectura de gases en la respuesta."""

    h2: float
    ch4: float
    c2h6: float
    c2h4: float
    c2h2: float
    co: float
    co2: float
    o2: float
    n2: float


class SampleResponse(BaseModel):
    """Response de una muestra."""

    id: int
    sample_code: str
    transformer_id: int
    extraction_date: date
    diagnosis_date: date
    gas_reading: GasReadingResponse


# ================================================================== #
#  Diagnostico normativo
# ================================================================== #


class MethodResultResponse(BaseModel):
    """Resultado de un metodo normativo individual."""

    method_name: str
    fault_type: str
    description: str


class NormativeDiagnosisResponse(BaseModel):
    """Resultado del diagnostico normativo completo."""

    consensus_fault: str
    agreement_pct: float
    vote_counts: dict[str, int]
    methods: list[MethodResultResponse]


# ================================================================== #
#  IA
# ================================================================== #


class AIClassificationResponse(BaseModel):
    """Resultado de clasificacion por IA."""

    fault_type: str
    probabilities: Optional[dict[str, float]] = None


class ModelSummary(BaseModel):
    """Resumen de un modelo evaluado durante el entrenamiento."""

    name: str
    accuracy: float
    std: float


class TrainingResponse(BaseModel):
    """Resultado del entrenamiento de IA."""

    best_model: str
    best_accuracy: float
    models: list[ModelSummary]


class EvaluationResponse(BaseModel):
    """Resultado de evaluacion de un modelo."""

    model_name: str
    accuracy: float
    macro_precision: float
    macro_recall: float
    macro_f1: float
    weighted_f1: float


# ================================================================== #
#  Diagnostico unificado
# ================================================================== #


class UnifiedDiagnosisResponse(BaseModel):
    """Resultado del diagnostico unificado."""

    sample_id: int
    sample_code: str
    normative_consensus: str
    normative_agreement_pct: float
    normative_methods: list[MethodResultResponse]
    ai_fault: Optional[str] = None
    ai_probabilities: Optional[dict[str, float]] = None
    agree: Optional[bool] = None


class ComparisonResponse(BaseModel):
    """Resumen comparativo normativo vs IA."""

    total: int
    agreements: int
    disagreements: int
    agreement_pct: float
    details: list[UnifiedDiagnosisResponse]


# ================================================================== #
#  Tendencias
# ================================================================== #


class GasRateResponse(BaseModel):
    """Tasa de generacion de un gas."""

    gas_name: str
    gas_label: str
    previous_ppm: float
    current_ppm: float
    delta_ppm: float
    days: int
    rate_ppm_day: float
    is_increasing: bool


class TrendAnalysisResponse(BaseModel):
    """Resultado del analisis de tendencia entre dos muestras."""

    sample_from_id: int
    sample_to_id: int
    days_between: int
    gas_rates: list[GasRateResponse]
    increasing_gases: list[str]
    critical_gases: list[str]


class GasHistoryResponse(BaseModel):
    """Historial de un gas."""

    gas_name: str
    gas_label: str
    dates: list[date]
    values: list[float]


# ================================================================== #
#  Importacion
# ================================================================== #


class ImportResponse(BaseModel):
    """Resultado de una importacion."""

    total_rows: int
    imported: int
    skipped: int
    errors: list[str]


# ================================================================== #
#  Validacion
# ================================================================== #


class GasStatisticsResponse(BaseModel):
    """Estadisticas de un gas."""

    gas_name: str
    min: float
    max: float
    mean: float
    std: float
    median: float


class DatasetSummaryResponse(BaseModel):
    """Resumen del dataset."""

    total_samples: int
    date_range: Optional[list[date]] = None
    fault_distribution: dict[str, int]
    gas_stats: list[GasStatisticsResponse]
    n_transformers: int


class ModelComparisonResponse(BaseModel):
    """Fila comparativa de modelos."""

    model_name: str
    accuracy: float
    macro_precision: float
    macro_recall: float
    macro_f1: float
    weighted_f1: float


class ValidationReportResponse(BaseModel):
    """Reporte completo de validacion."""

    dataset_summary: DatasetSummaryResponse
    model_comparisons: list[ModelComparisonResponse]
    best_model: Optional[EvaluationResponse] = None
    concordance: Optional[ComparisonResponse] = None
