"""Tests unitarios para routers FastAPI sin levantar servidor HTTP.

Se prueban los handlers directamente, mockeando los servicios globales
inyectados en cada router para validar:
    - mapeo correcto de excepciones -> HTTP status.
    - formato basico de respuestas.
"""

from __future__ import annotations

from datetime import date
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from src.dga.domain.exceptions import (
    DuplicateTransformerError,
    TransformerNotFoundError,
)
from src.dga.infrastructure.api import ai_router
from src.dga.infrastructure.api import diagnosis_router
from src.dga.infrastructure.api import sample_router
from src.dga.infrastructure.api import transformer_router
from src.dga.infrastructure.api import validation_router
from src.dga.infrastructure.api.schemas import (
    GasReadingSchema,
    SampleCreate,
    TransformerCreate,
)


def test_transformer_create_maps_duplicate_error(monkeypatch) -> None:
    """POST /transformers -> 409 cuando el nombre ya existe."""

    class _Service:
        def register_transformer(self, dto):
            raise DuplicateTransformerError(dto.name)

    monkeypatch.setattr(transformer_router, "transformer_service", _Service())

    with pytest.raises(HTTPException) as exc:
        transformer_router.create_transformer(TransformerCreate(name="T-01"))

    assert exc.value.status_code == 409


def test_sample_create_maps_transformer_not_found(monkeypatch) -> None:
    """POST /samples -> 404 cuando no existe el transformador."""

    class _Service:
        def register_sample(self, _dto):
            raise TransformerNotFoundError(999)

    monkeypatch.setattr(sample_router, "sample_service", _Service())

    body = SampleCreate(
        sample_code="M-001",
        transformer_id=999,
        extraction_date=date(2025, 1, 1),
        h2=10, ch4=5, c2h6=3, c2h4=2, c2h2=1, co=100, co2=500, o2=1000, n2=5000,
    )

    with pytest.raises(HTTPException) as exc:
        sample_router.create_sample(body)

    assert exc.value.status_code == 404


def test_diagnosis_single_method_not_found(monkeypatch) -> None:
    """POST /diagnosis/normative/{method} -> 404 para metodo inexistente."""

    class _DiagService:
        @staticmethod
        def diagnose_single(_reading, _method_name):
            return None

        @staticmethod
        def available_methods():
            return ["IEEE C57.104-2019", "IEC 60599:2022"]

    monkeypatch.setattr(diagnosis_router, "diagnosis_service", _DiagService())

    body = GasReadingSchema(
        h2=10, ch4=5, c2h6=3, c2h4=2, c2h2=1, co=100, co2=500, o2=1000, n2=5000,
    )

    with pytest.raises(HTTPException) as exc:
        diagnosis_router.diagnose_single_method("inexistente", body)

    assert exc.value.status_code == 404


def test_ai_train_maps_value_error(monkeypatch) -> None:
    """POST /ai/train -> 400 cuando faltan muestras o clases."""

    class _AIService:
        @staticmethod
        def train(save=True):
            assert save is True
            raise ValueError("muestras insuficientes")

    monkeypatch.setattr(ai_router, "ai_service", _AIService())

    with pytest.raises(HTTPException) as exc:
        ai_router.train_models()

    assert exc.value.status_code == 400


def test_ai_train_success_response(monkeypatch) -> None:
    """POST /ai/train retorna estructura esperada en caso exitoso."""

    class _AIService:
        @staticmethod
        def train(save=True):
            assert save is True
            best = SimpleNamespace(name="Random Forest", cv_accuracy=0.95)
            models = [
                SimpleNamespace(name="Random Forest", cv_accuracy=0.95, cv_std=0.02),
                SimpleNamespace(name="SVM", cv_accuracy=0.90, cv_std=0.03),
            ]
            return SimpleNamespace(best_model=best, models=models)

    monkeypatch.setattr(ai_router, "ai_service", _AIService())

    resp = ai_router.train_models()
    assert resp.best_model == "Random Forest"
    assert len(resp.models) == 2


def test_validation_full_report_without_samples(monkeypatch) -> None:
    """GET /validation/full-report -> 400 cuando no hay muestras."""

    class _SampleService:
        @staticmethod
        def list_samples():
            return []

    monkeypatch.setattr(validation_router, "sample_service", _SampleService())

    with pytest.raises(HTTPException) as exc:
        validation_router.full_report()

    assert exc.value.status_code == 400
