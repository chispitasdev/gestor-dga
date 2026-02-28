"""Tests unitarios para gas_ratios.py."""

import pytest

from src.dga.domain.models.gas_reading import GasReading
from src.dga.application.services.normative_methods.gas_ratios import (
    safe_ratio,
    ratio_ch4_h2,
    ratio_c2h2_c2h4,
    ratio_c2h4_c2h6,
    ratio_c2h6_ch4,
    ratio_c2h2_ch4,
    ratio_co2_co,
    total_combustible_gases,
    total_hydrocarbons,
    duval_triangle_percentages,
    duval_pentagon_percentages,
)


def _make_reading(**kwargs: float) -> GasReading:
    """Crea un GasReading con valores por defecto en 0."""
    defaults: dict[str, float] = {
        "h2": 0.0, "ch4": 0.0, "c2h6": 0.0, "c2h4": 0.0, "c2h2": 0.0,
        "co": 0.0, "co2": 0.0, "o2": 0.0, "n2": 0.0,
    }
    defaults.update(kwargs)
    return GasReading(**defaults)


class TestSafeRatio:

    def test_normal_division(self) -> None:
        assert safe_ratio(10, 5) == 2.0

    def test_zero_denominator_with_positive_numerator(self) -> None:
        assert safe_ratio(10, 0) == 999.0

    def test_negative_denominator_with_positive_numerator(self) -> None:
        assert safe_ratio(10, -1) == 999.0

    def test_zero_denominator_and_zero_numerator(self) -> None:
        assert safe_ratio(0, 0) == 0.0

    def test_zero_numerator(self) -> None:
        assert safe_ratio(0, 5) == 0.0


class TestGasRatios:

    def test_ratio_ch4_h2(self) -> None:
        r = _make_reading(ch4=120, h2=60)
        assert ratio_ch4_h2(r) == pytest.approx(2.0)

    def test_ratio_c2h2_c2h4(self) -> None:
        r = _make_reading(c2h2=5, c2h4=25)
        assert ratio_c2h2_c2h4(r) == pytest.approx(0.2)

    def test_ratio_c2h4_c2h6(self) -> None:
        r = _make_reading(c2h4=300, c2h6=100)
        assert ratio_c2h4_c2h6(r) == pytest.approx(3.0)

    def test_ratio_c2h6_ch4(self) -> None:
        r = _make_reading(c2h6=50, ch4=100)
        assert ratio_c2h6_ch4(r) == pytest.approx(0.5)

    def test_ratio_c2h2_ch4(self) -> None:
        r = _make_reading(c2h2=10, ch4=100)
        assert ratio_c2h2_ch4(r) == pytest.approx(0.1)

    def test_ratio_co2_co(self) -> None:
        r = _make_reading(co2=3000, co=300)
        assert ratio_co2_co(r) == pytest.approx(10.0)


class TestTotals:

    def test_total_combustible_gases(self) -> None:
        r = _make_reading(h2=100, ch4=50, c2h6=30, c2h4=20, c2h2=10, co=90)
        assert total_combustible_gases(r) == pytest.approx(300.0)

    def test_total_hydrocarbons(self) -> None:
        r = _make_reading(ch4=50, c2h6=30, c2h4=20, c2h2=10)
        assert total_hydrocarbons(r) == pytest.approx(110.0)


class TestDuvalPercentages:

    def test_triangle_normal(self) -> None:
        r = _make_reading(ch4=60, c2h4=30, c2h2=10)
        pct_ch4, pct_c2h4, pct_c2h2 = duval_triangle_percentages(r)
        assert pct_ch4 == pytest.approx(60.0)
        assert pct_c2h4 == pytest.approx(30.0)
        assert pct_c2h2 == pytest.approx(10.0)

    def test_triangle_all_zero(self) -> None:
        r = _make_reading()
        assert duval_triangle_percentages(r) == (0.0, 0.0, 0.0)

    def test_pentagon_normal(self) -> None:
        r = _make_reading(h2=20, ch4=20, c2h6=20, c2h4=20, c2h2=20)
        pcts = duval_pentagon_percentages(r)
        assert all(p == pytest.approx(20.0) for p in pcts)

    def test_pentagon_all_zero(self) -> None:
        r = _make_reading()
        assert duval_pentagon_percentages(r) == (0.0, 0.0, 0.0, 0.0, 0.0)
