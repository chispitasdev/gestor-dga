"""Tests unitarios para el diagnostico unificado (Fase 4).

Cubre:
    - UnifiedDiagnosisResult: estructura de datos
    - UnifiedDiagnosisService: diagnose, diagnose_batch, compare
    - Formateo de reportes y tablas comparativas
    - Comportamiento sin modelo de IA entrenado
"""

from __future__ import annotations

import tempfile
from datetime import date

import numpy as np
import pytest

from src.dga.domain.models.gas_reading import GasReading
from src.dga.domain.models.sample import Sample
from src.dga.domain.models.fault_type import FaultType
from src.dga.domain.ports.sample_repository import SampleRepository
from src.dga.application.services.normative_diagnosis_service import (
    NormativeDiagnosisService,
)
from src.dga.application.services.ai_engine.ai_service import AIService
from src.dga.application.services.ai_engine.data_preparation import (
    extract_features,
)
from src.dga.application.services.unified_diagnosis_service import (
    UnifiedDiagnosisResult,
    UnifiedDiagnosisService,
    ComparisonSummary,
)


# ================================================================== #
#  Fixtures
# ================================================================== #

def _reading_normal() -> GasReading:
    return GasReading(h2=15, ch4=5, c2h6=3, c2h4=2, c2h2=0, co=200, co2=1500, o2=20000, n2=55000)


def _reading_d2() -> GasReading:
    return GasReading(h2=1500, ch4=200, c2h6=60, c2h4=400, c2h2=500, co=300, co2=1200, o2=17000, n2=48000)


def _reading_t3() -> GasReading:
    return GasReading(h2=300, ch4=400, c2h6=150, c2h4=1200, c2h2=15, co=600, co2=5000, o2=16000, n2=48000)


def _make_sample(sid: int, reading: GasReading) -> Sample:
    return Sample(
        sample_code=f"UNI-{sid:04d}",
        transformer_id=1,
        extraction_date=date(2024, 6, 15),
        gas_reading=reading,
        id=sid,
    )


def _make_varied_samples(n_per_type: int = 8) -> list[Sample]:
    """Genera muestras sinteticas variadas para entrenamiento."""
    rng = np.random.RandomState(42)
    bases = [
        _reading_normal(),
        _reading_d2(),
        _reading_t3(),
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
                sample_code=f"VAR-{sid:04d}",
                transformer_id=1,
                extraction_date=date(2024, 1, 1),
                gas_reading=gr,
                id=sid,
            ))
            sid += 1
    return samples


class _FakeRepo(SampleRepository):
    """Repositorio falso para tests."""

    def __init__(self, samples: list[Sample]) -> None:
        self._samples = samples

    def get_all(self) -> list[Sample]:
        return list(self._samples)

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


# ================================================================== #
#  Tests: sin modelo IA
# ================================================================== #

class TestUnifiedWithoutAI:
    """Tests del diagnostico unificado sin modelo IA entrenado."""

    def test_diagnose_without_ai_returns_normative_only(self) -> None:
        sample = _make_sample(1, _reading_d2())
        norm_svc = NormativeDiagnosisService()
        repo = _FakeRepo([sample])
        ai_svc = AIService(repo, norm_svc, model_dir=tempfile.mkdtemp())

        unified = UnifiedDiagnosisService(norm_svc, ai_svc)
        result = unified.diagnose(sample)

        assert result.normative is not None
        assert result.normative.consensus_fault is not None
        assert result.ai_fault is None
        assert result.agree is None

    def test_diagnose_batch_returns_list(self) -> None:
        samples = [
            _make_sample(1, _reading_normal()),
            _make_sample(2, _reading_d2()),
        ]
        norm_svc = NormativeDiagnosisService()
        repo = _FakeRepo(samples)
        ai_svc = AIService(repo, norm_svc, model_dir=tempfile.mkdtemp())

        unified = UnifiedDiagnosisService(norm_svc, ai_svc)
        results = unified.diagnose_batch(samples)

        assert len(results) == 2
        for r in results:
            assert isinstance(r, UnifiedDiagnosisResult)

    def test_compare_without_ai_zero_agreements(self) -> None:
        samples = [
            _make_sample(1, _reading_normal()),
            _make_sample(2, _reading_t3()),
        ]
        norm_svc = NormativeDiagnosisService()
        repo = _FakeRepo(samples)
        ai_svc = AIService(repo, norm_svc, model_dir=tempfile.mkdtemp())

        unified = UnifiedDiagnosisService(norm_svc, ai_svc)
        summary = unified.compare(samples)

        assert summary.total == 0  # Sin IA, ninguna es comparable
        assert summary.agreement_pct == 0.0


# ================================================================== #
#  Tests: con modelo IA entrenado
# ================================================================== #

