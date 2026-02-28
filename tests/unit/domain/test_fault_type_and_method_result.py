"""Tests unitarios para FaultType y MethodResult."""

import pytest

from src.dga.domain.models.fault_type import FaultType
from src.dga.domain.models.method_result import MethodResult


class TestFaultType:
    """Pruebas del enum FaultType."""

    def test_all_fault_types_exist(self) -> None:
        expected = {"N", "PD", "D1", "D2", "T1", "T2", "T3", "DT", "S"}
        actual = {ft.name for ft in FaultType}
        assert actual == expected

    def test_normal_value(self) -> None:
        assert FaultType.N.value == "Normal"

    def test_str_representation(self) -> None:
        assert "PD" in str(FaultType.PD)
        assert "Descargas parciales" in str(FaultType.PD)

    def test_enum_identity(self) -> None:
        assert FaultType.D1 is FaultType.D1
        assert FaultType.D1 == FaultType.D1
        assert FaultType.D1 != FaultType.D2


class TestMethodResult:
    """Pruebas del value object MethodResult."""

    def test_creation(self) -> None:
        result = MethodResult(
            method_name="Test",
            fault_type=FaultType.N,
            description="Prueba",
            details={"key": "value"},
        )
        assert result.method_name == "Test"
        assert result.fault_type == FaultType.N
        assert result.description == "Prueba"
        assert result.details == {"key": "value"}

    def test_immutable(self) -> None:
        result = MethodResult(method_name="Test", fault_type=FaultType.N)
        with pytest.raises(AttributeError):
            result.method_name = "Otro"  # type: ignore[misc]

    def test_default_values(self) -> None:
        result = MethodResult(method_name="Test", fault_type=FaultType.T1)
        assert result.description == ""
        assert result.details == {}

    def test_str(self) -> None:
        result = MethodResult(
            method_name="IEEE", fault_type=FaultType.D2, description="Arco"
        )
        text = str(result)
        assert "IEEE" in text
        assert "D2" in text
