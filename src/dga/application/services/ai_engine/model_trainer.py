"""Entrenador de modelos de clasificacion para diagnostico DGA.

Entrena y compara 4 algoritmos de machine learning:
    1. Random Forest (RF)
    2. Support Vector Machine (SVM)
    3. K-Nearest Neighbors (KNN)
    4. Multi-Layer Perceptron (MLP / Red Neuronal)

Cada modelo se entrena con validacion cruzada estratificada y se
persiste en disco con joblib para uso posterior.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import cross_val_score, StratifiedKFold
import joblib

from src.dga.application.services.ai_engine.data_preparation import (
    FAULT_LABELS,
    FEATURE_NAMES,
)


@dataclass(frozen=True, slots=True)
class TrainedModel:
    """Representa un modelo entrenado con sus metricas.

    Attributes:
        name: Nombre del algoritmo.
        pipeline: Pipeline de sklearn (scaler + clasificador).
        cv_accuracy: Accuracy promedio en validacion cruzada.
        cv_std: Desviacion estandar de la accuracy en CV.
        cv_scores: Scores individuales por fold.
    """

    name: str
    pipeline: Pipeline
    cv_accuracy: float
    cv_std: float
    cv_scores: list[float]


@dataclass(frozen=True, slots=True)
class TrainingResult:
    """Resultado completo de una sesion de entrenamiento.

    Attributes:
        models: Lista de modelos entrenados, ordenados por accuracy.
        best_model: Modelo con mejor accuracy media en CV.
        feature_names: Nombres de features usados.
        label_names: Nombres de las clases.
        n_samples: Cantidad de muestras de entrenamiento.
        n_classes: Cantidad de clases distintas en los datos.
    """

    models: list[TrainedModel]
    best_model: TrainedModel
    feature_names: list[str]
    label_names: list[str]
    n_samples: int
    n_classes: int


def _build_pipelines() -> list[tuple[str, Pipeline]]:
    """Construye los 4 pipelines de clasificacion.

    Cada pipeline incluye StandardScaler + clasificador.
    Los hiperparametros son valores razonables para DGA.
    """
    return [
        (
            "Random Forest",
            Pipeline([
                ("scaler", StandardScaler()),
                ("clf", RandomForestClassifier(
                    n_estimators=200,
                    max_depth=None,
                    min_samples_split=3,
                    min_samples_leaf=1,
                    random_state=42,
                    n_jobs=-1,
                )),
            ]),
        ),
        (
            "SVM",
            Pipeline([
                ("scaler", StandardScaler()),
                ("clf", SVC(
                    kernel="rbf",
                    C=10.0,
                    gamma="scale",
                    random_state=42,
                    probability=True,
                )),
            ]),
        ),
        (
            "KNN",
            Pipeline([
                ("scaler", StandardScaler()),
                ("clf", KNeighborsClassifier(
                    n_neighbors=5,
                    weights="distance",
                    metric="euclidean",
                    n_jobs=-1,
                )),
            ]),
        ),
        (
            "MLP",
            Pipeline([
                ("scaler", StandardScaler()),
                ("clf", MLPClassifier(
                    hidden_layer_sizes=(64, 32),
                    activation="relu",
                    solver="adam",
                    max_iter=500,
                    random_state=42,
                    early_stopping=True,
                    validation_fraction=0.15,
                )),
            ]),
        ),
    ]


class ModelTrainer:
    """Entrenador que compara multiples algoritmos de ML.

    Realiza validacion cruzada estratificada, entrena cada modelo
    con todos los datos y persiste el mejor en disco.
    """

    def __init__(self, n_folds: int = 5) -> None:
        """Inicializa el entrenador.

        Args:
            n_folds: Numero de folds para validacion cruzada.
        """
        self._n_folds = n_folds

    def train_all(
        self,
        X: NDArray[np.float64],
        y: NDArray[np.int64],
    ) -> TrainingResult:
        """Entrena los 4 modelos y retorna resultados comparativos.

        Args:
            X: Matriz de features (n_samples, 9).
            y: Vector de etiquetas numericas.

        Returns:
            TrainingResult con todos los modelos y el mejor.

        Raises:
            ValueError: Si hay menos de n_folds muestras o menos de 2 clases.
        """
        n_samples = X.shape[0]
        unique_classes = np.unique(y)
        n_classes = len(unique_classes)

        if n_samples < self._n_folds:
            raise ValueError(
                f"Se necesitan al menos {self._n_folds} muestras para "
                f"validacion cruzada con {self._n_folds} folds. "
                f"Se tienen {n_samples}."
            )

        if n_classes < 2:
            raise ValueError(
                f"Se necesitan al menos 2 clases distintas para entrenar. "
                f"Se encontro solo {n_classes} clase."
            )

        # Ajustar folds si hay clases con pocas muestras
        min_class_count = min(np.bincount(y)[unique_classes])
        effective_folds = min(self._n_folds, min_class_count)
        if effective_folds < 2:
            effective_folds = 2

        cv = StratifiedKFold(
            n_splits=effective_folds, shuffle=True, random_state=42
        )

        trained: list[TrainedModel] = []

        for name, pipeline in _build_pipelines():
            # Validacion cruzada
            scores = cross_val_score(
                pipeline, X, y, cv=cv, scoring="accuracy", n_jobs=-1
            )

            # Entrenar con todos los datos
            pipeline.fit(X, y)

            trained.append(TrainedModel(
                name=name,
                pipeline=pipeline,
                cv_accuracy=round(float(np.mean(scores)), 4),
                cv_std=round(float(np.std(scores)), 4),
                cv_scores=[round(float(s), 4) for s in scores],
            ))

        # Ordenar por accuracy descendente
        trained.sort(key=lambda m: m.cv_accuracy, reverse=True)

        return TrainingResult(
            models=trained,
            best_model=trained[0],
            feature_names=FEATURE_NAMES,
            label_names=FAULT_LABELS,
            n_samples=n_samples,
            n_classes=n_classes,
        )

    @staticmethod
    def save_model(model: TrainedModel, path: str | Path) -> Path:
        """Persiste un modelo entrenado en disco con joblib.

        Args:
            model: Modelo a guardar.
            path: Ruta del archivo .joblib.

        Returns:
            Path absoluto del archivo guardado.
        """
        dest = Path(path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(model.pipeline, dest)
        return dest.resolve()

    @staticmethod
    def load_model(path: str | Path) -> Pipeline:
        """Carga un modelo desde disco.

        Args:
            path: Ruta del archivo .joblib.

        Returns:
            Pipeline de sklearn listo para predecir.

        Raises:
            FileNotFoundError: Si el archivo no existe.
        """
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Modelo no encontrado: {p}")
        return joblib.load(p)
