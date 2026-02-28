"""Puerto abstracto del repositorio de transformadores.

Define el contrato que cualquier adaptador de persistencia debe cumplir
para gestionar entidades ``Transformer``. La capa de aplicacion depende
exclusivamente de esta interfaz, no de la implementacion concreta
(Principio de Inversion de Dependencias).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from src.dga.domain.models.transformer import Transformer


class TransformerRepository(ABC):
    """Interfaz abstracta para la persistencia de transformadores.

    Todas las implementaciones concretas (SQLite, PostgreSQL, en memoria, etc.)
    deben heredar de esta clase e implementar cada metodo.
    """

    @abstractmethod
    def create(self, transformer: Transformer) -> Transformer:
        """Persiste un nuevo transformador y retorna la entidad con ID asignado.

        Args:
            transformer: Entidad sin ID (sera asignado por la persistencia).

        Returns:
            La misma entidad con el ``id`` poblado.

        Raises:
            DuplicateTransformerError: Si ya existe un transformador con el
                mismo nombre.
        """

    @abstractmethod
    def get_by_id(self, transformer_id: int) -> Optional[Transformer]:
        """Busca un transformador por su identificador unico.

        Args:
            transformer_id: ID del transformador a buscar.

        Returns:
            La entidad encontrada o ``None`` si no existe.
        """

    @abstractmethod
    def get_all(self) -> list[Transformer]:
        """Retorna todos los transformadores registrados.

        Returns:
            Lista de transformadores, puede estar vacia.
        """

    @abstractmethod
    def update(self, transformer: Transformer) -> Transformer:
        """Actualiza los datos de un transformador existente.

        Args:
            transformer: Entidad con ``id`` valido y datos actualizados.

        Returns:
            La entidad actualizada.

        Raises:
            TransformerNotFoundError: Si el ID no corresponde a ningun registro.
            DuplicateTransformerError: Si el nuevo nombre ya esta en uso.
        """

    @abstractmethod
    def delete(self, transformer_id: int) -> None:
        """Elimina un transformador por su identificador.

        La eliminacion en cascada de las muestras asociadas depende de la
        configuracion de integridad referencial del adaptador concreto.

        Args:
            transformer_id: ID del transformador a eliminar.

        Raises:
            TransformerNotFoundError: Si el ID no corresponde a ningun registro.
        """
