"""Tests unitarios para el servicio de validacion (Fase 6).

Verifica:
    - Resumen estadistico del dataset.
    - Tabla comparativa de modelos.
    - Exportacion a CSV.
    - Formateo de reportes.
"""

from __future__ import annotations

import tempfile
from datetime import date
from pathlib import Path

import numpy as np
import pytest

from src.dga.domain.models.gas_reading import GasReading
from src.dga.domain.models.sample import Sample
from src.dga.domain.ports.sample_repository import SampleRepository
from src.dga.application.services.normative_diagnosis_service import (
    NormativeDiagnosisService,
)
from src.dga.application.services.ai_engine.ai_service import AIService
from src.dga.application.services.ai_engine.data_preparation import (
    extract_features,
)
from src.dga.application.services.unified_diagnosis_service import (
    UnifiedDiagnosisService,
)
from src.dga.application.services.validation_service import (
    ValidationService,
    DatasetSummary,
    ModelComparisonRow,
)


# ================================================================== #
#  Fixtures y helpers
# ================================================================== #


class _FakeRepo(SampleRepository):
    """Repositorio falso para pruebas."""

    def __init__(self, samples: list[Sample] | None = None) -> None:
        self._samples = list(samples) if samples else []

    def get_all(self) -> list[Sample]:
        return self._samples

    def get_by_id(self, sample_id: int) -> Sample | None:
        return next((s for s in self._samples if s.id == sample_id), None)

    def get_by_transformer_id(self, transformer_id: int) -> list[Sample]:
        return [s for s in self._samples if s.transformer_id == transformer_id]

    def create(self, sample: Sample) -> Sample:
        return sample

    def update(self, sample: Sample) -> Sample:
        return sample

    def delete(self, sample_id: int) -> None:
        pass

    def delete_by_transformer_id(self, tid: int) -> None:
        pass


def _reading_normal() -> GasReading:
    return GasReading(h2=15, ch4=5, c2h6=3, c2h4=2, c2h2=0, co=200, co2=1500, o2=20000, n2=55000)

def _reading_d2() -> GasReading:
    return GasReading(h2=1500, ch4=200, c2h6=60, c2h4=400, c2h2=500, co=300, co2=1200, o2=17000, n2=48000)

def _reading_t3() -> GasReading:
    return GasReading(h2=300, ch4=400, c2h6=150, c2h4=1200, c2h2=15, co=600, co2=5000, o2=16000, n2=48000)


def _make_varied_samples(n_per_type: int = 8) -> list[Sample]:
    """Genera un dataset variado con ruido para pruebas."""
    rng = np.random.RandomState(42)
    bases = [
        _reading_normal(), _reading_d2(), _reading_t3(),
        GasReading(h2=800, ch4=60, c2h6=5, c2h4=2, c2h2=1, co=100, co2=1000, o2=18000, n2=50000),
        GasReading(h2=50, ch4=100, c2h6=80, c2h4=10, c2h2=0, co=400, co2=3000, o2=20000, n2=55000),
        GasReading(h2=100, ch4=200, c2h6=100, c2h4=400, c2h2=5, co=500, co2=4000, o2=18000, n2=52000),
        GasReading(h2=200, ch4=50, c2h6=15, c2h4=80, c2h2=150, co=100, co2=900, o2=19000, n2=52000),
    ]
    samples: list[Sample] = []
    sid = 1
    for reading in bases:
        vals = extract_features(reading)
        for _ in range(n_per_type):
            noisy = [max(0.0, v + rng.normal(0, max(1, v * 0.1))) for v in vals]
            gr = GasReading(
                h2=noisy[0], ch4=noisy[1], c2h6=noisy[2],
                c2h4=noisy[3], c2h2=noisy[4], co=noisy[5],
                co2=noisy[6], o2=noisy[7], n2=noisy[8],
            )
            samples.append(Sample(
                sample_code=f"VAL-{sid:04d}", transformer_id=(sid % 3) + 1,
                extraction_date=date(2024, 1, max(1, min(28, sid))),
                gas_reading=gr, id=sid,
            ))
            sid += 1
    return samples


@pytest.fixture
def normative_svc() -> NormativeDiagnosisService:
    return NormativeDiagnosisService()


@pytest.fixture
def varied_samples() -> list[Sample]:
    return _make_varied_samples(n_per_type=10)


@pytest.fixture
def validation_svc(normative_svc, varied_samples):
    repo = _FakeRepo(varied_samples)
    ai = AIService(repo, normative_svc)
    unified = UnifiedDiagnosisService(normative_svc, ai)
    return ValidationService(normative_svc, ai, unified)


# ================================================================== #
#  Tests: Dataset Summary
# ================================================================== #

