"""Servicio de diagnostico unificado: normativo + IA.

Combina los resultados de los 6 metodos normativos con la prediccion
del motor de inteligencia artificial en un reporte consolidado.
Permite comparar ambos enfoques y medir su nivel de concordancia.

Ejemplo de uso:
    >>> result = unified_service.diagnose(sample)
    >>> print(result.normative_fault, result.ai_fault, result.agree)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.dga.domain.models.fault_type import FaultType
from src.dga.domain.models.sample import Sample
from src.dga.application.services.normative_diagnosis_service import (
    NormativeDiagnosisService,
    NormativeDiagnosisResult,
)
from src.dga.application.services.ai_engine.ai_service import AIService


@dataclass(frozen=True, slots=True)
class UnifiedDiagnosisResult:
    """Resultado consolidado de un diagnostico unificado.

    Attributes:
        sample: Muestra diagnosticada.
        normative: Resultado completo del diagnostico normativo.
        ai_fault: Falla predicha por IA (None si no hay modelo).
        ai_probabilities: Probabilidades por clase de la IA (None si no hay modelo).
        agree: True si el consenso normativo y la IA coinciden.
    """

    sample: Sample
    normative: NormativeDiagnosisResult
    ai_fault: Optional[FaultType] = None
    ai_probabilities: Optional[dict[FaultType, float]] = None
    agree: Optional[bool] = None


@dataclass(frozen=True, slots=True)
class ComparisonSummary:
    """Resumen comparativo normativo vs. IA sobre multiples muestras.

    Attributes:
        total: Numero total de muestras comparadas.
        agreements: Cantidad de coincidencias.
        disagreements: Cantidad de discrepancias.
        agreement_pct: Porcentaje de concordancia.
        details: Lista de resultados individuales.
    """

    total: int
    agreements: int
    disagreements: int
    agreement_pct: float
    details: list[UnifiedDiagnosisResult]


class UnifiedDiagnosisService:
    """Servicio que unifica diagnostico normativo e IA.

    Ejecuta ambas estrategias sobre una muestra y produce un
    resultado consolidado con nivel de concordancia.
    """

    def __init__(
        self,
        normative_service: NormativeDiagnosisService,
        ai_service: AIService,
    ) -> None:
        self._normative = normative_service
        self._ai = ai_service

    def diagnose(self, sample: Sample) -> UnifiedDiagnosisResult:
        """Diagnostica una muestra con ambos enfoques.

        Args:
            sample: Muestra a diagnosticar.

        Returns:
            UnifiedDiagnosisResult con normativo, IA y concordancia.
        """
        reading = sample.gas_reading

        # Diagnostico normativo (siempre disponible)
        normative = self._normative.diagnose_all(reading)

        # Diagnostico IA (solo si hay modelo)
        ai_fault: Optional[FaultType] = None
        ai_probs: Optional[dict[FaultType, float]] = None
        agree: Optional[bool] = None

        if self._ai.has_model():
            try:
                ai_fault, ai_probs = self._ai.classify_with_proba(reading)
                agree = normative.consensus_fault == ai_fault
            except (RuntimeError, AttributeError):
                try:
                    ai_fault = self._ai.classify(reading)
                    agree = normative.consensus_fault == ai_fault
                except RuntimeError:
                    pass

        return UnifiedDiagnosisResult(
            sample=sample,
            normative=normative,
            ai_fault=ai_fault,
            ai_probabilities=ai_probs,
            agree=agree,
        )

    def diagnose_batch(
        self, samples: list[Sample]
    ) -> list[UnifiedDiagnosisResult]:
        """Diagnostica multiples muestras.

        Args:
            samples: Lista de muestras.

        Returns:
            Lista de UnifiedDiagnosisResult.
        """
        return [self.diagnose(s) for s in samples]

    def compare(self, samples: list[Sample]) -> ComparisonSummary:
        """Compara normativo vs. IA en un conjunto de muestras.

        Args:
            samples: Lista de muestras a comparar.

        Returns:
            ComparisonSummary con estadisticas de concordancia.
        """
        details = self.diagnose_batch(samples)

        # Solo contar las que tienen ambos diagnosticos
        comparable = [d for d in details if d.agree is not None]
        total = len(comparable)
        agreements = sum(1 for d in comparable if d.agree)
        disagreements = total - agreements
        pct = round((agreements / total) * 100, 1) if total > 0 else 0.0

        return ComparisonSummary(
            total=total,
            agreements=agreements,
            disagreements=disagreements,
            agreement_pct=pct,
            details=details,
        )

    @staticmethod
    def format_unified_report(result: UnifiedDiagnosisResult) -> str:
        """Formatea un resultado unificado como texto para consola.

        Args:
            result: Resultado a formatear.

        Returns:
            String con el reporte legible.
        """
        s = result.sample
        n = result.normative
        lines: list[str] = []

        lines.append(f"\n{'='*60}")
        lines.append("  DIAGNOSTICO UNIFICADO")
        lines.append(f"{'='*60}")
        lines.append(f"  Muestra    : {s.sample_code} (ID {s.id})")
        lines.append(f"  Fecha      : {s.extraction_date}")
        lines.append(f"  Transf. ID : {s.transformer_id}")
        lines.append(f"{'-'*60}")

        # Normativo
        lines.append("\n  --- Diagnostico Normativo ---")
        lines.append(f"  {'Metodo':<25} {'Falla':<30}")
        lines.append(f"  {'-'*55}")
        for mr in n.results:
            lines.append(f"  {mr.method_name:<25} {mr.fault_type!s:<30}")
        lines.append(f"  {'-'*55}")
        lines.append(
            f"  Consenso: {n.consensus_fault!s} "
            f"({n.agreement_pct:.0f}% acuerdo)"
        )

        # IA
        lines.append("\n  --- Diagnostico IA ---")
        if result.ai_fault is not None:
            lines.append(f"  Prediccion: {result.ai_fault!s}")
            if result.ai_probabilities:
                lines.append(f"\n  {'Clase':<25} {'Prob':>8}")
                lines.append(f"  {'-'*34}")
                sorted_probs = sorted(
                    result.ai_probabilities.items(),
                    key=lambda x: x[1],
                    reverse=True,
                )
                for ft, p in sorted_probs:
                    if p > 0.01:
                        lines.append(f"  {ft!s:<25} {p:>8.2%}")
        else:
            lines.append("  (No hay modelo de IA entrenado)")

        # Concordancia
        lines.append("\n  --- Concordancia ---")
        if result.agree is not None:
            symbol = "SI" if result.agree else "NO"
            lines.append(
                f"  Normativo: {n.consensus_fault.name:<6} | "
                f"IA: {result.ai_fault.name if result.ai_fault else '?':<6} | "
                f"Coinciden: {symbol}"
            )
        else:
            lines.append("  (Comparacion no disponible sin modelo IA)")

        lines.append(f"{'='*60}")
        return "\n".join(lines)

    @staticmethod
    def format_comparison_table(summary: ComparisonSummary) -> str:
        """Formatea un resumen comparativo como tabla.

        Args:
            summary: Resumen de comparacion.

        Returns:
            String con la tabla formateada.
        """
        lines: list[str] = []
        lines.append(f"\n{'='*72}")
        lines.append("  COMPARACION NORMATIVO vs. IA")
        lines.append(f"{'='*72}")
        lines.append(
            f"  Total muestras: {summary.total}  |  "
            f"Coinciden: {summary.agreements}  |  "
            f"Difieren: {summary.disagreements}  |  "
            f"Concordancia: {summary.agreement_pct:.1f}%"
        )
        lines.append(f"{'-'*72}")
        lines.append(
            f"  {'Muestra':<15} {'Fecha':>12} "
            f"{'Normativo':<15} {'IA':<15} {'Ok?':>5}"
        )
        lines.append(f"  {'-'*64}")

        for d in summary.details:
            norm_name = d.normative.consensus_fault.name
            ai_name = d.ai_fault.name if d.ai_fault else "---"
            ok = "SI" if d.agree else ("NO" if d.agree is not None else "---")
            lines.append(
                f"  {d.sample.sample_code:<15} "
                f"{d.sample.extraction_date!s:>12} "
                f"{norm_name:<15} {ai_name:<15} {ok:>5}"
            )

        lines.append(f"{'='*72}")
        return "\n".join(lines)
