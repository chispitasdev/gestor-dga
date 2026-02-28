"""Servicio de analisis de tendencias de gases disueltos.

Calcula tasas de generacion de gas entre muestras consecutivas de un
mismo transformador, identifica gases con crecimiento anormal y provee
datos tabulares para visualizacion de tendencias.

La tasa de generacion se expresa en ppm/dia y se calcula como:
    tasa = (concentracion_actual - concentracion_anterior) / dias_transcurridos
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from src.dga.domain.models.gas_reading import GasReading
from src.dga.domain.models.sample import Sample


@dataclass(frozen=True, slots=True)
class GasRate:
    """Tasa de generacion de un gas individual entre dos muestras.

    Attributes:
        gas_name: Nombre del gas (ej. 'h2').
        gas_label: Etiqueta descriptiva (ej. 'Hidrogeno (H2)').
        previous_ppm: Concentracion en la muestra anterior.
        current_ppm: Concentracion en la muestra actual.
        delta_ppm: Diferencia absoluta (current - previous).
        days: Dias transcurridos entre muestras.
        rate_ppm_day: Tasa de generacion en ppm/dia.
        is_increasing: True si la concentracion esta subiendo.
    """

    gas_name: str
    gas_label: str
    previous_ppm: float
    current_ppm: float
    delta_ppm: float
    days: int
    rate_ppm_day: float
    is_increasing: bool


@dataclass(frozen=True, slots=True)
class TrendAnalysis:
    """Resultado completo del analisis de tendencia entre dos muestras.

    Attributes:
        transformer_id: ID del transformador analizado.
        sample_from: Muestra anterior (referencia).
        sample_to: Muestra actual.
        days_between: Dias entre las dos muestras.
        gas_rates: Lista de tasas por gas.
        increasing_gases: Gases con tasa positiva (creciendo).
        critical_gases: Gases que superan el umbral de tasa critica.
    """

    transformer_id: int
    sample_from: Sample
    sample_to: Sample
    days_between: int
    gas_rates: list[GasRate]
    increasing_gases: list[str]
    critical_gases: list[str]


@dataclass(frozen=True, slots=True)
class GasHistory:
    """Historial de un gas a traves de multiples muestras.

    Attributes:
        gas_name: Nombre del gas.
        gas_label: Etiqueta descriptiva.
        dates: Lista de fechas de extraccion.
        values: Lista de concentraciones (ppm), alineada con dates.
    """

    gas_name: str
    gas_label: str
    dates: list[date]
    values: list[float]


# ── Umbrales de tasa critica (ppm/dia) segun IEEE C57.104 ──────────
# Si la tasa de generacion supera estos valores, se considera anormal.
_CRITICAL_RATES: dict[str, float] = {
    "h2": 5.0,
    "ch4": 3.0,
    "c2h6": 3.0,
    "c2h4": 3.0,
    "c2h2": 0.5,
    "co": 10.0,
    "co2": 50.0,
    "o2": 0.0,   # no aplica para O2
    "n2": 0.0,   # no aplica para N2
}


class TrendService:
    """Servicio para analisis de tendencias de gases.

    Es un servicio sin estado — no depende de repositorios. Opera
    directamente sobre listas de muestras proporcionadas por el caller.
    """

    @staticmethod
    def analyze_pair(
        previous: Sample, current: Sample
    ) -> TrendAnalysis:
        """Analiza la tendencia entre dos muestras consecutivas.

        Args:
            previous: Muestra anterior (mas antigua).
            current: Muestra posterior (mas reciente).

        Returns:
            TrendAnalysis con las tasas de generacion por gas.

        Raises:
            ValueError: Si las muestras no son del mismo transformador
                o la muestra actual no es posterior a la anterior.
        """
        if previous.transformer_id != current.transformer_id:
            raise ValueError(
                "Las muestras deben pertenecer al mismo transformador."
            )

        days = (current.extraction_date - previous.extraction_date).days
        if days <= 0:
            raise ValueError(
                "La muestra actual debe tener fecha posterior a la anterior."
            )

        labels = GasReading.descriptive_labels()
        gas_rates: list[GasRate] = []
        increasing: list[str] = []
        critical: list[str] = []

        for gas_name in GasReading.field_names():
            prev_val = getattr(previous.gas_reading, gas_name)
            curr_val = getattr(current.gas_reading, gas_name)
            delta = curr_val - prev_val
            rate = delta / days

            is_inc = delta > 0
            if is_inc:
                increasing.append(gas_name)

            crit_threshold = _CRITICAL_RATES.get(gas_name, 0.0)
            if crit_threshold > 0 and rate > crit_threshold:
                critical.append(gas_name)

            gas_rates.append(GasRate(
                gas_name=gas_name,
                gas_label=labels[gas_name],
                previous_ppm=prev_val,
                current_ppm=curr_val,
                delta_ppm=round(delta, 2),
                days=days,
                rate_ppm_day=round(rate, 4),
                is_increasing=is_inc,
            ))

        return TrendAnalysis(
            transformer_id=current.transformer_id,
            sample_from=previous,
            sample_to=current,
            days_between=days,
            gas_rates=gas_rates,
            increasing_gases=increasing,
            critical_gases=critical,
        )

    @staticmethod
    def build_gas_history(
        samples: list[Sample],
    ) -> list[GasHistory]:
        """Construye el historial temporal de cada gas a partir de muestras.

        Las muestras se ordenan por fecha de extraccion.

        Args:
            samples: Lista de muestras del mismo transformador.

        Returns:
            Lista de GasHistory, uno por cada gas.
        """
        if not samples:
            return []

        sorted_samples = sorted(samples, key=lambda s: s.extraction_date)
        labels = GasReading.descriptive_labels()
        histories: list[GasHistory] = []

        for gas_name in GasReading.field_names():
            dates = [s.extraction_date for s in sorted_samples]
            values = [
                getattr(s.gas_reading, gas_name) for s in sorted_samples
            ]
            histories.append(GasHistory(
                gas_name=gas_name,
                gas_label=labels[gas_name],
                dates=dates,
                values=values,
            ))

        return histories

    @staticmethod
    def compute_all_rates(
        samples: list[Sample],
    ) -> list[TrendAnalysis]:
        """Calcula las tasas de generacion entre cada par consecutivo.

        Args:
            samples: Muestras del mismo transformador, en cualquier orden.

        Returns:
            Lista de TrendAnalysis entre pares consecutivos (ordenados por fecha).
        """
        if len(samples) < 2:
            return []

        sorted_samples = sorted(samples, key=lambda s: s.extraction_date)
        analyses: list[TrendAnalysis] = []

        for i in range(len(sorted_samples) - 1):
            prev = sorted_samples[i]
            curr = sorted_samples[i + 1]
            days = (curr.extraction_date - prev.extraction_date).days
            if days > 0:
                analyses.append(TrendService.analyze_pair(prev, curr))

        return analyses
