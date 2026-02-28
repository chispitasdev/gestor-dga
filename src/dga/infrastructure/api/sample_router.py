"""Router FastAPI para gestion de muestras DGA."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from src.dga.application.dto.sample_dto import CreateSampleDTO, UpdateSampleDTO
from src.dga.domain.exceptions import (
    DuplicateSampleCodeError,
    InvalidGasValueError,
    SampleNotFoundError,
    TransformerNotFoundError,
)
from src.dga.infrastructure.api.converters import sample_to_response
from src.dga.infrastructure.api.dependencies import sample_service
from src.dga.infrastructure.api.schemas import (
    SampleCreate,
    SampleResponse,
    SampleUpdate,
)

router = APIRouter(prefix="/api/samples", tags=["Muestras"])


@router.get("/", response_model=list[SampleResponse])
def list_samples() -> list[SampleResponse]:
    """Retorna todas las muestras registradas."""
    samples = sample_service.list_samples()
    return [sample_to_response(s) for s in samples]


@router.get("/{sample_id}", response_model=SampleResponse)
def get_sample(sample_id: int) -> SampleResponse:
    """Obtiene una muestra por su ID."""
    try:
        s = sample_service.get_sample(sample_id)
        return sample_to_response(s)
    except SampleNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/transformer/{transformer_id}", response_model=list[SampleResponse]
)
def list_by_transformer(transformer_id: int) -> list[SampleResponse]:
    """Retorna las muestras de un transformador especifico."""
    try:
        samples = sample_service.list_samples_by_transformer(transformer_id)
        return [sample_to_response(s) for s in samples]
    except TransformerNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/", response_model=SampleResponse, status_code=201)
def create_sample(body: SampleCreate) -> SampleResponse:
    """Registra una nueva muestra de aceite."""
    try:
        dto = CreateSampleDTO(
            sample_code=body.sample_code,
            transformer_id=body.transformer_id,
            extraction_date=body.extraction_date,
            h2=body.h2, ch4=body.ch4, c2h6=body.c2h6,
            c2h4=body.c2h4, c2h2=body.c2h2, co=body.co,
            co2=body.co2, o2=body.o2, n2=body.n2,
        )
        s = sample_service.register_sample(dto)
        return sample_to_response(s)
    except TransformerNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DuplicateSampleCodeError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except (InvalidGasValueError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{sample_id}", response_model=SampleResponse)
def update_sample(sample_id: int, body: SampleUpdate) -> SampleResponse:
    """Actualiza una muestra existente."""
    try:
        dto = UpdateSampleDTO(
            id=sample_id,
            sample_code=body.sample_code,
            transformer_id=body.transformer_id,
            extraction_date=body.extraction_date,
            diagnosis_date=body.diagnosis_date,
            h2=body.h2, ch4=body.ch4, c2h6=body.c2h6,
            c2h4=body.c2h4, c2h2=body.c2h2, co=body.co,
            co2=body.co2, o2=body.o2, n2=body.n2,
        )
        s = sample_service.update_sample(dto)
        return sample_to_response(s)
    except SampleNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except TransformerNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DuplicateSampleCodeError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except (InvalidGasValueError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{sample_id}", status_code=204)
def delete_sample(sample_id: int) -> None:
    """Elimina una muestra."""
    try:
        sample_service.remove_sample(sample_id)
    except SampleNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
