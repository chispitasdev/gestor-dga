"""Tests unitarios para el motor de IA (Fase 3).

Cubre:
    - data_preparation: extract_features, auto_label, prepare_dataset
    - model_trainer: train_all, save/load
    - fault_classifier: classify, classify_batch
    - model_evaluator: evaluate, format_report
    - ai_service: flujo integrado

Usa datos sinteticos generados en las fixtures para evitar
dependencia de datos reales.
"""

from __future__ import annotations

import tempfile
from datetime import date
from pathlib import Path

import numpy as np
import pytest

from src.dga.domain.models.gas_reading import GasReading
from src.dga.domain.models.sample import Sample
from src.dga.domain.models.fault_type import FaultType
from src.dga.application.services.normative_diagnosis_service import (
    NormativeDiagnosisService,
)
from src.dga.application.services.ai_engine.data_preparation import (
    FAULT_LABELS,
    FAULT_TO_INDEX,
    INDEX_TO_FAULT,
    FEATURE_NAMES,
    PreparedDataset,
    extract_features,
    auto_label,
    prepare_dataset,
)
from src.dga.application.services.ai_engine.model_trainer import (
    ModelTrainer,
)
from src.dga.application.services.ai_engine.fault_classifier import (
    FaultClassifier,
)
from src.dga.application.services.ai_engine.model_evaluator import (
    ModelEvaluator,
)


# ================================================================== #
#  Fixtures: lecturas representativas de cada tipo de falla
# ================================================================== #

def _reading_normal() -> GasReading:
    """Lectura tipica de transformador en condicion normal."""
    return GasReading(h2=15, ch4=5, c2h6=3, c2h4=2, c2h2=0, co=200, co2=1500, o2=20000, n2=55000)


def _reading_pd() -> GasReading:
    """Descargas parciales: H2 alto, resto bajo, CH4 algo."""
    return GasReading(h2=800, ch4=60, c2h6=5, c2h4=2, c2h2=1, co=100, co2=1000, o2=18000, n2=50000)


def _reading_d1() -> GasReading:
    """Descarga baja energia: C2H2 alto relativo."""
    return GasReading(h2=200, ch4=50, c2h6=15, c2h4=80, c2h2=150, co=100, co2=900, o2=19000, n2=52000)


def _reading_d2() -> GasReading:
    """Descarga alta energia: C2H2 muy alto, H2 muy alto."""
    return GasReading(h2=1500, ch4=200, c2h6=60, c2h4=400, c2h2=500, co=300, co2=1200, o2=17000, n2=48000)


def _reading_t1() -> GasReading:
    """Termica < 300: CH4 y C2H6 predominan."""
    return GasReading(h2=50, ch4=100, c2h6=80, c2h4=10, c2h2=0, co=400, co2=3000, o2=20000, n2=55000)


def _reading_t2() -> GasReading:
    """Termica 300-700: C2H4 predomina."""
    return GasReading(h2=100, ch4=200, c2h6=100, c2h4=400, c2h2=5, co=500, co2=4000, o2=18000, n2=52000)


def _reading_t3() -> GasReading:
    """Termica > 700: C2H4 muy alto."""
    return GasReading(h2=300, ch4=400, c2h6=150, c2h4=1200, c2h2=15, co=600, co2=5000, o2=16000, n2=48000)


# Genera muestras sinteticas con variaciones aleatorias
def _make_samples(n_per_type: int = 8) -> list[Sample]:
    """Genera muestras sinteticas con pequenas variaciones.

    Crea n_per_type muestras por cada tipo de falla base,
    anadiendo ruido gaussiano para diversidad.
    """
    rng = np.random.RandomState(42)
    base_readings = [
        _reading_normal(),
        _reading_pd(),
        _reading_d1(),
        _reading_d2(),
        _reading_t1(),
        _reading_t2(),
        _reading_t3(),
    ]

    samples: list[Sample] = []
    sample_id = 1

    for reading in base_readings:
        values = extract_features(reading)
        for _ in range(n_per_type):
            noisy = [
                max(0.0, v + rng.normal(0, max(1, v * 0.1)))
                for v in values
            ]
            gr = GasReading(
                h2=noisy[0], ch4=noisy[1], c2h6=noisy[2],
                c2h4=noisy[3], c2h2=noisy[4], co=noisy[5],
                co2=noisy[6], o2=noisy[7], n2=noisy[8],
            )
            samples.append(Sample(
                sample_code=f"SYN-{sample_id:04d}",
                transformer_id=1,
                extraction_date=date(2024, 1, 1),
                gas_reading=gr,
                id=sample_id,
            ))
            sample_id += 1

    return samples


# ================================================================== #
#  Tests: data_preparation
# ================================================================== #

