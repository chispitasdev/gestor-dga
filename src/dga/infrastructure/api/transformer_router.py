"""Router FastAPI para gestion de transformadores."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from src.dga.application.dto.transformer_dto import (
    CreateTransformerDTO,
    UpdateTransformerDTO,
)
from src.dga.domain.exceptions import (
    DuplicateTransformerError,
    TransformerNotFoundError,
)
from src.dga.infrastructure.api.converters import transformer_to_response
from src.dga.infrastructure.api.dependencies import transformer_service
from src.dga.infrastructure.api.schemas import (
    TransformerCreate,
    TransformerResponse,
    TransformerUpdate,
)

router = APIRouter(prefix="/api/transformers", tags=["Transformadores"])


@router.get("/", response_model=list[TransformerResponse])
def list_transformers() -> list[TransformerResponse]:
    """Retorna todos los transformadores registrados."""
    transformers = transformer_service.list_transformers()
    return [transformer_to_response(t) for t in transformers]


@router.get("/{transformer_id}", response_model=TransformerResponse)
def get_transformer(transformer_id: int) -> TransformerResponse:
    """Obtiene un transformador por su ID."""
    try:
        t = transformer_service.get_transformer(transformer_id)
        return transformer_to_response(t)
    except TransformerNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/", response_model=TransformerResponse, status_code=201)
def create_transformer(body: TransformerCreate) -> TransformerResponse:
    """Registra un nuevo transformador."""
    try:
        dto = CreateTransformerDTO(name=body.name)
        t = transformer_service.register_transformer(dto)
        return transformer_to_response(t)
    except DuplicateTransformerError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{transformer_id}", response_model=TransformerResponse)
def update_transformer(
    transformer_id: int, body: TransformerUpdate
) -> TransformerResponse:
    """Actualiza un transformador existente."""
    try:
        dto = UpdateTransformerDTO(id=transformer_id, name=body.name)
        t = transformer_service.update_transformer(dto)
        return transformer_to_response(t)
    except TransformerNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DuplicateTransformerError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.delete("/{transformer_id}", status_code=204)
def delete_transformer(transformer_id: int) -> None:
    """Elimina un transformador."""
    try:
        transformer_service.remove_transformer(transformer_id)
    except TransformerNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
