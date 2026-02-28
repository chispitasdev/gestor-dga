"""Servicio de aplicacion para la gestion de muestras DGA.

Orquesta las operaciones CRUD sobre muestras de aceite, coordinando entre
los DTOs, las entidades de dominio (incluyendo el Value Object GasReading)
y los puertos de repositorio. Valida la existencia del transformador
asociado antes de crear o actualizar una muestra.
"""

from __future__ import annotations

from src.dga.application.dto.sample_dto import CreateSampleDTO, UpdateSampleDTO
from src.dga.domain.exceptions import (
    SampleNotFoundError,
    TransformerNotFoundError,
)
from src.dga.domain.models.gas_reading import GasReading
from src.dga.domain.models.sample import Sample
from src.dga.domain.ports.sample_repository import SampleRepository
from src.dga.domain.ports.transformer_repository import TransformerRepository


class SampleService:
    """Caso de uso para operaciones CRUD de muestras de aceite.

    Requiere ambos puertos de repositorio: muestras y transformadores.
    El repositorio de transformadores se utiliza para validar la existencia
    del equipo antes de asociar una muestra.

    Args:
        sample_repository: Implementacion del repositorio de muestras.
        transformer_repository: Implementacion del repositorio de transformadores.
    """

    def __init__(
        self,
        sample_repository: SampleRepository,
        transformer_repository: TransformerRepository,
    ) -> None:
        self._sample_repo = sample_repository
        self._transformer_repo = transformer_repository

    def _validate_transformer_exists(self, transformer_id: int) -> None:
        """Verifica que el transformador asociado exista.

        Args:
            transformer_id: ID del transformador a verificar.

        Raises:
            TransformerNotFoundError: Si no existe.
        """
        if self._transformer_repo.get_by_id(transformer_id) is None:
            raise TransformerNotFoundError(transformer_id)

    @staticmethod
    def _build_gas_reading(
        h2: float, ch4: float, c2h6: float, c2h4: float, c2h2: float,
        co: float, co2: float, o2: float, n2: float,
    ) -> GasReading:
        """Construye un GasReading a partir de valores individuales.

        Args:
            h2: Hidrogeno (ppm).
            ch4: Metano (ppm).
            c2h6: Etano (ppm).
            c2h4: Etileno (ppm).
            c2h2: Acetileno (ppm).
            co: Monoxido de carbono (ppm).
            co2: Dioxido de carbono (ppm).
            o2: Oxigeno (ppm).
            n2: Nitrogeno (ppm).

        Returns:
            Instancia inmutable de GasReading.

        Raises:
            InvalidGasValueError: Si algun valor es negativo o no numerico.
        """
        return GasReading(
            h2=h2, ch4=ch4, c2h6=c2h6, c2h4=c2h4, c2h2=c2h2,
            co=co, co2=co2, o2=o2, n2=n2,
        )

    def register_sample(self, dto: CreateSampleDTO) -> Sample:
        """Registra una nueva muestra de aceite en el sistema.

        Construye la entidad ``Sample`` con ``diagnosis_date`` igual a la
        fecha actual del sistema.

        Args:
            dto: Datos de la muestra a crear.

        Returns:
            Entidad con el ``id`` asignado por la persistencia.

        Raises:
            TransformerNotFoundError: Si el transformador no existe.
            DuplicateSampleCodeError: Si el codigo de muestra ya esta en uso.
            InvalidGasValueError: Si algun gas tiene valor invalido.
        """
        self._validate_transformer_exists(dto.transformer_id)
        gas_reading = self._build_gas_reading(
            h2=dto.h2, ch4=dto.ch4, c2h6=dto.c2h6, c2h4=dto.c2h4,
            c2h2=dto.c2h2, co=dto.co, co2=dto.co2, o2=dto.o2, n2=dto.n2,
        )
        sample = Sample(
            sample_code=dto.sample_code,
            transformer_id=dto.transformer_id,
            extraction_date=dto.extraction_date,
            gas_reading=gas_reading,
        )
        return self._sample_repo.create(sample)

    def list_samples(self) -> list[Sample]:
        """Retorna todas las muestras registradas.

        Returns:
            Lista de muestras, puede estar vacia.
        """
        return self._sample_repo.get_all()

    def get_sample(self, sample_id: int) -> Sample:
        """Obtiene una muestra por su ID.

        Args:
            sample_id: Identificador de la muestra.

        Returns:
            Entidad de la muestra encontrada.

        Raises:
            SampleNotFoundError: Si no existe.
        """
        sample = self._sample_repo.get_by_id(sample_id)
        if sample is None:
            raise SampleNotFoundError(sample_id)
        return sample

    def list_samples_by_transformer(self, transformer_id: int) -> list[Sample]:
        """Retorna todas las muestras de un transformador especifico.

        Args:
            transformer_id: ID del transformador.

        Returns:
            Lista de muestras del transformador.

        Raises:
            TransformerNotFoundError: Si el transformador no existe.
        """
        self._validate_transformer_exists(transformer_id)
        return self._sample_repo.get_by_transformer_id(transformer_id)

    def update_sample(self, dto: UpdateSampleDTO) -> Sample:
        """Actualiza los datos de una muestra existente.

        Args:
            dto: Datos actualizados incluyendo el ID.

        Returns:
            Entidad actualizada.

        Raises:
            SampleNotFoundError: Si la muestra no existe.
            TransformerNotFoundError: Si el transformador no existe.
            DuplicateSampleCodeError: Si el nuevo codigo ya esta en uso.
            InvalidGasValueError: Si algun gas tiene valor invalido.
        """
        self._validate_transformer_exists(dto.transformer_id)
        gas_reading = self._build_gas_reading(
            h2=dto.h2, ch4=dto.ch4, c2h6=dto.c2h6, c2h4=dto.c2h4,
            c2h2=dto.c2h2, co=dto.co, co2=dto.co2, o2=dto.o2, n2=dto.n2,
        )
        sample = Sample(
            sample_code=dto.sample_code,
            transformer_id=dto.transformer_id,
            extraction_date=dto.extraction_date,
            gas_reading=gas_reading,
            diagnosis_date=dto.diagnosis_date,
            id=dto.id,
        )
        return self._sample_repo.update(sample)

    def remove_sample(self, sample_id: int) -> None:
        """Elimina una muestra por su identificador.

        Args:
            sample_id: ID de la muestra a eliminar.

        Raises:
            SampleNotFoundError: Si no existe.
        """
        self._sample_repo.delete(sample_id)
