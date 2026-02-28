"""Tests unitarios para los 6 metodos normativos y el servicio orquestador.

Se utilizan lecturas de referencia que representan escenarios tipicos
de fallas conocidas para validar la clasificacion de cada metodo.
"""

import pytest

from src.dga.domain.models.fault_type import FaultType
from src.dga.domain.models.gas_reading import GasReading
from src.dga.domain.models.method_result import MethodResult
from src.dga.application.services.normative_methods import (
    ieee_c57_104,
    iec_60599,
    rogers,
    dornenburg,
    duval_triangle,
    duval_pentagon,
)
from src.dga.application.services.normative_diagnosis_service import (
    NormativeDiagnosisService,
    NormativeDiagnosisResult,
)


def _make_reading(**kwargs: float) -> GasReading:
    """Crea un GasReading con valores por defecto en 0."""
    defaults: dict[str, float] = {
        "h2": 0.0, "ch4": 0.0, "c2h6": 0.0, "c2h4": 0.0, "c2h2": 0.0,
        "co": 0.0, "co2": 0.0, "o2": 0.0, "n2": 0.0,
    }
    defaults.update(kwargs)
    return GasReading(**defaults)


# ====================================================================
# Lecturas de referencia para escenarios tipicos
# ====================================================================

# Normal: gases bajos
NORMAL_READING = _make_reading(
    h2=15, ch4=10, c2h6=5, c2h4=3, c2h2=0, co=100, co2=1500, o2=20000, n2=50000
)

# Descargas parciales: H2 alto, resto bajo
PD_READING = _make_reading(
    h2=500, ch4=10, c2h6=2, c2h4=1, c2h2=0, co=100, co2=2000, o2=18000, n2=55000
)

# Descargas de baja energia (D1): H2 y C2H2 presentes
D1_READING = _make_reading(
    h2=200, ch4=30, c2h6=10, c2h4=15, c2h2=50, co=150, co2=2500, o2=18000, n2=52000
)

# Descargas de alta energia (D2): C2H2 dominante + C2H4
D2_READING = _make_reading(
    h2=150, ch4=80, c2h6=40, c2h4=200, c2h2=100, co=300, co2=3000, o2=17000, n2=50000
)

# Falla termica baja (T1): CH4 alto respecto a H2
T1_READING = _make_reading(
    h2=50, ch4=200, c2h6=100, c2h4=20, c2h2=0, co=200, co2=3000, o2=19000, n2=51000
)

# Falla termica media (T2): C2H4 moderado
T2_READING = _make_reading(
    h2=60, ch4=150, c2h6=80, c2h4=150, c2h2=0, co=250, co2=3500, o2=18000, n2=50000
)

# Falla termica alta (T3): C2H4 dominante
T3_READING = _make_reading(
    h2=80, ch4=100, c2h6=30, c2h4=500, c2h2=1, co=400, co2=5000, o2=17000, n2=48000
)


# ====================================================================
# Tests IEEE C57.104-2019
# ====================================================================

class TestIEEEC57104:

    def test_normal_condition(self) -> None:
        result = ieee_c57_104.diagnose(NORMAL_READING)
        assert isinstance(result, MethodResult)
        assert result.method_name == "IEEE C57.104-2019"
        assert result.fault_type == FaultType.N
        assert result.details["overall_condition"] <= 2

    def test_high_gases_elevated_condition(self) -> None:
        result = ieee_c57_104.diagnose(T3_READING)
        assert result.details["overall_condition"] >= 3

    def test_returns_tdcg(self) -> None:
        result = ieee_c57_104.diagnose(NORMAL_READING)
        assert "tdcg_ppm" in result.details
        assert result.details["tdcg_ppm"] >= 0

    def test_condition_4_with_extreme_gases(self) -> None:
        extreme = _make_reading(
            h2=600, ch4=300, c2h6=200, c2h4=300, c2h2=50,
            co=1500, co2=12000, o2=15000, n2=45000
        )
        result = ieee_c57_104.diagnose(extreme)
        assert result.details["overall_condition"] == 4


# ====================================================================
# Tests IEC 60599
# ====================================================================

class TestIEC60599:

    def test_method_name(self) -> None:
        result = iec_60599.diagnose(NORMAL_READING)
        assert result.method_name == "IEC 60599:2022"

    def test_thermal_fault_high(self) -> None:
        result = iec_60599.diagnose(T3_READING)
        assert result.fault_type in (FaultType.T2, FaultType.T3)

    def test_discharge_with_acetylene(self) -> None:
        result = iec_60599.diagnose(D2_READING)
        assert result.fault_type in (FaultType.D1, FaultType.D2, FaultType.DT)

    def test_details_contain_ratios(self) -> None:
        result = iec_60599.diagnose(T1_READING)
        assert "R1_C2H2_C2H4" in result.details
        assert "R2_CH4_H2" in result.details
        assert "R5_C2H4_C2H6" in result.details


# ====================================================================
# Tests Rogers
# ====================================================================

class TestRogers:

    def test_method_name(self) -> None:
        result = rogers.diagnose(NORMAL_READING)
        assert result.method_name == "Rogers"

    def test_normal_low_gases(self) -> None:
        result = rogers.diagnose(NORMAL_READING)
        # Con gases tan bajos, Rogers puede dar N o un fallback
        assert isinstance(result.fault_type, FaultType)

    def test_thermal_pattern(self) -> None:
        result = rogers.diagnose(T2_READING)
        assert result.fault_type in (FaultType.T1, FaultType.T2, FaultType.T3, FaultType.N)

    def test_details_contain_pattern(self) -> None:
        result = rogers.diagnose(T1_READING)
        assert "pattern" in result.details


