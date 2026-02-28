"""Graficos de tendencias de gases disueltos en el tiempo.

Genera graficos de linea mostrando la evolucion temporal de cada gas
para un transformador, con marcadores de umbrales criticos.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
import matplotlib.dates as mdates

from src.dga.application.services.trend_service import GasHistory


# Colores distintivos para cada gas
_GAS_COLORS: dict[str, str] = {
    "h2": "#e41a1c",
    "ch4": "#377eb8",
    "c2h6": "#4daf4a",
    "c2h4": "#984ea3",
    "c2h2": "#ff7f00",
    "co": "#a65628",
    "co2": "#f781bf",
    "o2": "#999999",
    "n2": "#666666",
}


def plot_gas_trends(
    histories: list[GasHistory],
    gases: list[str] | None = None,
    title: str = "Tendencias de Gases Disueltos",
    save_path: str | Path | None = None,
    figsize: tuple[float, float] = (12, 6),
) -> Figure:
    """Genera un grafico de lineas con la evolucion temporal de gases.

    Args:
        histories: Lista de GasHistory (uno por gas).
        gases: Nombres de gases a incluir (None = combustibles).
        title: Titulo del grafico.
        save_path: Ruta para guardar la imagen.
        figsize: Tamano de la figura.

    Returns:
        Objeto Figure de matplotlib.
    """
    if gases is None:
        # Solo gases combustibles por defecto (excluir O2 y N2)
        gases = ["h2", "ch4", "c2h6", "c2h4", "c2h2", "co"]

    fig, ax = plt.subplots(1, 1, figsize=figsize)

    for hist in histories:
        if hist.gas_name not in gases:
            continue
        if not hist.dates:
            continue

        color = _GAS_COLORS.get(hist.gas_name, "#333333")
        ax.plot(
            hist.dates, hist.values,  # type: ignore[arg-type]
            marker="o", markersize=5,
            linewidth=1.5,
            color=color,
            label=hist.gas_label,
        )

    ax.set_xlabel("Fecha de extraccion", fontsize=11)
    ax.set_ylabel("Concentracion (ppm)", fontsize=11)
    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.legend(loc="upper left", fontsize=9, framealpha=0.9)
    ax.grid(True, alpha=0.3)

    # Formato de fechas
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    fig.autofmt_xdate(rotation=30)

    fig.tight_layout()

    if save_path:
        p = Path(save_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(p, dpi=150, bbox_inches="tight")

    return fig


def plot_gas_trends_individual(
    histories: list[GasHistory],
    gases: list[str] | None = None,
    title: str = "Tendencias de Gases (Individual)",
    save_path: str | Path | None = None,
    figsize: tuple[float, float] = (14, 10),
) -> Figure:
    """Genera subplots individuales para cada gas.

    Args:
        histories: Lista de GasHistory.
        gases: Nombres de gases a incluir.
        title: Titulo general.
        save_path: Ruta para guardar.
        figsize: Tamano de la figura.

    Returns:
        Objeto Figure de matplotlib.
    """
    if gases is None:
        gases = ["h2", "ch4", "c2h6", "c2h4", "c2h2", "co"]

    selected = [h for h in histories if h.gas_name in gases and h.dates]
    n = len(selected)
    if n == 0:
        fig, ax = plt.subplots(1, 1, figsize=(6, 4))
        ax.text(0.5, 0.5, "Sin datos", ha="center", va="center")
        return fig

    cols = 2
    rows = (n + 1) // 2
    fig, axes = plt.subplots(rows, cols, figsize=figsize)
    fig.suptitle(title, fontsize=14, fontweight="bold")

    if n == 1:
        axes = [[axes]]
    elif rows == 1:
        axes = [axes]

    flat_axes: list[Axes] = [
        ax for row in axes for ax in (row if hasattr(row, '__iter__') else [row])  # type: ignore[union-attr]
    ]

    for i, hist in enumerate(selected):
        ax = flat_axes[i]
        color = _GAS_COLORS.get(hist.gas_name, "#333333")
        ax.plot(
            hist.dates, hist.values,  # type: ignore[arg-type]
            marker="s", markersize=4, linewidth=1.2,
            color=color,
        )
        ax.set_title(hist.gas_label, fontsize=10, fontweight="bold")
        ax.set_ylabel("ppm", fontsize=9)
        ax.grid(True, alpha=0.3)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))
        ax.tick_params(axis="x", rotation=30, labelsize=8)

    # Ocultar ejes sobrantes
    last_idx = len(selected) - 1
    for j in range(last_idx + 1, len(flat_axes)):
        flat_axes[j].set_visible(False)

    fig.tight_layout()

    if save_path:
        p = Path(save_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(p, dpi=150, bbox_inches="tight")

    return fig
