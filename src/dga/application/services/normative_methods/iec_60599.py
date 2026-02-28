"""Metodo de diagnostico IEC 60599:2022.

Clasifica fallas en transformadores de potencia mediante la
interpretacion de tres relaciones clave de gases disueltos,
conforme a la Tabla 2 de la norma IEC 60599:2022.

Relaciones usadas:
    R1 = C2H2 / C2H4
    R2 = CH4 / H2
    R5 = C2H4 / C2H6

Codigos de relacion:
    0 = < limite inferior
    1 = rango intermedio
    2 = >= limite superior
"""

from __future__ import annotations

from src.dga.domain.models.fault_type import FaultType
from src.dga.domain.models.gas_reading import GasReading
from src.dga.domain.models.method_result import MethodResult
from src.dga.application.services.normative_methods.gas_ratios import (
    ratio_c2h2_c2h4,
    ratio_ch4_h2,
    ratio_c2h4_c2h6,
)

METHOD_NAME = "IEC 60599:2022"


def _code_r1(ratio: float) -> int:
    """Codigo para R1 = C2H2 / C2H4.

    < 0.1  -> 0   (sin significancia)
    0.1-1  -> 1
    > 1    -> 2
    """
    if ratio < 0.1:
        return 0
    if ratio <= 1.0:
        return 1
    return 2


def _code_r2(ratio: float) -> int:
    """Codigo para R2 = CH4 / H2.

    < 0.1  -> 0   (predomina H2)
    0.1-1  -> 1
    > 1    -> 2   (predomina CH4)
    """
    if ratio < 0.1:
        return 0
    if ratio <= 1.0:
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


# ── Tabla de diagnostico IEC 60599 ────────────────────────────────
# Clave: (code_r1, code_r2, code_r5) -> (FaultType, descripcion)
# Se cubren los casos tipicos de la Tabla 2.
_DIAGNOSIS_TABLE: dict[tuple[int, int, int], tuple[FaultType, str]] = {
    # PD — Descargas parciales: H2 predominante
    (0, 0, 0): (FaultType.PD, "Descargas parciales de baja energia"),

    # D1 — Descargas de baja energia
    (1, 0, 0): (FaultType.D1, "Descargas de baja energia (chispas)"),
    (2, 0, 0): (FaultType.D1, "Descargas de baja energia con C2H2 elevado"),

    # D2 — Descargas de alta energia
    (1, 0, 1): (FaultType.D2, "Descargas de alta energia"),
    (1, 0, 2): (FaultType.D2, "Descargas de alta energia severas"),
    (2, 0, 1): (FaultType.D2, "Descargas de alta energia con arco"),
    (2, 0, 2): (FaultType.D2, "Descargas de alta energia con arco severo"),

    # T1 — Falla termica < 300°C
    (0, 1, 0): (FaultType.T1, "Falla termica baja temperatura (< 300 °C)"),
    (0, 2, 0): (FaultType.T1, "Falla termica baja temperatura (< 300 °C)"),

    # T2 — Falla termica 300-700°C
    (0, 2, 1): (FaultType.T2, "Falla termica media temperatura (300-700 °C)"),
    (0, 1, 1): (FaultType.T2, "Falla termica media temperatura (300-700 °C)"),

    # T3 — Falla termica > 700°C
    (0, 2, 2): (FaultType.T3, "Falla termica alta temperatura (> 700 °C)"),
    (0, 1, 2): (FaultType.T3, "Falla termica alta temperatura (> 700 °C)"),

    # DT — Mezcla termica y electrica
    (1, 1, 0): (FaultType.DT, "Mezcla de descarga y falla termica"),
    (2, 1, 0): (FaultType.DT, "Mezcla de descarga y falla termica"),
    (1, 2, 0): (FaultType.DT, "Mezcla de descarga y falla termica"),
    (2, 2, 0): (FaultType.DT, "Mezcla de descarga y falla termica"),
    (1, 1, 1): (FaultType.DT, "Mezcla de descarga y falla termica"),
    (2, 1, 1): (FaultType.DT, "Mezcla de descarga y falla termica"),
    (1, 2, 1): (FaultType.DT, "Mezcla de descarga y falla termica"),
    (2, 2, 1): (FaultType.DT, "Mezcla de descarga y falla termica"),
    (1, 1, 2): (FaultType.DT, "Mezcla de descarga y falla termica"),
    (2, 1, 2): (FaultType.DT, "Mezcla de descarga y falla termica"),
    (1, 2, 2): (FaultType.DT, "Mezcla de descarga y falla termica"),
    (2, 2, 2): (FaultType.DT, "Mezcla de descarga y falla termica"),
}


def diagnose(reading: GasReading) -> MethodResult:
    """Ejecuta el diagnostico IEC 60599:2022.

    Calcula las tres relaciones de gas, las codifica y busca el
    patron en la tabla de diagnostico.

    Args:
        reading: Lectura de gases disueltos.

    Returns:
        MethodResult con el tipo de falla detectada.
    """
    r1 = ratio_c2h2_c2h4(reading)
    r2 = ratio_ch4_h2(reading)
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
        description = "No se identifica un patron de falla definido"

    return MethodResult(
        method_name=METHOD_NAME,
        fault_type=fault_type,
        description=description,
        details={
            "R1_C2H2_C2H4": round(r1, 4),
            "R2_CH4_H2": round(r2, 4),
            "R5_C2H4_C2H6": round(r5, 4),
            "code_R1": c1,
            "code_R2": c2,
            "code_R5": c5,
            "pattern": f"({c1}, {c2}, {c5})",
        },
    )
