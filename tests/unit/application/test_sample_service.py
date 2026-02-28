"""Tests unitarios para SampleService.

Utiliza mocks de ambos repositorios (muestras y transformadores) para
verificar la orquestacion correcta de las operaciones CRUD, incluyendo
la validacion de existencia del transformador asociado.
"""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

import pytest

from src.dga.application.dto.sample_dto import CreateSampleDTO, UpdateSampleDTO
from src.dga.application.services.sample_service import SampleService
from src.dga.domain.exceptions import (
    SampleNotFoundError,
    TransformerNotFoundError,
)
from src.dga.domain.models.gas_reading import GasReading
from src.dga.domain.models.sample import Sample
from src.dga.domain.models.transformer import Transformer


# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------

@pytest.fixture()
def mock_sample_repo() -> MagicMock:
    """Mock del puerto SampleRepository."""
    return MagicMock()


@pytest.fixture()
def mock_transformer_repo() -> MagicMock:
    """Mock del puerto TransformerRepository."""
    return MagicMock()


@pytest.fixture()
def service(
    mock_sample_repo: MagicMock,
    mock_transformer_repo: MagicMock,
) -> SampleService:
    """Instancia del servicio con repositorios mockeados."""
    return SampleService(mock_sample_repo, mock_transformer_repo)


def _gas_kwargs() -> dict[str, float]:
    """Retorna valores de gas validos para construir DTOs."""
    return {
        "h2": 10.0, "ch4": 5.0, "c2h6": 3.0,
        "c2h4": 2.0, "c2h2": 0.5, "co": 100.0,
        "co2": 500.0, "o2": 3000.0, "n2": 50000.0,
    }


def _sample_entity() -> Sample:
    """Retorna una entidad Sample valida para uso en mocks."""
    return Sample(
        id=1,
        sample_code="M-001",
        transformer_id=1,
        extraction_date=date(2025, 6, 15),
        gas_reading=GasReading(**_gas_kwargs()),
    )


# ----------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------

class TestSampleService:
    """Suite de tests para el servicio de muestras."""

    def test_register_validates_transformer_and_creates(
        self, service: SampleService,
        mock_sample_repo: MagicMock,
        mock_transformer_repo: MagicMock,
    ) -> None:
        """register_sample verifica que el transformador exista y crea."""
        mock_transformer_repo.get_by_id.return_value = Transformer(
            name="T-01", id=1,
        )
        mock_sample_repo.create.return_value = _sample_entity()

        dto = CreateSampleDTO(
            sample_code="M-001",
            transformer_id=1,
            extraction_date=date(2025, 6, 15),
            **_gas_kwargs(),
        )
        result = service.register_sample(dto)

        mock_transformer_repo.get_by_id.assert_called_once_with(1)
        mock_sample_repo.create.assert_called_once()
        assert result.id == 1

    def test_register_raises_if_transformer_missing(
        self, service: SampleService,
        mock_transformer_repo: MagicMock,
    ) -> None:
        """register_sample lanza error si el transformador no existe."""
        mock_transformer_repo.get_by_id.return_value = None

        dto = CreateSampleDTO(
            sample_code="M-002",
            transformer_id=999,
            extraction_date=date(2025, 6, 15),
            **_gas_kwargs(),
        )
        with pytest.raises(TransformerNotFoundError):
            service.register_sample(dto)

    def test_get_existing_sample(
        self, service: SampleService,
        mock_sample_repo: MagicMock,
    ) -> None:
        """get_sample retorna la entidad si existe."""
        mock_sample_repo.get_by_id.return_value = _sample_entity()

        result = service.get_sample(1)

        assert result.sample_code == "M-001"

    def test_get_nonexistent_sample_raises_error(
        self, service: SampleService,
        mock_sample_repo: MagicMock,
    ) -> None:
        """get_sample lanza error si no existe."""
        mock_sample_repo.get_by_id.return_value = None

        with pytest.raises(SampleNotFoundError):
            service.get_sample(999)

    def test_list_delegates_to_repo(
        self, service: SampleService,
        mock_sample_repo: MagicMock,
    ) -> None:
        """list_samples delega al repositorio."""
        mock_sample_repo.get_all.return_value = [_sample_entity()]

        result = service.list_samples()

        mock_sample_repo.get_all.assert_called_once()
        assert len(result) == 1

    def test_list_by_transformer_validates_and_filters(
        self, service: SampleService,
        mock_sample_repo: MagicMock,
        mock_transformer_repo: MagicMock,
    ) -> None:
        """list_samples_by_transformer valida el trafo y filtra."""
        mock_transformer_repo.get_by_id.return_value = Transformer(
            name="T-01", id=1,
        )
        mock_sample_repo.get_by_transformer_id.return_value = [
            _sample_entity(),
        ]

        result = service.list_samples_by_transformer(1)

        mock_transformer_repo.get_by_id.assert_called_once_with(1)
        assert len(result) == 1

    def test_update_validates_transformer_and_updates(
        self, service: SampleService,
        mock_sample_repo: MagicMock,
        mock_transformer_repo: MagicMock,
    ) -> None:
        """update_sample verifica el trafo y actualiza."""
        mock_transformer_repo.get_by_id.return_value = Transformer(
            name="T-01", id=1,
        )
        mock_sample_repo.update.return_value = _sample_entity()

        dto = UpdateSampleDTO(
            id=1,
            sample_code="M-001",
            transformer_id=1,
            extraction_date=date(2025, 6, 15),
            diagnosis_date=date.today(),
            **_gas_kwargs(),
        )
        result = service.update_sample(dto)

        mock_sample_repo.update.assert_called_once()
        assert result.id == 1

    def test_remove_delegates_to_repo(
        self, service: SampleService,
        mock_sample_repo: MagicMock,
    ) -> None:
        """remove_sample delega al repositorio."""
        service.remove_sample(1)
        mock_sample_repo.delete.assert_called_once_with(1)
