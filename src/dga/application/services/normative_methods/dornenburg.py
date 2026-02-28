"""Metodo de diagnostico de Dornenburg (Relaciones de gas).

Utiliza cuatro relaciones de gases y verifica que las concentraciones
superen umbrales minimos de validez (L1) antes de aplicar la tabla
de diagnostico.

Relaciones:
    R1 = CH4 / H2
    R2 = C2H2 / C2H4
    R3 = C2H2 / CH4
    R4 = C2H6 / C2H2

El metodo solo es aplicable si al menos un gas clave supera su
limite L1 de significancia.
"""

from __future__ import annotations

from src.dga.domain.models.fault_type import FaultType
from src.dga.domain.models.gas_reading import GasReading
from src.dga.domain.models.method_result import MethodResult
from src.dga.application.services.normative_methods.gas_ratios import (
    ratio_ch4_h2,
    ratio_c2h2_c2h4,
    ratio_c2h2_ch4,
    ratio_c2h6_c2h2,
)

METHOD_NAME = "Dornenburg"

# ── Limites L1 de significancia (ppm) ──────────────────────────────
# Si ninguno de estos gases supera su L1, el metodo no aplica.
_L1_LIMITS: dict[str, float] = {
    "h2": 100,
    "ch4": 120,
    "c2h2": 1,
    "c2h4": 50,
    "c2h6": 65,
    "co": 350,
}


def _exceeds_l1(reading: GasReading) -> bool:
    """Verifica que al menos un gas clave supere su limite L1."""
    gas_map = {
        "h2": reading.h2, "ch4": reading.ch4, "c2h2": reading.c2h2,
        "c2h4": reading.c2h4, "c2h6": reading.c2h6, "co": reading.co,
    }
    return any(gas_map[gas] > limit for gas, limit in _L1_LIMITS.items())


def _classify(r1: float, r2: float, r3: float, r4: float) -> tuple[FaultType, str]:
    """Clasifica la falla usando los criterios de Dornenburg.

    Aplicamos las reglas de decision del metodo original:
    - Si R1 > 1.0 y R3 < 0.3 y R2 < 0.1 y R4 > 0.4 → Falla termica
    - Si R1 < 0.1 y R2 no significativo → Descargas parciales
    - Si R2 > 0.1 y R3 > 0.3 → Descargas (arco)
    """
    # Falla termica: predominan hidrocarburos pesados
    if r1 > 1.0 and r2 < 0.1:
        if r4 > 0.4:
            return FaultType.T2, "Falla termica (descomposicion de aceite)"
        return FaultType.T1, "Falla termica de baja temperatura"

    # Descargas parciales (corona): predomina H2
    if r1 < 0.1 and r2 < 0.1:
        return FaultType.PD, "Descargas parciales (efecto corona)"

    # Descargas de alta energia: acetileno presente
    if r2 > 0.1 and r3 > 0.3:
        return FaultType.D2, "Descargas de alta energia (arco electrico)"

    # Descargas de baja energia
    if r2 > 0.1:
        return FaultType.D1, "Descargas de baja energia"

    # Falla termica por defecto cuando hay gases pero no cuadra otro patron
    if r1 > 1.0:
        return FaultType.T1, "Posible falla termica"

    return FaultType.N, "Sin patron de falla definido por Dornenburg"


def diagnose(reading: GasReading) -> MethodResult:
    """Ejecuta el diagnostico de Dornenburg.

    Primero verifica que se superen los limites L1. Si no,
    retorna un resultado indicando que el metodo no es aplicable.

    Args:
        reading: Lectura de gases disueltos.

    Returns:
        MethodResult con el tipo de falla detectada.
    """
    if not _exceeds_l1(reading):
        return MethodResult(
            method_name=METHOD_NAME,
            fault_type=FaultType.N,
            description="Gases por debajo de limites L1; metodo no aplicable",
            details={"applicable": False, "l1_limits": _L1_LIMITS},
        )

    r1 = ratio_ch4_h2(reading)
    r2 = ratio_c2h2_c2h4(reading)
    r3 = ratio_c2h2_ch4(reading)
    r4 = ratio_c2h6_c2h2(reading)

    fault_type, description = _classify(r1, r2, r3, r4)

    return MethodResult(
        method_name=METHOD_NAME,
        fault_type=fault_type,
        description=description,
        details={
            "applicable": True,
            "R1_CH4_H2": round(r1, 4),
            "R2_C2H2_C2H4": round(r2, 4),
            "R3_C2H2_CH4": round(r3, 4),
            "R4_C2H6_C2H2": round(r4, 4),
        },
    )
