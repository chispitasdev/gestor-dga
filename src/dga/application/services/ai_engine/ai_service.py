"""Servicio de aplicacion del motor de IA.

Orquesta todo el flujo de machine learning:
    1. Prepara datos desde las muestras almacenadas.
    2. Entrena y compara 4 algoritmos.
    3. Evalua el mejor modelo.
    4. Clasifica nuevas lecturas de gases.
    5. Persiste / carga modelos entrenados.

Este servicio actua como fachada unica para la capa de presentacion.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from src.dga.domain.models.gas_reading import GasReading
from src.dga.domain.models.fault_type import FaultType
from src.dga.domain.models.sample import Sample
from src.dga.domain.ports.sample_repository import SampleRepository
from src.dga.application.services.normative_diagnosis_service import (
    NormativeDiagnosisService,
)
from src.dga.application.services.ai_engine.data_preparation import (
    prepare_dataset,
    PreparedDataset,
)
from src.dga.application.services.ai_engine.model_trainer import (
    ModelTrainer,
    TrainingResult,
)
from src.dga.application.services.ai_engine.model_evaluator import (
    ModelEvaluator,
    EvaluationResult,
)
from src.dga.application.services.ai_engine.fault_classifier import (
    FaultClassifier,
)


# Ruta por defecto para persistir modelos
DEFAULT_MODEL_DIR = Path("models")
DEFAULT_MODEL_NAME = "best_model.joblib"


class AIService:
    """Servicio de alto nivel para diagnostico DGA con IA.

    Coordina data_preparation, model_trainer, model_evaluator y
    fault_classifier en un flujo unificado.
    """

    def __init__(
        self,
        sample_repository: SampleRepository,
        normative_service: NormativeDiagnosisService,
        model_dir: str | Path = DEFAULT_MODEL_DIR,
        n_folds: int = 5,
    ) -> None:
        """Inicializa el servicio de IA.

        Args:
            sample_repository: Repositorio para obtener muestras.
            normative_service: Servicio normativo para auto-etiquetado.
            model_dir: Directorio donde persistir modelos.
            n_folds: Folds para validacion cruzada.
        """
        self._sample_repo = sample_repository
        self._normative = normative_service
        self._model_dir = Path(model_dir)
        self._n_folds = n_folds
        self._classifier: Optional[FaultClassifier] = None

    # ------------------------------------------------------------------ #
    #  Preparacion de datos
    # ------------------------------------------------------------------ #

    def prepare_data(
        self, samples: list[Sample] | None = None
    ) -> PreparedDataset:
        """Prepara el dataset para entrenamiento.

        Si no se pasan muestras, obtiene todas del repositorio.

        Args:
            samples: Lista de muestras (None = todas las del repo).

        Returns:
            PreparedDataset listo para entrenar.
        """
        if samples is None:
            samples = self._sample_repo.get_all()
        return prepare_dataset(samples, self._normative)

    # ------------------------------------------------------------------ #
    #  Entrenamiento
    # ------------------------------------------------------------------ #

    def train(
        self, samples: list[Sample] | None = None, save: bool = True
    ) -> TrainingResult:
        """Entrena los 4 modelos y opcionalmente persiste el mejor.

        Args:
            samples: Muestras para entrenar (None = todas del repo).
            save: Si True, guarda el mejor modelo en disco.

        Returns:
            TrainingResult con comparacion de los 4 modelos.

        Raises:
            ValueError: Si hay insuficientes muestras o clases.
        """
        dataset = self.prepare_data(samples)
        trainer = ModelTrainer(n_folds=self._n_folds)
        result = trainer.train_all(dataset.X, dataset.y)

        if save:
            model_path = self._model_dir / DEFAULT_MODEL_NAME
            trainer.save_model(result.best_model, model_path)

        # Cargar clasificador con el mejor modelo
        self._classifier = FaultClassifier(result.best_model.pipeline)

        return result

    # ------------------------------------------------------------------ #
    #  Evaluacion
    # ------------------------------------------------------------------ #

    def evaluate_all(
        self, samples: list[Sample] | None = None
    ) -> list[EvaluationResult]:
        """Evalua los 4 modelos con validacion cruzada.

        Args:
            samples: Muestras para evaluar (None = todas del repo).

        Returns:
            Lista de EvaluationResult, uno por modelo.
        """
        dataset = self.prepare_data(samples)
        evaluator = ModelEvaluator(n_folds=self._n_folds)

        from src.dga.application.services.ai_engine.model_trainer import (
            _build_pipelines,
        )

        results: list[EvaluationResult] = []
        for name, pipeline in _build_pipelines():
            ev = evaluator.evaluate(name, pipeline, dataset.X, dataset.y)
            results.append(ev)

        results.sort(key=lambda r: r.overall_accuracy, reverse=True)
        return results

    # ------------------------------------------------------------------ #
    #  Clasificacion
    # ------------------------------------------------------------------ #

    def classify(self, reading: GasReading) -> FaultType:
        """Clasifica una lectura de gases con el modelo cargado.

        Intenta usar el clasificador en memoria; si no hay uno,
        intenta cargar desde disco.

        Args:
            reading: Lectura de 9 gases.

        Returns:
            FaultType predicho.

        Raises:
            RuntimeError: Si no hay modelo entrenado ni persistido.
        """
        classifier = self._get_classifier()
        return classifier.classify(reading)

    def classify_with_proba(
        self, reading: GasReading
    ) -> tuple[FaultType, dict[FaultType, float]]:
        """Clasifica con probabilidades por clase.

        Args:
            reading: Lectura de 9 gases.

        Returns:
            Tupla (FaultType, dict de probabilidades).
        """
        classifier = self._get_classifier()
        return classifier.classify_with_probabilities(reading)

    def classify_batch(
        self, readings: list[GasReading]
    ) -> list[FaultType]:
        """Clasifica multiples lecturas.

        Args:
            readings: Lista de lecturas.

        Returns:
            Lista de FaultType predichos.
        """
        classifier = self._get_classifier()
        return classifier.classify_batch(readings)

    # ------------------------------------------------------------------ #
    #  Gestion de modelos
    # ------------------------------------------------------------------ #

    def has_model(self) -> bool:
        """Verifica si existe un modelo (en memoria o en disco)."""
        if self._classifier is not None:
            return True
        return (self._model_dir / DEFAULT_MODEL_NAME).exists()

    def load_model(self) -> None:
        """Carga el modelo persistido desde disco.

        Raises:
            FileNotFoundError: Si no hay modelo guardado.
        """
        path = self._model_dir / DEFAULT_MODEL_NAME
        self._classifier = FaultClassifier.from_file(path)

    def model_path(self) -> Path:
        """Retorna la ruta del modelo persistido."""
        return self._model_dir / DEFAULT_MODEL_NAME

    # ------------------------------------------------------------------ #
    #  Internos
    # ------------------------------------------------------------------ #

    def _get_classifier(self) -> FaultClassifier:
        """Obtiene el clasificador, cargandolo si es necesario."""
        if self._classifier is not None:
            return self._classifier

        path = self._model_dir / DEFAULT_MODEL_NAME
        if path.exists():
            self._classifier = FaultClassifier.from_file(path)
            return self._classifier

        raise RuntimeError(
            "No hay modelo de IA entrenado. "
            "Ejecute primero la opcion de entrenamiento."
        )
