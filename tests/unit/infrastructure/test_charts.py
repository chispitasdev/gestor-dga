"""Tests unitarios para los modulos de graficos (Fase 5).

Verifica que cada funcion de grafico:
    - Retorna un objeto Figure de matplotlib.
    - Guarda archivos PNG cuando se especifica save_path.
    - No falla con datos vacios o minimos.
"""

from __future__ import annotations

import tempfile
from datetime import date
from pathlib import Path

import numpy as np
import pytest
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from src.dga.domain.models.gas_reading import GasReading
from src.dga.domain.models.sample import Sample
from src.dga.application.services.normative_diagnosis_service import (
    NormativeDiagnosisService,
)
from src.dga.application.services.trend_service import TrendService, GasHistory
from src.dga.application.services.ai_engine.data_preparation import (
    prepare_dataset,
    extract_features,
)
from src.dga.application.services.ai_engine.model_trainer import (
    ModelTrainer,
    TrainingResult,
)
from src.dga.application.services.ai_engine.model_evaluator import (
    ModelEvaluator,
    EvaluationResult,
)
from src.dga.infrastructure.charts.duval_triangle_chart import (
    plot_duval_triangle,
    _ternary_to_cart,
)
from src.dga.infrastructure.charts.trend_chart import (
    plot_gas_trends,
    plot_gas_trends_individual,
)
from src.dga.infrastructure.charts.model_charts import (
    plot_confusion_matrix,
    plot_model_comparison,
    plot_class_metrics,
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


def _make_varied_samples(n_per_type: int = 8) -> list[Sample]:
    rng = np.random.RandomState(42)
    bases = [_reading_normal(), _reading_d2(), _reading_t3(),
             GasReading(h2=800, ch4=60, c2h6=5, c2h4=2, c2h2=1, co=100, co2=1000, o2=18000, n2=50000),
             GasReading(h2=50, ch4=100, c2h6=80, c2h4=10, c2h2=0, co=400, co2=3000, o2=20000, n2=55000),
             GasReading(h2=100, ch4=200, c2h6=100, c2h4=400, c2h2=5, co=500, co2=4000, o2=18000, n2=52000),
             GasReading(h2=200, ch4=50, c2h6=15, c2h4=80, c2h2=150, co=100, co2=900, o2=19000, n2=52000)]
    samples: list[Sample] = []
    sid = 1
    for reading in bases:
        vals = extract_features(reading)
        for _ in range(n_per_type):
            noisy = [max(0.0, v + rng.normal(0, max(1, v * 0.1))) for v in vals]
            gr = GasReading(h2=noisy[0], ch4=noisy[1], c2h6=noisy[2],
                            c2h4=noisy[3], c2h2=noisy[4], co=noisy[5],
                            co2=noisy[6], o2=noisy[7], n2=noisy[8])
            samples.append(Sample(sample_code=f"CH-{sid:04d}", transformer_id=1,
                                  extraction_date=date(2024, 1, 1), gas_reading=gr, id=sid))
            sid += 1
    return samples


# ================================================================== #
#  Tests: Ternary conversion
# ================================================================== #

class TestTernaryConversion:
    def test_pure_a(self) -> None:
        x, y = _ternary_to_cart(100, 0, 0)
        assert abs(x - 0.0) < 0.01
        assert abs(y) < 0.01 or y > 0

    def test_pure_b(self) -> None:
        x, y = _ternary_to_cart(0, 100, 0)
        assert abs(x - 1.0) < 0.01
        assert abs(y) < 0.01

    def test_pure_c(self) -> None:
        x, y = _ternary_to_cart(0, 0, 100)
        assert abs(x - 0.5) < 0.01
        assert y > 0.8


# ================================================================== #
#  Tests: Duval Triangle chart
# ================================================================== #

class TestDuvalTriangleChart:
    def test_returns_figure(self) -> None:
        fig = plot_duval_triangle([_reading_d2()])
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_with_multiple_readings(self) -> None:
        readings = [_reading_normal(), _reading_d2(), _reading_t3()]
        labels = ["Normal", "D2", "T3"]
        fig = plot_duval_triangle(readings, labels=labels)
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_empty_readings(self) -> None:
        fig = plot_duval_triangle([])
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_saves_png(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "duval.png"
            fig = plot_duval_triangle([_reading_d2()], save_path=path)
            assert path.exists()
            assert path.stat().st_size > 1000
            plt.close(fig)


# ================================================================== #
#  Tests: Trend charts
# ================================================================== #

class TestTrendCharts:
    @pytest.fixture
    def histories(self) -> list[GasHistory]:
        samples = [
            Sample(sample_code=f"T-{i}", transformer_id=1,
                   extraction_date=date(2024, 1, i + 1),
                   gas_reading=GasReading(
                       h2=10 + i * 5, ch4=5 + i * 2, c2h6=3 + i,
                       c2h4=2 + i * 3, c2h2=i * 0.5, co=200 + i * 10,
                       co2=1500 + i * 50, o2=20000, n2=55000),
                   id=i + 1)
            for i in range(5)
        ]
        return TrendService.build_gas_history(samples)

    def test_trend_returns_figure(self, histories) -> None:
        fig = plot_gas_trends(histories)
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_trend_saves_png(self, histories) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "trends.png"
            fig = plot_gas_trends(histories, save_path=path)
            assert path.exists()
            plt.close(fig)

    def test_individual_returns_figure(self, histories) -> None:
        fig = plot_gas_trends_individual(histories)
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_individual_saves_png(self, histories) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "ind.png"
            fig = plot_gas_trends_individual(histories, save_path=path)
            assert path.exists()
            plt.close(fig)

    def test_empty_histories(self) -> None:
        fig = plot_gas_trends([])
        assert isinstance(fig, Figure)
        plt.close(fig)


# ================================================================== #
#  Tests: Model charts
# ================================================================== #

class TestModelCharts:
    @pytest.fixture
    def training_result(self) -> TrainingResult:
        samples = _make_varied_samples(n_per_type=10)
        ds = prepare_dataset(samples, NormativeDiagnosisService())
        trainer = ModelTrainer(n_folds=3)
        return trainer.train_all(ds.X, ds.y)

    @pytest.fixture
    def evaluation_result(self) -> EvaluationResult:
        samples = _make_varied_samples(n_per_type=10)
        ds = prepare_dataset(samples, NormativeDiagnosisService())
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.preprocessing import StandardScaler
        from sklearn.pipeline import Pipeline
        pipe = Pipeline([("scaler", StandardScaler()),
                         ("clf", RandomForestClassifier(n_estimators=50, random_state=42))])
        evaluator = ModelEvaluator(n_folds=3)
        return evaluator.evaluate("RF Test", pipe, ds.X, ds.y)

    def test_confusion_matrix_returns_figure(self, evaluation_result) -> None:
        fig = plot_confusion_matrix(evaluation_result)
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_confusion_matrix_saves(self, evaluation_result) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "cm.png"
            fig = plot_confusion_matrix(evaluation_result, save_path=path)
            assert path.exists()
            plt.close(fig)

    def test_model_comparison_returns_figure(self, training_result) -> None:
        fig = plot_model_comparison(training_result)
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_model_comparison_saves(self, training_result) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "comp.png"
            fig = plot_model_comparison(training_result, save_path=path)
            assert path.exists()
            plt.close(fig)

    def test_class_metrics_returns_figure(self, evaluation_result) -> None:
        fig = plot_class_metrics(evaluation_result)
        assert isinstance(fig, Figure)
        plt.close(fig)

    def test_class_metrics_saves(self, evaluation_result) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "cls.png"
            fig = plot_class_metrics(evaluation_result, save_path=path)
            assert path.exists()
            plt.close(fig)
