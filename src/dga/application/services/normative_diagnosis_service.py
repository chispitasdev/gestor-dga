"""Servicio de diagnostico normativo unificado.

Orquesta la ejecucion de los 6 metodos normativos sobre una lectura
de gases y produce un resumen con todos los resultados individuales
mas un diagnostico por consenso (voto mayoritario).

Metodos implementados:
    1. IEEE C57.104-2019
    2. IEC 60599:2022
    3. Rogers
    4. Dornenburg
    5. Triangulo de Duval 1
    6. Pentagono de Duval 1
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

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


@dataclass(frozen=True, slots=True)
class NormativeDiagnosisResult:
    """Resultado completo del diagnostico normativo.

    Attributes:
        results: Lista de resultados individuales por metodo.
        consensus_fault: Tipo de falla por consenso (voto mayoritario).
        vote_counts: Conteo de votos por tipo de falla.
        agreement_pct: Porcentaje de acuerdo del consenso.
    """

    results: list[MethodResult]
    consensus_fault: FaultType
    vote_counts: dict[str, int]
    agreement_pct: float


class NormativeDiagnosisService:
    """Servicio que ejecuta todos los metodos normativos y calcula consenso.

    Es una clase sin estado (stateless) que no depende de repositorios
    ni infraestructura — opera unicamente sobre el value object GasReading.
    """

    # Funciones de diagnostico registradas (cada una: GasReading -> MethodResult)
    _METHODS = [
        ieee_c57_104.diagnose,
        iec_60599.diagnose,
        rogers.diagnose,
        dornenburg.diagnose,
        duval_triangle.diagnose,
        duval_pentagon.diagnose,
    ]

    def diagnose_all(self, reading: GasReading) -> NormativeDiagnosisResult:
        """Ejecuta los 6 metodos normativos y calcula consenso.

        Args:
            reading: Lectura de gases disueltos.

        Returns:
            NormativeDiagnosisResult con todos los resultados y el consenso.
        """
        results = [method(reading) for method in self._METHODS]
        consensus, counts, pct = self._compute_consensus(results)

        return NormativeDiagnosisResult(
            results=results,
            consensus_fault=consensus,
            vote_counts=counts,
            agreement_pct=pct,
        )

    def diagnose_single(
        self, reading: GasReading, method_name: str
    ) -> MethodResult | None:
        """Ejecuta un metodo normativo especifico por nombre.

        Args:
            reading: Lectura de gases disueltos.
            method_name: Nombre del metodo (ej.: "IEEE C57.104-2019").

        Returns:
            MethodResult del metodo solicitado, o None si no existe.
        """
        for method in self._METHODS:
            result = method(reading)
            if result.method_name.lower() == method_name.lower():
                return result
        return None

    @staticmethod
    def _compute_consensus(
        results: list[MethodResult],
    ) -> tuple[FaultType, dict[str, int], float]:
        """Calcula el tipo de falla por voto mayoritario.

        Returns:
            Tupla (fault_type_ganador, conteo_votos, porcentaje_acuerdo).
        """
        votes = [r.fault_type for r in results]
        counter = Counter(votes)
        total = len(votes)

        # Falla mas votada
        most_common_fault, most_common_count = counter.most_common(1)[0]

        vote_dict = {ft.name: count for ft, count in counter.items()}
        agreement = (most_common_count / total) * 100 if total > 0 else 0.0

        return most_common_fault, vote_dict, round(agreement, 1)

    @staticmethod
    def available_methods() -> list[str]:
        """Retorna los nombres de los metodos implementados."""
        return [
            ieee_c57_104.METHOD_NAME,
            iec_60599.METHOD_NAME,
            rogers.METHOD_NAME,
            dornenburg.METHOD_NAME,
            duval_triangle.METHOD_NAME,
            duval_pentagon.METHOD_NAME,
        ]