class TestDatasetSummary:
    def test_empty_dataset(self, normative_svc) -> None:
        repo = _FakeRepo()
        ai = AIService(repo, normative_svc)
        unified = UnifiedDiagnosisService(normative_svc, ai)
        svc = ValidationService(normative_svc, ai, unified)
        summary = svc.build_dataset_summary([])
        assert summary.total_samples == 0
        assert summary.date_range is None
        assert summary.gas_stats == []

    def test_summary_has_correct_total(self, validation_svc, varied_samples) -> None:
        summary = validation_svc.build_dataset_summary(varied_samples)
        assert summary.total_samples == len(varied_samples)

    def test_summary_has_gas_stats(self, validation_svc, varied_samples) -> None:
        summary = validation_svc.build_dataset_summary(varied_samples)
        assert len(summary.gas_stats) == 9  # 9 gases

    def test_gas_stats_contain_all_fields(self, validation_svc, varied_samples) -> None:
        summary = validation_svc.build_dataset_summary(varied_samples)
        for gs in summary.gas_stats:
            assert gs.min <= gs.mean <= gs.max
            assert gs.std >= 0
            assert gs.median >= gs.min

    def test_fault_distribution_sums_to_total(self, validation_svc, varied_samples) -> None:
        summary = validation_svc.build_dataset_summary(varied_samples)
        total = sum(summary.fault_distribution.values())
        assert total == len(varied_samples)

    def test_date_range_is_correct(self, validation_svc, varied_samples) -> None:
        summary = validation_svc.build_dataset_summary(varied_samples)
        assert summary.date_range is not None
        assert summary.date_range[0] <= summary.date_range[1]

    def test_n_transformers(self, validation_svc, varied_samples) -> None:
        summary = validation_svc.build_dataset_summary(varied_samples)
        expected = len({s.transformer_id for s in varied_samples})
        assert summary.n_transformers == expected


# ================================================================== #
#  Tests: Formateo
# ================================================================== #

class TestFormatting:
    def test_format_dataset_summary(self, validation_svc, varied_samples) -> None:
        summary = validation_svc.build_dataset_summary(varied_samples)
        text = ValidationService.format_dataset_summary(summary)
        assert "RESUMEN DEL DATASET" in text
        assert str(summary.total_samples) in text

    def test_format_model_comparison(self) -> None:
        rows = [
            ModelComparisonRow("RF", 0.95, 0.93, 0.92, 0.92, 0.94),
            ModelComparisonRow("SVM", 0.90, 0.88, 0.87, 0.87, 0.89),
        ]
        text = ValidationService.format_model_comparison(rows)
        assert "COMPARACION DE MODELOS" in text
        assert "RF" in text
        assert "SVM" in text

    def test_format_empty_dataset(self) -> None:
        summary = DatasetSummary(
            total_samples=0, date_range=None,
            fault_distribution={}, gas_stats=[], n_transformers=0,
        )
        text = ValidationService.format_dataset_summary(summary)
        assert "0" in text
        assert "(sin datos)" in text


# ================================================================== #
#  Tests: Exportacion CSV
# ================================================================== #

class TestCSVExport:
    def test_export_dataset_summary_creates_files(self, validation_svc, varied_samples) -> None:
        summary = validation_svc.build_dataset_summary(varied_samples)
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir) / "dataset"
            ValidationService.export_dataset_summary_csv(summary, base)
            assert (Path(tmpdir) / "dataset_fallas.csv").exists()
            assert (Path(tmpdir) / "dataset_gases.csv").exists()

    def test_export_model_comparison_creates_file(self) -> None:
        rows = [
            ModelComparisonRow("RF", 0.95, 0.93, 0.92, 0.92, 0.94),
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "models.csv"
            result_path = ValidationService.export_model_comparison_csv(rows, path)
            assert result_path.exists()
            content = result_path.read_text(encoding="utf-8")
            assert "RF" in content
            assert "0.95" in content

    def test_export_class_metrics_creates_file(self, validation_svc, varied_samples) -> None:
        _, evals = validation_svc.evaluate_all_models(varied_samples)
        assert evals, "Should have evaluation results"
        best = evals[0]
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "class_metrics.csv"
            result_path = ValidationService.export_class_metrics_csv(best, path)
            assert result_path.exists()
            content = result_path.read_text(encoding="utf-8")
            assert "Precision" in content

    def test_dataset_summary_csv_contains_all_gases(self, validation_svc, varied_samples) -> None:
        summary = validation_svc.build_dataset_summary(varied_samples)
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir) / "ds"
            ValidationService.export_dataset_summary_csv(summary, base)
            content = (Path(tmpdir) / "ds_gases.csv").read_text(encoding="utf-8")
            for gas in ["h2", "ch4", "c2h6", "c2h4", "c2h2", "co", "co2", "o2", "n2"]:
                assert gas in content


# ================================================================== #
#  Tests: Model evaluation (integration-level)
# ================================================================== #

class TestModelEvaluation:
    def test_evaluate_all_returns_4_rows(self, validation_svc, varied_samples) -> None:
        rows, evals = validation_svc.evaluate_all_models(varied_samples)
        assert len(rows) == 4
        assert len(evals) == 4

    def test_rows_sorted_by_accuracy(self, validation_svc, varied_samples) -> None:
        rows, _ = validation_svc.evaluate_all_models(varied_samples)
        accuracies = [r.accuracy for r in rows]
        assert accuracies == sorted(accuracies, reverse=True)

    def test_all_metrics_in_range(self, validation_svc, varied_samples) -> None:
        rows, _ = validation_svc.evaluate_all_models(varied_samples)
        for r in rows:
            assert 0.0 <= r.accuracy <= 1.0
            assert 0.0 <= r.macro_precision <= 1.0
            assert 0.0 <= r.macro_recall <= 1.0
            assert 0.0 <= r.macro_f1 <= 1.0
            assert 0.0 <= r.weighted_f1 <= 1.0
