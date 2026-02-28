"""Metodo de diagnostico del Pentagono de Duval 1.

El Pentagono de Duval utiliza los porcentajes relativos de cinco gases
de hidrocarburos (H2, CH4, C2H6, C2H4, C2H2) para clasificar el tipo
de falla en un espacio pentagonal.

Las zonas del pentagono son extensiones del triangulo de Duval que
proporcionan mayor resolucion diagnostica al incorporar H2 y C2H6.

Zonas:
    PD  : Descargas parciales
    D1  : Descargas de baja energia
    D2  : Descargas de alta energia
    T1  : Falla termica < 300 °C
    T2  : Falla termica 300-700 °C
    T3  : Falla termica > 700 °C
    S   : Sobrecalentamiento de aceite/celulosa
"""

from __future__ import annotations

from src.dga.domain.models.fault_type import FaultType
from src.dga.domain.models.gas_reading import GasReading
from src.dga.domain.models.method_result import MethodResult
from src.dga.application.services.normative_methods.gas_ratios import (
    duval_pentagon_percentages,
)

METHOD_NAME = "Pentagono de Duval 1"


def _classify_zone(
    pct_h2: float, pct_ch4: float, pct_c2h6: float,
    pct_c2h4: float, pct_c2h2: float,
) -> tuple[FaultType, str]:
    """Clasifica el punto en la zona correspondiente del Pentagono de Duval 1.

    Se implementan las zonas de decision del pentagono como reglas
    condicionales basadas en los umbrales publicados por Duval.
    Las fronteras son aproximaciones de las regiones poligonales
    del pentagono original.
    """
    # Zona PD: Descargas parciales — predomina H2
    if pct_h2 > 60 and pct_c2h2 < 5 and pct_c2h4 < 10:
        return FaultType.PD, "Descargas parciales (predomina H2)"

    # Zonas con acetileno significativo
    if pct_c2h2 > 15:
        if pct_c2h4 > 25:
            return FaultType.D2, "Descargas de alta energia"
        return FaultType.D1, "Descargas de baja energia"

    if pct_c2h2 > 5:
        if pct_c2h4 > 30:
            return FaultType.D2, "Descargas de alta energia (arco)"
        if pct_h2 > 30:
            return FaultType.D1, "Descargas de baja energia"
        return FaultType.DT, "Mezcla de descarga y falla termica"

    # Sin acetileno significativo (< 5%)
    # Predomina etileno → alta temperatura
    if pct_c2h4 > 50:
        return FaultType.T3, "Falla termica > 700 °C"

    if pct_c2h4 > 25:
        if pct_c2h6 > 20:
            return FaultType.T2, "Falla termica 300-700 °C"
        return FaultType.T3, "Falla termica > 700 °C"

    if pct_c2h4 > 10:
        if pct_c2h6 > 30:
            return FaultType.S, "Sobrecalentamiento"
        return FaultType.T2, "Falla termica 300-700 °C"

    # Predomina metano y/o etano
    if pct_ch4 > 40:
        if pct_c2h6 > 20:
            return FaultType.S, "Sobrecalentamiento (aceite/celulosa)"
        return FaultType.T1, "Falla termica < 300 °C"

    if pct_c2h6 > 40:
        return FaultType.S, "Sobrecalentamiento"

    if pct_h2 > 40:
        return FaultType.PD, "Descargas parciales"

    return FaultType.T1, "Falla termica de baja temperatura"


def diagnose(reading: GasReading) -> MethodResult:
    """Ejecuta el diagnostico del Pentagono de Duval 1.

    Args:
        reading: Lectura de gases disueltos.

    Returns:
        MethodResult con el tipo de falla segun la zona del pentagono.
    """
    pct_h2, pct_ch4, pct_c2h6, pct_c2h4, pct_c2h2 = duval_pentagon_percentages(
        reading
    )

    # Si todos son cero, no hay gases de hidrocarburos
    if pct_h2 == 0.0 and pct_ch4 == 0.0 and pct_c2h6 == 0.0:
        return MethodResult(
            method_name=METHOD_NAME,
            fault_type=FaultType.N,
            description="Gases insuficientes para aplicar el pentagono",
            details={
                "applicable": False,
                "pct_H2": 0.0, "pct_CH4": 0.0, "pct_C2H6": 0.0,
                "pct_C2H4": 0.0, "pct_C2H2": 0.0,
            },
        )

    fault_type, description = _classify_zone(
        pct_h2, pct_ch4, pct_c2h6, pct_c2h4, pct_c2h2
    )

    return MethodResult(
        method_name=METHOD_NAME,
        fault_type=fault_type,
        description=description,
        details={
            "applicable": True,
            "pct_H2": round(pct_h2, 2),
            "pct_CH4": round(pct_ch4, 2),
            "pct_C2H6": round(pct_c2h6, 2),
            "pct_C2H4": round(pct_c2h4, 2),
            "pct_C2H2": round(pct_c2h2, 2),
        },
    )