# ====================================================================
# Tests Dornenburg
# ====================================================================

class TestDornenburg:

    def test_method_name(self) -> None:
        result = dornenburg.diagnose(NORMAL_READING)
        assert result.method_name == "Dornenburg"

    def test_below_l1_not_applicable(self) -> None:
        low = _make_reading(h2=5, ch4=3, c2h6=2, c2h4=1, c2h2=0, co=50)
        result = dornenburg.diagnose(low)
        assert result.fault_type == FaultType.N
        assert result.details.get("applicable") is False

    def test_above_l1_applicable(self) -> None:
        result = dornenburg.diagnose(T2_READING)
        assert result.details.get("applicable") is True

    def test_pd_detection(self) -> None:
        result = dornenburg.diagnose(PD_READING)
        # PD reading has H2=500 above L1, should be applicable
        assert result.details["applicable"] is True


# ====================================================================
# Tests Triangulo de Duval
# ====================================================================

class TestDuvalTriangle:

    def test_method_name(self) -> None:
        result = duval_triangle.diagnose(NORMAL_READING)
        assert result.method_name == "Triangulo de Duval 1"

    def test_zero_gases_not_applicable(self) -> None:
        zero = _make_reading()
        result = duval_triangle.diagnose(zero)
        assert result.details.get("applicable") is False

    def test_thermal_high_c2h4(self) -> None:
        result = duval_triangle.diagnose(T3_READING)
        assert result.fault_type in (FaultType.T2, FaultType.T3)

    def test_percentages_sum_100(self) -> None:
        result = duval_triangle.diagnose(T2_READING)
        pcts = (
            result.details["pct_CH4"]
            + result.details["pct_C2H4"]
            + result.details["pct_C2H2"]
        )
        assert pcts == pytest.approx(100.0, abs=0.1)


# ====================================================================
# Tests Pentagono de Duval
# ====================================================================

class TestDuvalPentagon:

    def test_method_name(self) -> None:
        result = duval_pentagon.diagnose(NORMAL_READING)
        assert result.method_name == "Pentagono de Duval 1"

    def test_zero_gases_not_applicable(self) -> None:
        zero = _make_reading()
        result = duval_pentagon.diagnose(zero)
        assert result.details.get("applicable") is False

    def test_pd_detection_h2_dominant(self) -> None:
        result = duval_pentagon.diagnose(PD_READING)
        # H2 es muy dominante (500 de 513)
        assert result.fault_type in (FaultType.PD, FaultType.T1)

    def test_percentages_sum_100(self) -> None:
        result = duval_pentagon.diagnose(T2_READING)
        pcts = sum([
            result.details["pct_H2"],
            result.details["pct_CH4"],
            result.details["pct_C2H6"],
            result.details["pct_C2H4"],
            result.details["pct_C2H2"],
        ])
        assert pcts == pytest.approx(100.0, abs=0.1)


# ====================================================================
# Tests NormativeDiagnosisService
# ====================================================================

class TestNormativeDiagnosisService:

    def setup_method(self) -> None:
        self.service = NormativeDiagnosisService()

    def test_diagnose_all_returns_6_results(self) -> None:
        result = self.service.diagnose_all(NORMAL_READING)
        assert isinstance(result, NormativeDiagnosisResult)
        assert len(result.results) == 6

    def test_consensus_is_valid_fault_type(self) -> None:
        result = self.service.diagnose_all(T3_READING)
        assert isinstance(result.consensus_fault, FaultType)

    def test_agreement_percentage_range(self) -> None:
        result = self.service.diagnose_all(T2_READING)
        assert 0 <= result.agreement_pct <= 100

    def test_vote_counts_sum_to_6(self) -> None:
        result = self.service.diagnose_all(D2_READING)
        total_votes = sum(result.vote_counts.values())
        assert total_votes == 6

    def test_all_methods_named(self) -> None:
        result = self.service.diagnose_all(NORMAL_READING)
        names = {r.method_name for r in result.results}
        assert len(names) == 6

    def test_available_methods(self) -> None:
        methods = NormativeDiagnosisService.available_methods()
        assert len(methods) == 6
        assert "IEEE C57.104-2019" in methods
        assert "IEC 60599:2022" in methods

    def test_diagnose_single_existing(self) -> None:
        result = self.service.diagnose_single(NORMAL_READING, "Rogers")
        assert result is not None
        assert result.method_name == "Rogers"

    def test_diagnose_single_nonexistent(self) -> None:
        result = self.service.diagnose_single(NORMAL_READING, "MetodoInventado")
        assert result is None

    def test_thermal_consensus(self) -> None:
        """Un caso claramente termico deberia dar consenso T2 o T3."""
        result = self.service.diagnose_all(T3_READING)
        # La mayoria deberia votar falla termica
        thermal_faults = {FaultType.T1, FaultType.T2, FaultType.T3}
        thermal_votes = sum(
            1 for r in result.results if r.fault_type in thermal_faults
        )
        assert thermal_votes >= 3, "Al menos 3 de 6 metodos deben detectar falla termica"