class TestDataPreparation:
    """Tests para el modulo de preparacion de datos."""

    def test_fault_labels_has_all_fault_types(self) -> None:
        assert len(FAULT_LABELS) == len(FaultType)
        for ft in FaultType:
            assert ft.name in FAULT_LABELS

    def test_fault_to_index_roundtrip(self) -> None:
        for name, idx in FAULT_TO_INDEX.items():
            assert INDEX_TO_FAULT[idx].name == name

    def test_feature_names_count(self) -> None:
        assert len(FEATURE_NAMES) == 9

    def test_extract_features_returns_9_floats(self) -> None:
        reading = _reading_normal()
        features = extract_features(reading)
        assert len(features) == 9
        assert all(isinstance(f, (int, float)) for f in features)

    def test_extract_features_order_matches_gas_reading(self) -> None:
        reading = _reading_t2()
        features = extract_features(reading)
        for i, name in enumerate(FEATURE_NAMES):
            assert features[i] == getattr(reading, name)

    def test_auto_label_returns_valid_fault_name(self) -> None:
        service = NormativeDiagnosisService()
        label = auto_label(_reading_d2(), service)
        assert label in FAULT_LABELS

    def test_prepare_dataset_empty(self) -> None:
        ds = prepare_dataset([], NormativeDiagnosisService())
        assert ds.X.shape == (0, 9)
        assert ds.y.shape == (0,)
        assert ds.fault_labels == []

    def test_prepare_dataset_with_samples(self) -> None:
        samples = _make_samples(n_per_type=3)
        ds = prepare_dataset(samples, NormativeDiagnosisService())
        assert ds.X.shape[0] == len(samples)
        assert ds.X.shape[1] == 9
        assert ds.y.shape[0] == len(samples)
        assert len(ds.fault_labels) == len(samples)
        assert len(ds.sample_ids) == len(samples)

    def test_prepare_dataset_without_service_labels_normal(self) -> None:
        """Sin servicio normativo, todas las etiquetas son 'N'."""
        reading = _reading_d2()
        sample = Sample(
            sample_code="TEST-001",
            transformer_id=1,
            extraction_date=date(2024, 1, 1),
            gas_reading=reading,
            id=1,
        )
        ds = prepare_dataset([sample], diagnosis_service=None)
        assert ds.fault_labels[0] == "N"


# ================================================================== #
#  Tests: model_trainer
# ================================================================== #

class TestModelTrainer:
    """Tests para el entrenador de modelos."""

    @pytest.fixture
    def dataset(self) -> PreparedDataset:
        samples = _make_samples(n_per_type=10)
        return prepare_dataset(samples, NormativeDiagnosisService())

    def test_train_all_returns_4_models(self, dataset: PreparedDataset) -> None:
        trainer = ModelTrainer(n_folds=3)
        result = trainer.train_all(dataset.X, dataset.y)
        assert len(result.models) == 4
        assert result.best_model is not None

    def test_models_sorted_by_accuracy(self, dataset: PreparedDataset) -> None:
        trainer = ModelTrainer(n_folds=3)
        result = trainer.train_all(dataset.X, dataset.y)
        accuracies = [m.cv_accuracy for m in result.models]
        assert accuracies == sorted(accuracies, reverse=True)

    def test_best_model_is_first(self, dataset: PreparedDataset) -> None:
        trainer = ModelTrainer(n_folds=3)
        result = trainer.train_all(dataset.X, dataset.y)
        assert result.best_model.name == result.models[0].name

    def test_trained_model_has_cv_scores(self, dataset: PreparedDataset) -> None:
        trainer = ModelTrainer(n_folds=3)
        result = trainer.train_all(dataset.X, dataset.y)
        for model in result.models:
            assert len(model.cv_scores) >= 2
            assert 0.0 <= model.cv_accuracy <= 1.0

    def test_training_result_metadata(self, dataset: PreparedDataset) -> None:
        trainer = ModelTrainer(n_folds=3)
        result = trainer.train_all(dataset.X, dataset.y)
        assert result.n_samples == dataset.X.shape[0]
        assert result.n_classes >= 2

    def test_save_and_load_model(self, dataset: PreparedDataset) -> None:
        trainer = ModelTrainer(n_folds=3)
        result = trainer.train_all(dataset.X, dataset.y)

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test_model.joblib"
            saved = trainer.save_model(result.best_model, path)
            assert saved.exists()

            loaded = trainer.load_model(path)
            # Debe poder predecir
            pred = loaded.predict(dataset.X[:5])
            assert len(pred) == 5

    def test_load_nonexistent_raises(self) -> None:
        with pytest.raises(FileNotFoundError):
            ModelTrainer.load_model("nonexistent_model.joblib")

    def test_too_few_samples_raises(self) -> None:
        X = np.array([[1, 2, 3, 4, 5, 6, 7, 8, 9]], dtype=np.float64)
        y = np.array([0], dtype=np.int64)
        trainer = ModelTrainer(n_folds=5)
        with pytest.raises(ValueError, match="al menos"):
            trainer.train_all(X, y)

    def test_single_class_raises(self) -> None:
        X = np.array([[1]*9, [2]*9, [3]*9, [4]*9, [5]*9], dtype=np.float64)
        y = np.array([0, 0, 0, 0, 0], dtype=np.int64)
        trainer = ModelTrainer(n_folds=3)
        with pytest.raises(ValueError, match="2 clases"):
            trainer.train_all(X, y)


