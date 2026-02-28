"""Servicio de aplicacion para la gestion de transformadores.

Orquesta las operaciones CRUD sobre transformadores coordinando entre
los DTOs de entrada, las entidades de dominio y los puertos de
repositorio. No contiene logica de persistencia (SRP).
"""

from __future__ import annotations

from src.dga.application.dto.transformer_dto import (
    CreateTransformerDTO,
    UpdateTransformerDTO,
)
from src.dga.domain.exceptions import TransformerNotFoundError
from src.dga.domain.models.transformer import Transformer
from src.dga.domain.ports.transformer_repository import TransformerRepository


class TransformerService:
    """Caso de uso para operaciones CRUD de transformadores.

    Recibe el puerto ``TransformerRepository`` por inyeccion de dependencias,
    cumpliendo con el Principio de Inversion de Dependencias (DIP).

    Args:
        repository: Implementacion concreta del repositorio de transformadores.
    """

    def __init__(self, repository: TransformerRepository) -> None:
        self._repository = repository

    def register_transformer(self, dto: CreateTransformerDTO) -> Transformer:
        """Registra un nuevo transformador en el sistema.

        Args:
            dto: Datos del transformador a crear.

        Returns:
            Entidad con el ``id`` asignado por la persistencia.

        Raises:
            DuplicateTransformerError: Si el nombre ya esta registrado.
            ValueError: Si el nombre es invalido.
        """
        transformer = Transformer(name=dto.name)
        return self._repository.create(transformer)

    def list_transformers(self) -> list[Transformer]:
        """Retorna todos los transformadores registrados.

        Returns:
            Lista de transformadores, puede estar vacia.
        """
        return self._repository.get_all()

    def get_transformer(self, transformer_id: int) -> Transformer:
        """Obtiene un transformador por su ID.

        Args:
            transformer_id: Identificador del transformador.

        Returns:
            Entidad del transformador encontrado.

        Raises:
            TransformerNotFoundError: Si no existe.
        """
        transformer = self._repository.get_by_id(transformer_id)
        if transformer is None:
            raise TransformerNotFoundError(transformer_id)
        return transformer

    def update_transformer(self, dto: UpdateTransformerDTO) -> Transformer:
        """Actualiza los datos de un transformador existente.

        Args:
            dto: Datos actualizados incluyendo el ID.

        Returns:
            Entidad actualizada.

        Raises:
            TransformerNotFoundError: Si el ID no existe.
            DuplicateTransformerError: Si el nuevo nombre ya esta en uso.
        """
        transformer = Transformer(name=dto.name, id=dto.id)
        return self._repository.update(transformer)

    def remove_transformer(self, transformer_id: int) -> None:
        """Elimina un transformador y sus muestras asociadas.

        Args:
            transformer_id: Identificador del transformador a eliminar.

        Raises:
            TransformerNotFoundError: Si el ID no existe.
        """
        self._repository.delete(transformer_id)
