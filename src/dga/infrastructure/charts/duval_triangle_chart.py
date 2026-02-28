"""Grafico del Triangulo de Duval 1 con matplotlib.

Dibuja el triangulo ternario con las 7 zonas de falla coloreadas
y permite superponer uno o mas puntos de muestra sobre el diagrama.

Coordenadas ternarias → cartesianas:
    x = 0.5 * (2*B + C) / (A + B + C)
    y = (sqrt(3)/2) * C / (A + B + C)
donde A = %CH4, B = %C2H4, C = %C2H2.
"""

from __future__ import annotations

from pathlib import Path
import numpy as np
import matplotlib

matplotlib.use("Agg")  # Backend no interactivo

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.patches import Polygon as MplPolygon

from src.dga.domain.models.gas_reading import GasReading
from src.dga.application.services.normative_methods.gas_ratios import (
    duval_triangle_percentages,
)

# Constante para conversiones ternarias
_SQRT3_2 = np.sqrt(3) / 2


def _ternary_to_cart(a: float, b: float, c: float) -> tuple[float, float]:
    """Convierte coordenadas ternarias (A, B, C) → cartesianas (x, y).

    A = %CH4 (vertice superior izquierdo)
    B = %C2H4 (vertice inferior derecho)
    C = %C2H2 (vertice superior derecho)
    """
    total = a + b + c
    if total == 0:
        return (0.5, _SQRT3_2 / 3)
    x = 0.5 * (2 * b + c) / total
    y = _SQRT3_2 * c / total
    return (x, y)


# Zonas del Triangulo de Duval 1 (coordenadas ternarias: %CH4, %C2H4, %C2H2)
# Cada zona es una lista de vertices en orden.
_ZONES: dict[str, dict] = {
    "PD": {
        "vertices_ternary": [
            (98, 2, 0), (80, 20, 0), (80, 16, 4), (98, 0, 2),
        ],
        "color": "#b3e6b3",
        "label": "PD",
    },
    "T1": {
        "vertices_ternary": [
            (80, 20, 0), (46, 50, 4), (76, 20, 4), (80, 16, 4),
        ],
        "color": "#ffffb3",
        "label": "T1",
    },
    "T2": {
        "vertices_ternary": [
            (46, 50, 4), (0, 100, 0), (0, 76, 4),
        ],
        "color": "#ffd699",
        "label": "T2",
    },
    "T3": {
        "vertices_ternary": [
            (80, 20, 0), (0, 100, 0), (46, 50, 4),
        ],
        "color": "#ff9999",
        "label": "T3",
    },
    "D1": {
        "vertices_ternary": [
            (98, 0, 2), (80, 16, 4), (76, 20, 4), (23, 0, 77),
            (0, 0, 100),
        ],
        "color": "#b3d9ff",
        "label": "D1",
    },
    "D2": {
        "vertices_ternary": [
            (23, 0, 77), (76, 20, 4), (0, 76, 4), (0, 71, 29),
        ],
        "color": "#d9b3ff",
        "label": "D2",
    },
    "DT": {
        "vertices_ternary": [
            (0, 71, 29), (0, 76, 4), (0, 100, 0), (0, 0, 100),
            (23, 0, 77),
        ],
        "color": "#ffccee",
        "label": "DT",
    },
}


def plot_duval_triangle(
    readings: list[GasReading],
    labels: list[str] | None = None,
    title: str = "Triangulo de Duval 1",
    save_path: str | Path | None = None,
    figsize: tuple[float, float] = (8, 7),
) -> Figure:
    """Genera el grafico del Triangulo de Duval 1.

    Args:
        readings: Lista de lecturas de gases a ubicar en el triangulo.
        labels: Etiquetas opcionales para cada punto.
        title: Titulo del grafico.
        save_path: Ruta para guardar la imagen (None = no guarda).
        figsize: Tamano de la figura.

    Returns:
        Objeto Figure de matplotlib.
    """
    fig, ax = plt.subplots(1, 1, figsize=figsize)
    ax.set_aspect("equal")
    ax.set_xlim(-0.05, 1.05)
    ax.set_ylim(-0.05, _SQRT3_2 + 0.05)
    ax.axis("off")
    ax.set_title(title, fontsize=14, fontweight="bold", pad=15)

    # Dibujar zonas coloreadas
    for zone_name, zone_data in _ZONES.items():
        verts_ternary = zone_data["vertices_ternary"]
        verts_cart = [_ternary_to_cart(a, b, c) for a, b, c in verts_ternary]
        poly = MplPolygon(
            verts_cart,
            closed=True,
            facecolor=zone_data["color"],
            edgecolor="gray",
            linewidth=0.5,
            alpha=0.7,
        )
        ax.add_patch(poly)

        # Etiqueta de zona en el centroide
        cx = float(np.mean([v[0] for v in verts_cart]))
        cy = float(np.mean([v[1] for v in verts_cart]))
        ax.text(
            cx, cy, zone_data["label"],
            ha="center", va="center",
            fontsize=9, fontweight="bold", color="black",
        )

    # Triangulo exterior
    tri_verts = [
        _ternary_to_cart(100, 0, 0),   # CH4
        _ternary_to_cart(0, 100, 0),    # C2H4
        _ternary_to_cart(0, 0, 100),    # C2H2
    ]
    triangle = MplPolygon(
        tri_verts + [tri_verts[0]],
        closed=True,
        fill=False,
        edgecolor="black",
        linewidth=2,
    )
    ax.add_patch(triangle)

    # Etiquetas de vertices
    ax.text(
        tri_verts[0][0], tri_verts[0][1] + 0.03,
        "%CH₄", ha="center", fontsize=11, fontweight="bold",
    )
    ax.text(
        tri_verts[1][0] + 0.03, tri_verts[1][1] - 0.03,
        "%C₂H₄", ha="left", fontsize=11, fontweight="bold",
    )
    ax.text(
        tri_verts[2][0] - 0.03, tri_verts[2][1] - 0.03,
        "%C₂H₂", ha="right", fontsize=11, fontweight="bold",
    )

    # Plotear lecturas
    if readings:
        for i, reading in enumerate(readings):
            pct_ch4, pct_c2h4, pct_c2h2 = duval_triangle_percentages(reading)
            x, y = _ternary_to_cart(pct_ch4, pct_c2h4, pct_c2h2)
            ax.plot(x, y, "ko", markersize=8, zorder=5)
            ax.plot(x, y, "ro", markersize=5, zorder=6)

            if labels and i < len(labels):
                ax.annotate(
                    labels[i], (x, y),
                    textcoords="offset points", xytext=(8, 8),
                    fontsize=8, color="navy",
                    arrowprops=dict(arrowstyle="-", color="gray", lw=0.5),
                )

    fig.tight_layout()

    if save_path:
        p = Path(save_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(p, dpi=150, bbox_inches="tight")

    return fig
