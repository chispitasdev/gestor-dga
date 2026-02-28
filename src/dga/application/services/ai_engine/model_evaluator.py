"""Evaluador de modelos de clasificacion DGA.

Genera metricas detalladas para un modelo entrenado:
    - Accuracy, Precision, Recall, F1-Score por clase.
    - Matriz de confusion.
    - Reporte resumido formateado para el Capitulo 5 de la tesis.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import cross_val_predict, StratifiedKFold
from sklearn.pipeline import Pipeline

from src.dga.application.services.ai_engine.data_preparation import (
    FAULT_LABELS,
    INDEX_TO_FAULT,
)
from src.dga.domain.models.fault_type import FaultType


@dataclass(frozen=True, slots=True)
class ClassMetrics:
    """Metricas de una clase individual.

    Attributes:
        fault_type: Tipo de falla evaluado.
        precision: Precision (TP / (TP + FP)).
        recall: Recall (TP / (TP + FN)).
        f1_score: F1 (media harmonica de precision y recall).
        support: Numero de muestras reales de esta clase.
    """

    fault_type: FaultType
    precision: float
    recall: float
    f1_score: float
    support: int


@dataclass(frozen=True, slots=True)
class EvaluationResult:
    """Resultado completo de la evaluacion de un modelo.

    Attributes:
        model_name: Nombre del algoritmo evaluado.
        overall_accuracy: Accuracy global.
        macro_precision: Precision macro (promedio no ponderado).
        macro_recall: Recall macro.
        macro_f1: F1-Score macro.
        weighted_f1: F1-Score ponderado por soporte.
        class_metrics: Metricas por clase.
        confusion_matrix: Matriz de confusion (ndarray).
        label_names: Nombres de las etiquetas.
        n_samples: Total de muestras evaluadas.
    """

    model_name: str
    overall_accuracy: float
    macro_precision: float
    macro_recall: float
    macro_f1: float
    weighted_f1: float
    class_metrics: list[ClassMetrics]
    confusion_matrix: NDArray[np.int64]
    label_names: list[str]
    n_samples: int


class ModelEvaluator:
    """Evalua modelos de clasificacion DGA con validacion cruzada."""

    def __init__(self, n_folds: int = 5) -> None:
        self._n_folds = n_folds

    def evaluate(
        self,
        model_name: str,
        pipeline: Pipeline,
        X: NDArray[np.float64],
        y: NDArray[np.int64],
    ) -> EvaluationResult:
        """Evalua un modelo con predicciones de validacion cruzada.

        Usa ``cross_val_predict`` para obtener predicciones fuera de
        muestra (out-of-fold) y calcula metricas sobre ellas.

        Args:
            model_name: Nombre del algoritmo.
            pipeline: Pipeline de sklearn (debe estar sin entrenar o
                      se re-entrena internamente por CV).
            X: Matriz de features.
            y: Vector de etiquetas.

        Returns:
            EvaluationResult con todas las metricas.
        """
        unique_classes = np.unique(y)
        min_class_count = min(np.bincount(y)[unique_classes])
        effective_folds = min(self._n_folds, min_class_count)
        if effective_folds < 2:
            effective_folds = 2

        cv = StratifiedKFold(
            n_splits=effective_folds, shuffle=True, random_state=42
        )

        # Predicciones fuera de muestra
        y_pred = cross_val_predict(pipeline, X, y, cv=cv, n_jobs=-1)

        # Clases presentes en los datos
        present_labels = sorted(unique_classes)
        present_names = [FAULT_LABELS[i] for i in present_labels]

        # Metricas globales
        acc = round(float(accuracy_score(y, y_pred)), 4)
        macro_p = round(float(precision_score(
            y, y_pred, average="macro", zero_division=0
        )), 4)
        macro_r = round(float(recall_score(
            y, y_pred, average="macro", zero_division=0
        )), 4)
        macro_f = round(float(f1_score(
            y, y_pred, average="macro", zero_division=0
        )), 4)
        weighted_f = round(float(f1_score(
            y, y_pred, average="weighted", zero_division=0
        )), 4)

        # Metricas por clase
        report: dict = classification_report(  # type: ignore[assignment]
            y, y_pred,
            labels=present_labels,
            target_names=present_names,
            output_dict=True,
            zero_division=0,
        )

        class_metrics: list[ClassMetrics] = []
        for idx, name in zip(present_labels, present_names):
            r = report[name]
            ft = INDEX_TO_FAULT[int(idx)]
            class_metrics.append(ClassMetrics(
                fault_type=ft,
                precision=round(float(r["precision"]), 4),
                recall=round(float(r["recall"]), 4),
                f1_score=round(float(r["f1-score"]), 4),
                support=int(r["support"]),
            ))

        # Matriz de confusion
        cm = confusion_matrix(y, y_pred, labels=present_labels)

        return EvaluationResult(
            model_name=model_name,
            overall_accuracy=acc,
            macro_precision=macro_p,
            macro_recall=macro_r,
            macro_f1=macro_f,
            weighted_f1=weighted_f,
            class_metrics=class_metrics,
            confusion_matrix=cm,
            label_names=present_names,
            n_samples=len(y),
        )

    @staticmethod
    def format_report(result: EvaluationResult) -> str:
        """Formatea las metricas como texto tabular para consola / tesis.

        Args:
            result: Resultado de evaluacion.

        Returns:
            String con la tabla formateada.
        """
        lines: list[str] = []
        lines.append(f"\n{'='*60}")
        lines.append(f"  EVALUACION: {result.model_name}")
        lines.append(f"{'='*60}")
        lines.append(f"  Muestras totales : {result.n_samples}")
        lines.append(f"  Accuracy global  : {result.overall_accuracy:.2%}")
        lines.append(f"  Macro Precision  : {result.macro_precision:.2%}")
        lines.append(f"  Macro Recall     : {result.macro_recall:.2%}")
        lines.append(f"  Macro F1-Score   : {result.macro_f1:.2%}")
        lines.append(f"  Weighted F1      : {result.weighted_f1:.2%}")
        lines.append(f"{'-'*60}")

        # Tabla por clase
        header = f"  {'Clase':<20} {'Prec':>8} {'Recall':>8} {'F1':>8} {'N':>6}"
        lines.append(header)
        lines.append(f"  {'-'*52}")

        for cm in result.class_metrics:
            name = str(cm.fault_type).split(" – ")[0] if " – " in str(cm.fault_type) else cm.fault_type.name
            lines.append(
                f"  {name:<20} {cm.precision:>8.2%} "
                f"{cm.recall:>8.2%} {cm.f1_score:>8.2%} {cm.support:>6}"
            )

        lines.append(f"{'-'*60}")

        # Matriz de confusion
        lines.append("\n  Matriz de Confusion:")
        labels = result.label_names
        # Header
        pad = 8
        header_row = "  " + " " * pad
        for lbl in labels:
            short = lbl[:6]
            header_row += f"{short:>7}"
        lines.append(header_row)

        for i, row in enumerate(result.confusion_matrix):
            short = labels[i][:6]
            row_str = f"  {short:<{pad}}"
            for val in row:
                row_str += f"{val:>7}"
            lines.append(row_str)

        lines.append(f"{'='*60}\n")
        return "\n".join(lines)
