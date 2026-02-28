"""Graficos de evaluacion de modelos de IA.

Genera:
    - Matriz de confusion como heatmap.
    - Grafico de barras comparando accuracy de los modelos.
    - Grafico de barras agrupadas con precision/recall/F1 por clase.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from src.dga.application.services.ai_engine.model_evaluator import (
    EvaluationResult,
)
from src.dga.application.services.ai_engine.model_trainer import (
    TrainingResult,
)


def plot_confusion_matrix(
    result: EvaluationResult,
    title: str | None = None,
    save_path: str | Path | None = None,
    figsize: tuple[float, float] = (8, 6),
) -> Figure:
    """Genera un heatmap de la matriz de confusion.

    Args:
        result: EvaluationResult con confusion_matrix y label_names.
        title: Titulo del grafico (defecto: usa model_name).
        save_path: Ruta para guardar la imagen.
        figsize: Tamano de la figura.

    Returns:
        Objeto Figure de matplotlib.
    """
    cm = result.confusion_matrix
    labels = result.label_names

    if title is None:
        title = f"Matriz de Confusion — {result.model_name}"

    fig, ax = plt.subplots(1, 1, figsize=figsize)

    im = ax.imshow(cm, interpolation="nearest", cmap="Blues")
    fig.colorbar(im, ax=ax, shrink=0.8)

    n = len(labels)
    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=9)
    ax.set_yticklabels(labels, fontsize=9)

    # Anotar valores en celdas
    thresh = cm.max() / 2
    for i in range(n):
        for j in range(n):
            ax.text(
                j, i, str(cm[i, j]),
                ha="center", va="center",
                color="white" if cm[i, j] > thresh else "black",
                fontsize=10, fontweight="bold",
            )

    ax.set_xlabel("Predicho", fontsize=11)
    ax.set_ylabel("Real", fontsize=11)
    ax.set_title(title, fontsize=13, fontweight="bold")

    fig.tight_layout()

    if save_path:
        p = Path(save_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(p, dpi=150, bbox_inches="tight")

    return fig


def plot_model_comparison(
    training_result: TrainingResult,
    title: str = "Comparacion de Modelos — Accuracy (CV)",
    save_path: str | Path | None = None,
    figsize: tuple[float, float] = (10, 5),
) -> Figure:
    """Genera un grafico de barras comparando la accuracy de los modelos.

    Args:
        training_result: TrainingResult con lista de modelos entrenados.
        title: Titulo del grafico.
        save_path: Ruta para guardar.
        figsize: Tamano de la figura.

    Returns:
        Objeto Figure de matplotlib.
    """
    models = training_result.models
    names = [m.name for m in models]
    accs = [m.cv_accuracy for m in models]
    stds = [m.cv_std for m in models]

    colors = ["#4CAF50", "#2196F3", "#FF9800", "#9C27B0"]
    while len(colors) < len(models):
        colors.append("#607D8B")

    fig, ax = plt.subplots(1, 1, figsize=figsize)

    bars = ax.bar(
        names, accs,
        yerr=stds, capsize=6,
        color=colors[:len(models)],
        edgecolor="black", linewidth=0.8,
        alpha=0.85,
    )

    # Anotar valores sobre las barras
    for bar, acc, std in zip(bars, accs, stds):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + std + 0.005,
            f"{acc:.2%}",
            ha="center", va="bottom",
            fontsize=10, fontweight="bold",
        )

    # Linea del mejor
    best_acc = max(accs)
    ax.axhline(y=best_acc, color="red", linestyle="--", alpha=0.5, linewidth=1)

    ax.set_ylabel("Accuracy", fontsize=11)
    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.set_ylim(0, min(1.08, max(accs) + max(stds) + 0.08))
    ax.grid(axis="y", alpha=0.3)

    fig.tight_layout()

    if save_path:
        p = Path(save_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(p, dpi=150, bbox_inches="tight")

    return fig


def plot_class_metrics(
    result: EvaluationResult,
    title: str | None = None,
    save_path: str | Path | None = None,
    figsize: tuple[float, float] = (12, 6),
) -> Figure:
    """Genera un grafico de barras agrupadas: precision/recall/F1 por clase.

    Args:
        result: EvaluationResult con class_metrics.
        title: Titulo (defecto: usa model_name).
        save_path: Ruta para guardar.
        figsize: Tamano de la figura.

    Returns:
        Objeto Figure de matplotlib.
    """
    if title is None:
        title = f"Metricas por Clase — {result.model_name}"

    class_names = [cm.fault_type.name for cm in result.class_metrics]
    precisions = [cm.precision for cm in result.class_metrics]
    recalls = [cm.recall for cm in result.class_metrics]
    f1s = [cm.f1_score for cm in result.class_metrics]

    x = np.arange(len(class_names))
    width = 0.25

    fig, ax = plt.subplots(1, 1, figsize=figsize)

    ax.bar(x - width, precisions, width, label="Precision", color="#4CAF50", alpha=0.85)
    ax.bar(x, recalls, width, label="Recall", color="#2196F3", alpha=0.85)
    ax.bar(x + width, f1s, width, label="F1-Score", color="#FF9800", alpha=0.85)

    ax.set_xticks(x)
    ax.set_xticklabels(class_names, fontsize=9)
    ax.set_ylabel("Score", fontsize=11)
    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.legend(fontsize=10)
    ax.set_ylim(0, 1.1)
    ax.grid(axis="y", alpha=0.3)

    fig.tight_layout()

    if save_path:
        p = Path(save_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(p, dpi=150, bbox_inches="tight")

    return fig
