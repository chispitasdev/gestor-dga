"""Utilidades de calculo de relaciones (ratios) entre gases.

Proporciona funciones puras que calculan las relaciones clave usadas
por los metodos normativos (Rogers, Dornenburg, IEC 60599, etc.).
Todas operan sobre un GasReading y retornan valores float.
"""

from __future__ import annotations

from src.dga.domain.models.gas_reading import GasReading


def safe_ratio(numerator: float, denominator: float) -> float:
    """Calcula una relacion protegida contra division por cero.

    Si el denominador es cero o negativo y el numerador es positivo,
    retorna un valor alto (999.0) indicando relacion muy grande.
    Si ambos son cero o negativos, retorna 0.0.
    """
    if denominator <= 0:
        return 999.0 if numerator > 0 else 0.0
    return numerator / denominator


# ── Relaciones clasicas (IEC 60599 / Rogers / Dornenburg) ──────────

def ratio_ch4_h2(reading: GasReading) -> float:
    """CH4 / H2 — sensible a temperatura de falla."""
    return safe_ratio(reading.ch4, reading.h2)


def ratio_c2h2_c2h4(reading: GasReading) -> float:
    """C2H2 / C2H4 — discrimina descargas vs. termicas."""
    return safe_ratio(reading.c2h2, reading.c2h4)


def ratio_c2h4_c2h6(reading: GasReading) -> float:
    """C2H4 / C2H6 — indica severidad termica."""
    return safe_ratio(reading.c2h4, reading.c2h6)


def ratio_c2h6_ch4(reading: GasReading) -> float:
    """C2H6 / CH4."""
    return safe_ratio(reading.c2h6, reading.ch4)


def ratio_c2h6_c2h2(reading: GasReading) -> float:
    """C2H6 / C2H2 — usada por Dornenburg (R4)."""
    return safe_ratio(reading.c2h6, reading.c2h2)


def ratio_c2h2_ch4(reading: GasReading) -> float:
    """C2H2 / CH4 — usada por Dornenburg."""
    return safe_ratio(reading.c2h2, reading.ch4)


def ratio_co2_co(reading: GasReading) -> float:
    """CO2 / CO — indica degradacion de celulosa."""
    return safe_ratio(reading.co2, reading.co)


# ── Total de gases combustibles ────────────────────────────────────

def total_combustible_gases(reading: GasReading) -> float:
    """Suma de los 5 gases combustibles de hidrocarburos + H2.

    TDCG = H2 + CH4 + C2H6 + C2H4 + C2H2 + CO
    Segun IEEE C57.104-2019.
    """
    return (
        reading.h2 + reading.ch4 + reading.c2h6
        + reading.c2h4 + reading.c2h2 + reading.co
    )


def total_hydrocarbons(reading: GasReading) -> float:
    """Suma de gases hidrocarburos: CH4 + C2H6 + C2H4 + C2H2."""
    return reading.ch4 + reading.c2h6 + reading.c2h4 + reading.c2h2


# ── Porcentajes para Duval ─────────────────────────────────────────

def duval_triangle_percentages(reading: GasReading) -> tuple[float, float, float]:
    """Calcula porcentajes (%CH4, %C2H4, %C2H2) para el Triangulo de Duval 1.

    Returns:
        Tupla (pct_ch4, pct_c2h4, pct_c2h2) con valores 0-100.
        Si la suma es cero, retorna (0.0, 0.0, 0.0).
    """
    total = reading.ch4 + reading.c2h4 + reading.c2h2
    if total <= 0:
        return (0.0, 0.0, 0.0)
    pct_ch4 = (reading.ch4 / total) * 100
    pct_c2h4 = (reading.c2h4 / total) * 100
    pct_c2h2 = (reading.c2h2 / total) * 100
    return (pct_ch4, pct_c2h4, pct_c2h2)


def duval_pentagon_percentages(
    reading: GasReading,
) -> tuple[float, float, float, float, float]:
    """Calcula porcentajes (%H2, %CH4, %C2H6, %C2H4, %C2H2) para el Pentagono de Duval 1.

    Returns:
        Tupla (pct_h2, pct_ch4, pct_c2h6, pct_c2h4, pct_c2h2) con valores 0-100.
        Si la suma es cero, retorna (0, 0, 0, 0, 0).
    """
    total = reading.h2 + reading.ch4 + reading.c2h6 + reading.c2h4 + reading.c2h2
    if total <= 0:
        return (0.0, 0.0, 0.0, 0.0, 0.0)
    pct_h2 = (reading.h2 / total) * 100
    pct_ch4 = (reading.ch4 / total) * 100
    pct_c2h6 = (reading.c2h6 / total) * 100
    pct_c2h4 = (reading.c2h4 / total) * 100
    pct_c2h2 = (reading.c2h2 / total) * 100
    return (pct_h2, pct_ch4, pct_c2h6, pct_c2h4, pct_c2h2)
