"""Puerto abstracto del repositorio de muestras DGA.

Define el contrato que cualquier adaptador de persistencia debe cumplir
para gestionar entidades ``Sample``. Sigue el mismo patron que
``TransformerRepository`` para mantener consistencia en la arquitectura.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from src.dga.domain.models.sample import Sample


class SampleRepository(ABC):
    """Interfaz abstracta para la persistencia de muestras de aceite.

    Todas las implementaciones concretas deben heredar de esta clase
    e implementar cada metodo.
    """

    @abstractmethod
    def create(self, sample: Sample) -> Sample:
        """Persiste una nueva muestra y retorna la entidad con ID asignado.

        Args:
            sample: Entidad sin ID (sera asignado por la persistencia).

        Returns:
            La misma entidad con el ``id`` poblado.

        Raises:
            DuplicateSampleCodeError: Si ya existe una muestra con el
                mismo codigo.
        """

    @abstractmethod
    def get_by_id(self, sample_id: int) -> Optional[Sample]:
        """Busca una muestra por su identificador unico.

        Args:
            sample_id: ID de la muestra a buscar.

        Returns:
            La entidad encontrada o ``None`` si no existe.
        """

    @abstractmethod
    def get_by_transformer_id(self, transformer_id: int) -> list[Sample]:
        """Retorna todas las muestras asociadas a un transformador.

        Args:
            transformer_id: ID del transformador cuyos registros se buscan.

        Returns:
            Lista de muestras del transformador, puede estar vacia.
        """

    @abstractmethod
    def get_all(self) -> list[Sample]:
        """Retorna todas las muestras registradas.

        Returns:
            Lista de muestras, puede estar vacia.
        """

    @abstractmethod
    def update(self, sample: Sample) -> Sample:
        """Actualiza los datos de una muestra existente.

        Args:
            sample: Entidad con ``id`` valido y datos actualizados.

        Returns:
            La entidad actualizada.

        Raises:
            SampleNotFoundError: Si el ID no corresponde a ningun registro.
            DuplicateSampleCodeError: Si el nuevo codigo ya esta en uso.
        """

    @abstractmethod
    def delete(self, sample_id: int) -> None:
        """Elimina una muestra por su identificador.

        Args:
            sample_id: ID de la muestra a eliminar.

        Raises:
            SampleNotFoundError: Si el ID no corresponde a ningun registro.
        """
