"""Metodo de diagnostico de Rogers (Relaciones de 4 gases).

Utiliza tres relaciones de gases segun la tabla de Rogers modificada
para clasificar el tipo de falla:

    R1 = CH4 / H2
    R2 = C2H2 / C2H4
    R5 = C2H4 / C2H6

Se codifica cada relacion y se busca el patron en la tabla diagnostica.
"""

from __future__ import annotations

from src.dga.domain.models.fault_type import FaultType
from src.dga.domain.models.gas_reading import GasReading
from src.dga.domain.models.method_result import MethodResult
from src.dga.application.services.normative_methods.gas_ratios import (
    ratio_ch4_h2,
    ratio_c2h2_c2h4,
    ratio_c2h4_c2h6,
)

METHOD_NAME = "Rogers"


def _code_r1(ratio: float) -> int:
    """Codigo para R1 = CH4 / H2.

    < 0.1  -> 5
    0.1-1  -> 0
    1-3    -> 1
    > 3    -> 2
    """
    if ratio < 0.1:
        return 5
    if ratio <= 1.0:
        return 0
    if ratio <= 3.0:
        return 1
    return 2


def _code_r2(ratio: float) -> int:
    """Codigo para R2 = C2H2 / C2H4.

    < 0.1  -> 0
    0.1-3  -> 1
    > 3    -> 2
    """
    if ratio < 0.1:
        return 0
    if ratio <= 3.0:
        return 1
    return 2


def _code_r5(ratio: float) -> int:
    """Codigo para R5 = C2H4 / C2H6.

    < 1    -> 0
    1-3    -> 1
    > 3    -> 2
    """
    if ratio < 1.0:
        return 0
    if ratio <= 3.0:
        return 1
    return 2


# ── Tabla de diagnostico de Rogers ─────────────────────────────────
# Clave: (code_r1, code_r2, code_r5) -> (FaultType, descripcion)
_DIAGNOSIS_TABLE: dict[tuple[int, int, int], tuple[FaultType, str]] = {
    # Normal / envejecimiento
    (0, 0, 0): (FaultType.N, "Deterioro normal por envejecimiento"),

    # Descargas parciales
    (5, 0, 0): (FaultType.PD, "Descargas parciales de baja energia"),

    # Descargas de baja energia (D1)
    (0, 1, 0): (FaultType.D1, "Descargas de baja energia"),
    (1, 1, 0): (FaultType.D1, "Descargas de baja energia"),

    # Descargas de alta energia (D2)
    (0, 2, 0): (FaultType.D2, "Descargas de alta energia (arco)"),
    (0, 1, 1): (FaultType.D2, "Descargas de alta energia"),
    (0, 1, 2): (FaultType.D2, "Descargas de alta energia con calentamiento"),
    (0, 2, 1): (FaultType.D2, "Descargas de alta energia"),
    (0, 2, 2): (FaultType.D2, "Descargas de alta energia"),

    # Falla termica < 300°C (T1)
    (1, 0, 0): (FaultType.T1, "Falla termica menor a 300 °C"),
    (2, 0, 0): (FaultType.T1, "Falla termica menor a 300 °C (CH4 alto)"),

    # Falla termica 300-700°C (T2)
    (2, 0, 1): (FaultType.T2, "Falla termica entre 300 y 700 °C"),
    (1, 0, 1): (FaultType.T2, "Falla termica entre 300 y 700 °C"),

    # Falla termica > 700°C (T3)
    (2, 0, 2): (FaultType.T3, "Falla termica mayor a 700 °C"),
    (1, 0, 2): (FaultType.T3, "Falla termica mayor a 700 °C"),
}


def diagnose(reading: GasReading) -> MethodResult:
    """Ejecuta el diagnostico de Rogers.

    Args:
        reading: Lectura de gases disueltos.

    Returns:
        MethodResult con el tipo de falla detectada.
    """
    r1 = ratio_ch4_h2(reading)
    r2 = ratio_c2h2_c2h4(reading)
    r5 = ratio_c2h4_c2h6(reading)

    c1 = _code_r1(r1)
    c2 = _code_r2(r2)
    c5 = _code_r5(r5)

    key = (c1, c2, c5)
    result = _DIAGNOSIS_TABLE.get(key)

    if result is not None:
        fault_type, description = result
    else:
        fault_type = FaultType.N
        description = "Combinacion de codigos sin diagnostico definido"

    return MethodResult(
        method_name=METHOD_NAME,
        fault_type=fault_type,
        description=description,
        details={
            "R1_CH4_H2": round(r1, 4),
            "R2_C2H2_C2H4": round(r2, 4),
            "R5_C2H4_C2H6": round(r5, 4),
            "code_R1": c1,
            "code_R2": c2,
            "code_R5": c5,
            "pattern": f"({c1}, {c2}, {c5})",
        },
    )
