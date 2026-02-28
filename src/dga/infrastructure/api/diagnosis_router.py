"""Router FastAPI para diagnostico normativo (6 metodos)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from src.dga.domain.exceptions import SampleNotFoundError
from src.dga.domain.models.gas_reading import GasReading
from src.dga.infrastructure.api.converters import normative_to_response
from src.dga.infrastructure.api.dependencies import (
    diagnosis_service,
    sample_service,
)
from src.dga.infrastructure.api.schemas import (
    GasReadingSchema,
    MethodResultResponse,
    NormativeDiagnosisResponse,
)

router = APIRouter(prefix="/api/diagnosis", tags=["Diagnostico Normativo"])


@router.post("/normative", response_model=NormativeDiagnosisResponse)
def diagnose_normative(body: GasReadingSchema) -> NormativeDiagnosisResponse:
    """Ejecuta los 6 metodos normativos sobre una lectura de gases."""
    reading = GasReading(
        h2=body.h2, ch4=body.ch4, c2h6=body.c2h6,
        c2h4=body.c2h4, c2h2=body.c2h2, co=body.co,
        co2=body.co2, o2=body.o2, n2=body.n2,
    )
    result = diagnosis_service.diagnose_all(reading)
    return normative_to_response(result)


@router.post(
    "/normative/{method_name}", response_model=MethodResultResponse
)
def diagnose_single_method(
    method_name: str, body: GasReadingSchema
) -> MethodResultResponse:
    """Ejecuta un metodo normativo especifico por nombre."""
    reading = GasReading(
        h2=body.h2, ch4=body.ch4, c2h6=body.c2h6,
        c2h4=body.c2h4, c2h2=body.c2h2, co=body.co,
        co2=body.co2, o2=body.o2, n2=body.n2,
    )
    result = diagnosis_service.diagnose_single(reading, method_name)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Metodo '{method_name}' no encontrado. "
            f"Disponibles: {diagnosis_service.available_methods()}",
        )
    return MethodResultResponse(
        method_name=result.method_name,
        fault_type=result.fault_type.name,
        description=result.description,
    )


@router.get(
    "/normative/sample/{sample_id}",
    response_model=NormativeDiagnosisResponse,
)
def diagnose_sample(sample_id: int) -> NormativeDiagnosisResponse:
    """Diagnostica una muestra existente por su ID."""
    try:
        sample = sample_service.get_sample(sample_id)
    except SampleNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    result = diagnosis_service.diagnose_all(sample.gas_reading)
    return normative_to_response(result)


@router.get("/methods", response_model=list[str])
def list_methods() -> list[str]:
    """Retorna los nombres de los metodos normativos disponibles."""
    return diagnosis_service.available_methods()
