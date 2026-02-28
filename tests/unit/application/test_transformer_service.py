"""Tests unitarios para TransformerService.

Utiliza mocks del repositorio para verificar que el servicio orquesta
correctamente las operaciones CRUD sin depender de la infraestructura.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.dga.application.dto.transformer_dto import (
    CreateTransformerDTO,
    UpdateTransformerDTO,
)
from src.dga.application.services.transformer_service import TransformerService
from src.dga.domain.exceptions import TransformerNotFoundError
from src.dga.domain.models.transformer import Transformer


@pytest.fixture()
def mock_repo() -> MagicMock:
    """Crea un mock del puerto TransformerRepository."""
    return MagicMock()


@pytest.fixture()
def service(mock_repo: MagicMock) -> TransformerService:
    """Instancia el servicio con el repositorio mockeado."""
    return TransformerService(repository=mock_repo)


class TestTransformerService:
    """Suite de tests para el servicio de transformadores."""

    def test_register_creates_entity_and_calls_repo(
        self, service: TransformerService, mock_repo: MagicMock,
    ) -> None:
        """register_transformer construye la entidad y llama a create."""
        mock_repo.create.return_value = Transformer(name="T-01", id=1)
        dto = CreateTransformerDTO(name="T-01")

        result = service.register_transformer(dto)

        mock_repo.create.assert_called_once()
        assert result.id == 1
        assert result.name == "T-01"

    def test_list_delegates_to_repo(
        self, service: TransformerService, mock_repo: MagicMock,
    ) -> None:
        """list_transformers delega al metodo get_all del repositorio."""
        mock_repo.get_all.return_value = [
            Transformer(name="T-01", id=1),
            Transformer(name="T-02", id=2),
        ]
        result = service.list_transformers()

        mock_repo.get_all.assert_called_once()
        assert len(result) == 2

    def test_get_existing_returns_entity(
        self, service: TransformerService, mock_repo: MagicMock,
    ) -> None:
        """get_transformer retorna la entidad si existe."""
        mock_repo.get_by_id.return_value = Transformer(name="T-01", id=1)

        result = service.get_transformer(1)

        mock_repo.get_by_id.assert_called_once_with(1)
        assert result.name == "T-01"

    def test_get_nonexistent_raises_error(
        self, service: TransformerService, mock_repo: MagicMock,
    ) -> None:
        """get_transformer lanza error si no existe."""
        mock_repo.get_by_id.return_value = None

        with pytest.raises(TransformerNotFoundError):
            service.get_transformer(999)

    def test_update_constructs_entity_and_calls_repo(
        self, service: TransformerService, mock_repo: MagicMock,
    ) -> None:
        """update_transformer construye la entidad y llama a update."""
        mock_repo.update.return_value = Transformer(name="T-01-mod", id=1)
        dto = UpdateTransformerDTO(id=1, name="T-01-mod")

        result = service.update_transformer(dto)

        mock_repo.update.assert_called_once()
        assert result.name == "T-01-mod"

    def test_remove_delegates_to_repo(
        self, service: TransformerService, mock_repo: MagicMock,
    ) -> None:
        """remove_transformer delega al metodo delete del repositorio."""
        service.remove_transformer(1)
        mock_repo.delete.assert_called_once_with(1)