class TestUnifiedWithAI:
    """Tests del diagnostico unificado con modelo IA entrenado."""

    @pytest.fixture
    def trained_services(self):
        """Crea servicios con IA entrenada."""
        train_samples = _make_varied_samples(n_per_type=10)
        norm_svc = NormativeDiagnosisService()
        tmpdir = tempfile.mkdtemp()
        repo = _FakeRepo(train_samples)
        ai_svc = AIService(repo, norm_svc, model_dir=tmpdir, n_folds=3)
        ai_svc.train(train_samples, save=True)
        return norm_svc, ai_svc

    def test_diagnose_with_ai_returns_both(self, trained_services) -> None:
        norm_svc, ai_svc = trained_services
        sample = _make_sample(999, _reading_d2())
        unified = UnifiedDiagnosisService(norm_svc, ai_svc)
        result = unified.diagnose(sample)

        assert result.normative is not None
        assert result.ai_fault is not None
        assert isinstance(result.ai_fault, FaultType)
        assert result.agree is not None
        assert isinstance(result.agree, bool)

    def test_diagnose_has_probabilities(self, trained_services) -> None:
        norm_svc, ai_svc = trained_services
        sample = _make_sample(999, _reading_t3())
        unified = UnifiedDiagnosisService(norm_svc, ai_svc)
        result = unified.diagnose(sample)

        assert result.ai_probabilities is not None
        assert len(result.ai_probabilities) > 0
        total = sum(result.ai_probabilities.values())
        assert abs(total - 1.0) < 0.02

    def test_compare_returns_summary(self, trained_services) -> None:
        norm_svc, ai_svc = trained_services
        samples = [
            _make_sample(1, _reading_normal()),
            _make_sample(2, _reading_d2()),
            _make_sample(3, _reading_t3()),
        ]
        unified = UnifiedDiagnosisService(norm_svc, ai_svc)
        summary = unified.compare(samples)

        assert isinstance(summary, ComparisonSummary)
        assert summary.total == 3
        assert summary.agreements + summary.disagreements == summary.total
        assert 0.0 <= summary.agreement_pct <= 100.0
        assert len(summary.details) == 3

    def test_agreement_when_same_fault(self, trained_services) -> None:
        norm_svc, ai_svc = trained_services
        unified = UnifiedDiagnosisService(norm_svc, ai_svc)
        # Usar una lectura muy extrema para alta confianza
        sample = _make_sample(999, _reading_d2())
        result = unified.diagnose(sample)
        # Verificar que agree es coherente con los valores
        if result.ai_fault == result.normative.consensus_fault:
            assert result.agree is True
        else:
            assert result.agree is False


# ================================================================== #
#  Tests: formateo
# ================================================================== #

class TestUnifiedFormatting:
    """Tests para el formateo de reportes."""

    def test_format_unified_report_without_ai(self) -> None:
        sample = _make_sample(1, _reading_normal())
        norm_svc = NormativeDiagnosisService()
        normative = norm_svc.diagnose_all(sample.gas_reading)

        result = UnifiedDiagnosisResult(
            sample=sample,
            normative=normative,
            ai_fault=None,
            ai_probabilities=None,
            agree=None,
        )
        report = UnifiedDiagnosisService.format_unified_report(result)

        assert "DIAGNOSTICO UNIFICADO" in report
        assert "UNI-0001" in report
        assert "Normativo" in report
        assert "No hay modelo" in report

    def test_format_unified_report_with_ai(self) -> None:
        sample = _make_sample(1, _reading_d2())
        norm_svc = NormativeDiagnosisService()
        normative = norm_svc.diagnose_all(sample.gas_reading)

        result = UnifiedDiagnosisResult(
            sample=sample,
            normative=normative,
            ai_fault=FaultType.D2,
            ai_probabilities={FaultType.D2: 0.85, FaultType.D1: 0.10, FaultType.T3: 0.05},
            agree=True,
        )
        report = UnifiedDiagnosisService.format_unified_report(result)

        assert "D2" in report
        assert "85.00%" in report
        assert "SI" in report

    def test_format_comparison_table(self) -> None:
        sample1 = _make_sample(1, _reading_normal())
        sample2 = _make_sample(2, _reading_d2())
        norm_svc = NormativeDiagnosisService()

        details = [
            UnifiedDiagnosisResult(
                sample=sample1,
                normative=norm_svc.diagnose_all(sample1.gas_reading),
                ai_fault=FaultType.N,
                agree=True,
            ),
            UnifiedDiagnosisResult(
                sample=sample2,
                normative=norm_svc.diagnose_all(sample2.gas_reading),
                ai_fault=FaultType.T3,
                agree=False,
            ),
        ]
        summary = ComparisonSummary(
            total=2, agreements=1, disagreements=1,
            agreement_pct=50.0, details=details,
        )
        table = UnifiedDiagnosisService.format_comparison_table(summary)

        assert "COMPARACION" in table
        assert "50.0%" in table
        assert "UNI-0001" in table
        assert "UNI-0002" in table

    def test_format_comparison_empty(self) -> None:
        summary = ComparisonSummary(
            total=0, agreements=0, disagreements=0,
            agreement_pct=0.0, details=[],
        )
        table = UnifiedDiagnosisService.format_comparison_table(summary)
        assert "COMPARACION" in table