# ================================================================== #
#  Tests: fault_classifier
# ================================================================== #

class TestFaultClassifier:
    """Tests para el clasificador de fallas."""

    @pytest.fixture
    def trained_pipeline(self):
        samples = _make_samples(n_per_type=10)
        ds = prepare_dataset(samples, NormativeDiagnosisService())
        trainer = ModelTrainer(n_folds=3)
        result = trainer.train_all(ds.X, ds.y)
        return result.best_model.pipeline

    def test_classify_returns_fault_type(self, trained_pipeline) -> None:
        clf = FaultClassifier(trained_pipeline)
        result = clf.classify(_reading_d2())
        assert isinstance(result, FaultType)

    def test_classify_batch_returns_list(self, trained_pipeline) -> None:
        clf = FaultClassifier(trained_pipeline)
        readings = [_reading_normal(), _reading_d1(), _reading_t3()]
        results = clf.classify_batch(readings)
        assert len(results) == 3
        for r in results:
            assert isinstance(r, FaultType)

    def test_classify_batch_empty(self, trained_pipeline) -> None:
        clf = FaultClassifier(trained_pipeline)
        assert clf.classify_batch([]) == []

    def test_classify_with_probabilities(self, trained_pipeline) -> None:
        clf = FaultClassifier(trained_pipeline)
        fault, probs = clf.classify_with_probabilities(_reading_t2())
        assert isinstance(fault, FaultType)
        assert isinstance(probs, dict)
        assert len(probs) > 0
        # Las probabilidades deben sumar ~1
        total = sum(probs.values())
        assert abs(total - 1.0) < 0.01

    def test_from_file_and_classify(self, trained_pipeline) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            import joblib
            path = Path(tmpdir) / "test.joblib"
            joblib.dump(trained_pipeline, path)

            clf = FaultClassifier.from_file(path)
            result = clf.classify(_reading_pd())
            assert isinstance(result, FaultType)

    def test_from_file_nonexistent_raises(self) -> None:
        with pytest.raises(FileNotFoundError):
            FaultClassifier.from_file("no_existe.joblib")


# ================================================================== #
#  Tests: model_evaluator
# ================================================================== #

class TestModelEvaluator:
    """Tests para el evaluador de modelos."""

    @pytest.fixture
    def dataset(self) -> PreparedDataset:
        samples = _make_samples(n_per_type=10)
        return prepare_dataset(samples, NormativeDiagnosisService())

    def test_evaluate_returns_result(self, dataset: PreparedDataset) -> None:
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.preprocessing import StandardScaler
        from sklearn.pipeline import Pipeline

        pipe = Pipeline([
            ("scaler", StandardScaler()),
            ("clf", RandomForestClassifier(n_estimators=50, random_state=42)),
        ])
        evaluator = ModelEvaluator(n_folds=3)
        result = evaluator.evaluate("Test RF", pipe, dataset.X, dataset.y)

        assert result.model_name == "Test RF"
        assert 0.0 <= result.overall_accuracy <= 1.0
        assert result.n_samples == dataset.X.shape[0]
        assert len(result.class_metrics) >= 2
        assert result.confusion_matrix.shape[0] == result.confusion_matrix.shape[1]

    def test_format_report_is_string(self, dataset: PreparedDataset) -> None:
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.preprocessing import StandardScaler
        from sklearn.pipeline import Pipeline

        pipe = Pipeline([
            ("scaler", StandardScaler()),
            ("clf", RandomForestClassifier(n_estimators=50, random_state=42)),
        ])
        evaluator = ModelEvaluator(n_folds=3)
        result = evaluator.evaluate("Test RF", pipe, dataset.X, dataset.y)
        report = ModelEvaluator.format_report(result)

        assert isinstance(report, str)
        assert "EVALUACION" in report
        assert "Test RF" in report
        assert "Accuracy" in report
        assert "Matriz de Confusion" in report


# ================================================================== #
#  Tests: indices y constantes
# ================================================================== #

class TestConstantConsistency:
    """Verifica consistencia de las constantes del motor de IA."""

    def test_index_to_fault_covers_all(self) -> None:
        for i in range(len(FaultType)):
            assert i in INDEX_TO_FAULT
            assert isinstance(INDEX_TO_FAULT[i], FaultType)

    def test_fault_to_index_covers_all(self) -> None:
        for ft in FaultType:
            assert ft.name in FAULT_TO_INDEX

    def test_index_fault_roundtrip(self) -> None:
        for ft in FaultType:
            idx = FAULT_TO_INDEX[ft.name]
            assert INDEX_TO_FAULT[idx] == ft
