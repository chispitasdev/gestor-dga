"""Tests unitarios para TrendService."""

import pytest

from datetime import date

from src.dga.domain.models.gas_reading import GasReading
from src.dga.domain.models.sample import Sample
from src.dga.application.services.trend_service import (
    TrendService,
    TrendAnalysis,
)


def _make_sample(
    sample_id: int,
    code: str,
    transformer_id: int,
    extraction_date: date,
    h2: float = 50, ch4: float = 30, c2h6: float = 20,
    c2h4: float = 10, c2h2: float = 1, co: float = 100,
    co2: float = 2000, o2: float = 18000, n2: float = 50000,
) -> Sample:
    """Crea una muestra de prueba."""
    return Sample(
        sample_code=code,
        transformer_id=transformer_id,
        extraction_date=extraction_date,
        gas_reading=GasReading(
            h2=h2, ch4=ch4, c2h6=c2h6, c2h4=c2h4, c2h2=c2h2,
            co=co, co2=co2, o2=o2, n2=n2,
        ),
        id=sample_id,
    )


class TestAnalyzePair:

    def test_basic_rate_calculation(self) -> None:
        prev = _make_sample(1, "M-001", 1, date(2024, 1, 1), h2=100)
        curr = _make_sample(2, "M-002", 1, date(2024, 1, 11), h2=200)

        result = TrendService.analyze_pair(prev, curr)

        assert isinstance(result, TrendAnalysis)
        assert result.days_between == 10
        assert result.transformer_id == 1

        h2_rate = next(r for r in result.gas_rates if r.gas_name == "h2")
        assert h2_rate.delta_ppm == 100.0
        assert h2_rate.rate_ppm_day == pytest.approx(10.0)
        assert h2_rate.is_increasing is True

    def test_decreasing_gas(self) -> None:
        prev = _make_sample(1, "M-001", 1, date(2024, 1, 1), h2=200)
        curr = _make_sample(2, "M-002", 1, date(2024, 1, 11), h2=100)

        result = TrendService.analyze_pair(prev, curr)
        h2_rate = next(r for r in result.gas_rates if r.gas_name == "h2")
        assert h2_rate.is_increasing is False
        assert h2_rate.delta_ppm == -100.0

    def test_critical_gas_detection(self) -> None:
        # H2 de 0 a 100 en 1 dia -> tasa 100 ppm/dia (umbral critico: 5)
        prev = _make_sample(1, "M-001", 1, date(2024, 1, 1), h2=0)
        curr = _make_sample(2, "M-002", 1, date(2024, 1, 2), h2=100)

        result = TrendService.analyze_pair(prev, curr)
        assert "h2" in result.critical_gases

    def test_different_transformer_raises(self) -> None:
        prev = _make_sample(1, "M-001", 1, date(2024, 1, 1))
        curr = _make_sample(2, "M-002", 2, date(2024, 1, 11))

        with pytest.raises(ValueError, match="mismo transformador"):
            TrendService.analyze_pair(prev, curr)

    def test_same_date_raises(self) -> None:
        prev = _make_sample(1, "M-001", 1, date(2024, 1, 1))
        curr = _make_sample(2, "M-002", 1, date(2024, 1, 1))

        with pytest.raises(ValueError, match="posterior"):
            TrendService.analyze_pair(prev, curr)

    def test_returns_9_gas_rates(self) -> None:
        prev = _make_sample(1, "M-001", 1, date(2024, 1, 1))
        curr = _make_sample(2, "M-002", 1, date(2024, 1, 11))

        result = TrendService.analyze_pair(prev, curr)
        assert len(result.gas_rates) == 9

    def test_increasing_gases_list(self) -> None:
        prev = _make_sample(1, "M-001", 1, date(2024, 1, 1), h2=50, ch4=30)
        curr = _make_sample(2, "M-002", 1, date(2024, 1, 11), h2=100, ch4=30)

        result = TrendService.analyze_pair(prev, curr)
        assert "h2" in result.increasing_gases
        assert "ch4" not in result.increasing_gases


class TestBuildGasHistory:

    def test_empty_list(self) -> None:
        assert TrendService.build_gas_history([]) == []

    def test_single_sample(self) -> None:
        samples = [_make_sample(1, "M-001", 1, date(2024, 1, 1))]
        histories = TrendService.build_gas_history(samples)
        assert len(histories) == 9
        assert len(histories[0].dates) == 1

    def test_ordered_by_date(self) -> None:
        s1 = _make_sample(1, "M-001", 1, date(2024, 3, 1), h2=300)
        s2 = _make_sample(2, "M-002", 1, date(2024, 1, 1), h2=100)
        s3 = _make_sample(3, "M-003", 1, date(2024, 2, 1), h2=200)

        histories = TrendService.build_gas_history([s1, s2, s3])
        h2_hist = next(h for h in histories if h.gas_name == "h2")

        # Debe estar ordenado por fecha
        assert h2_hist.dates == [date(2024, 1, 1), date(2024, 2, 1), date(2024, 3, 1)]
        assert h2_hist.values == [100, 200, 300]


class TestComputeAllRates:

    def test_less_than_2_samples(self) -> None:
        s1 = _make_sample(1, "M-001", 1, date(2024, 1, 1))
        assert TrendService.compute_all_rates([s1]) == []
        assert TrendService.compute_all_rates([]) == []

    def test_three_samples_gives_two_analyses(self) -> None:
        s1 = _make_sample(1, "M-001", 1, date(2024, 1, 1))
        s2 = _make_sample(2, "M-002", 1, date(2024, 2, 1))
        s3 = _make_sample(3, "M-003", 1, date(2024, 3, 1))

        analyses = TrendService.compute_all_rates([s3, s1, s2])  # desordenado
        assert len(analyses) == 2
        assert analyses[0].sample_from.id == 1
        assert analyses[0].sample_to.id == 2
