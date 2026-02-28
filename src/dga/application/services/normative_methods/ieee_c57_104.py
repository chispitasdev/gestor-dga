"""Metodo de diagnostico IEEE C57.104-2019.

Evalua el estado del transformador comparando las concentraciones
individuales de cada gas y el TDCG (Total Dissolved Combustible Gas)
contra los limites tipicos de la norma IEEE C57.104-2019 (Tabla 1).

Clasificacion por condiciones:
    - Condicion 1: Normal.
    - Condicion 2: Normal con precaucion.
    - Condicion 3: Anormal, se requiere investigacion.
    - Condicion 4: Peligrosa, accion inmediata.

Luego usa las relaciones de gas IEC basicas para sugerir un tipo de
falla cuando la condicion es >= 3.
"""

from __future__ import annotations

from src.dga.domain.models.fault_type import FaultType
from src.dga.domain.models.gas_reading import GasReading
from src.dga.domain.models.method_result import MethodResult
from src.dga.application.services.normative_methods.gas_ratios import (
    total_combustible_gases,
    ratio_ch4_h2,
    ratio_c2h2_c2h4,
    ratio_c2h4_c2h6,
)

METHOD_NAME = "IEEE C57.104-2019"

# ── Limites tipicos (ppm) por condicion ─────────────────────────────
# Cada gas tiene 3 umbrales que separan las 4 condiciones.
# Estructura: (limite_cond2, limite_cond3, limite_cond4)
_GAS_LIMITS: dict[str, tuple[float, float, float]] = {
    "h2":   (100, 200, 500),
    "ch4":  (75,  125, 200),
    "c2h6": (65,  100, 150),
    "c2h4": (50,  100, 200),
    "c2h2": (2,   10,  35),
    "co":   (350, 570, 1400),
    "co2":  (2500, 4000, 10000),
}

# Limites de TDCG (Total Dissolved Combustible Gas)
_TDCG_LIMITS: tuple[float, float, float] = (720, 1920, 4630)

_CONDITION_LABELS = {
    1: "Condicion 1: Funcionamiento normal",
    2: "Condicion 2: Normal con gases por encima de valores tipicos",
    3: "Condicion 3: Anormal, se requiere investigacion",
    4: "Condicion 4: Peligrosa, se requiere accion inmediata",
}


def _gas_condition(gas_name: str, value: float) -> int:
    """Determina la condicion (1-4) de un gas individual."""
    limits = _GAS_LIMITS.get(gas_name)
    if limits is None:
        return 1
    if value <= limits[0]:
        return 1
    if value <= limits[1]:
        return 2
    if value <= limits[2]:
        return 3
    return 4


def _tdcg_condition(tdcg: float) -> int:
    """Determina la condicion (1-4) por TDCG."""
    if tdcg <= _TDCG_LIMITS[0]:
        return 1
    if tdcg <= _TDCG_LIMITS[1]:
        return 2
    if tdcg <= _TDCG_LIMITS[2]:
        return 3
    return 4


def _suggest_fault_type(reading: GasReading) -> FaultType:
    """Sugiere el tipo de falla usando relaciones basicas de gas.

    Aplica criterios simplificados cuando la condicion global >= 3.
    """
    r1 = ratio_ch4_h2(reading)
    r2 = ratio_c2h2_c2h4(reading)
    r3 = ratio_c2h4_c2h6(reading)

    # Predomina acetileno → descargas
    if reading.c2h2 > 10:
        if r2 > 2.0:
            return FaultType.D1
        return FaultType.D2

    # Relaciones termicas
    if r3 > 4.0:
        return FaultType.T3
    if r3 > 1.0:
        return FaultType.T2
    if r1 > 1.0 and r3 <= 1.0:
        return FaultType.T1

    # Descargas parciales
    if reading.h2 > 100 and r1 < 0.1:
        return FaultType.PD

    return FaultType.S


def diagnose(reading: GasReading) -> MethodResult:
    """Ejecuta el diagnostico IEEE C57.104-2019.

    Args:
        reading: Lectura de gases disueltos.

    Returns:
        MethodResult con la condicion global y tipo de falla sugerido.
    """
    gas_values = {
        "h2": reading.h2, "ch4": reading.ch4, "c2h6": reading.c2h6,
        "c2h4": reading.c2h4, "c2h2": reading.c2h2, "co": reading.co,
        "co2": reading.co2,
    }

    individual_conditions = {
        gas: _gas_condition(gas, val) for gas, val in gas_values.items()
    }

    tdcg = total_combustible_gases(reading)
    tdcg_cond = _tdcg_condition(tdcg)

    overall = max(max(individual_conditions.values()), tdcg_cond)

    # Tipo de falla
    if overall <= 2:
        fault = FaultType.N
    else:
        fault = _suggest_fault_type(reading)

    description = _CONDITION_LABELS[overall]

    return MethodResult(
        method_name=METHOD_NAME,
        fault_type=fault,
        description=description,
        details={
            "overall_condition": overall,
            "tdcg_ppm": round(tdcg, 2),
            "tdcg_condition": tdcg_cond,
            "individual_conditions": individual_conditions,
        },
    )
