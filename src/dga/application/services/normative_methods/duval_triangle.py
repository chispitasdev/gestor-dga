"""Metodo de diagnostico del Triangulo de Duval 1.

El Triangulo de Duval utiliza los porcentajes relativos de tres gases
clave (CH4, C2H4, C2H2) para ubicar un punto en un triangulo
ternario y clasificar el tipo de falla.

Las zonas del triangulo estan definidas por Michel Duval (IEEE/IEC)
y corresponden a:
    PD  : Descargas parciales
    D1  : Descargas de baja energia
    D2  : Descargas de alta energia
    T1  : Falla termica < 300 °C
    T2  : Falla termica 300-700 °C
    T3  : Falla termica > 700 °C
    DT  : Mezcla descarga + termica
"""

from __future__ import annotations

from src.dga.domain.models.fault_type import FaultType
from src.dga.domain.models.gas_reading import GasReading
from src.dga.domain.models.method_result import MethodResult
from src.dga.application.services.normative_methods.gas_ratios import (
    duval_triangle_percentages,
)

METHOD_NAME = "Triangulo de Duval 1"


def _classify_zone(
    pct_ch4: float, pct_c2h4: float, pct_c2h2: float
) -> tuple[FaultType, str]:
    """Clasifica el punto en la zona correspondiente del Triangulo de Duval 1.

    Las fronteras se definen segun los limites publicados por Michel Duval.

    Se usa el sistema de coordenadas ternarias:
        %CH4 + %C2H4 + %C2H2 = 100

    Los limites de zona son aproximaciones de las regiones poligonales
    del triangulo original, implementadas como condiciones secuenciales.
    """
    # Zona PD: Descargas parciales — alto %CH4, muy bajo %C2H4 y %C2H2
    if pct_c2h2 > 13:
        if pct_c2h4 < 23:
            return FaultType.D1, "Descargas de baja energia"
        if pct_c2h2 > 29:
            return FaultType.D2, "Descargas de alta energia"
        return FaultType.D2, "Descargas de alta energia"

    # Sin acetileno significativo
    if pct_c2h2 <= 4:
        if pct_c2h4 < 20:
            if pct_ch4 > 98:
                return FaultType.PD, "Descargas parciales"
            return FaultType.T1, "Falla termica < 300 °C"
        if pct_c2h4 < 50:
            return FaultType.T2, "Falla termica 300-700 °C"
        return FaultType.T3, "Falla termica > 700 °C"

    # Acetileno bajo-medio (4-13%)
    if pct_c2h4 < 23:
        return FaultType.D1, "Descargas de baja energia"

    return FaultType.DT, "Mezcla de falla termica y electrica"


def diagnose(reading: GasReading) -> MethodResult:
    """Ejecuta el diagnostico del Triangulo de Duval 1.

    Args:
        reading: Lectura de gases disueltos.

    Returns:
        MethodResult con el tipo de falla segun la zona del triangulo.
    """
    pct_ch4, pct_c2h4, pct_c2h2 = duval_triangle_percentages(reading)

    # Si todos los porcentajes son cero, no hay gases suficientes
    if pct_ch4 == 0.0 and pct_c2h4 == 0.0 and pct_c2h2 == 0.0:
        return MethodResult(
            method_name=METHOD_NAME,
            fault_type=FaultType.N,
            description="Gases insuficientes para aplicar el triangulo",
            details={
                "applicable": False,
                "pct_CH4": 0.0, "pct_C2H4": 0.0, "pct_C2H2": 0.0,
            },
        )

    fault_type, description = _classify_zone(pct_ch4, pct_c2h4, pct_c2h2)

    return MethodResult(
        method_name=METHOD_NAME,
        fault_type=fault_type,
        description=description,
        details={
            "applicable": True,
            "pct_CH4": round(pct_ch4, 2),
            "pct_C2H4": round(pct_c2h4, 2),
            "pct_C2H2": round(pct_c2h2, 2),
        },
    )
