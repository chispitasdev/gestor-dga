"""Servicio de validacion y generacion de reportes para la tesis (Cap. 5).

Produce:
    1. Resumen estadistico del dataset (n muestras, distribucion por falla,
       estadisticas descriptivas por gas).
    2. Tabla comparativa de los 4 modelos (Accuracy, Precision, Recall, F1).
    3. Metricas detalladas por clase del mejor modelo.
    4. Analisis de concordancia normativo vs. IA.
    5. Exportacion a CSV de todas las tablas para inclusion en LaTeX.

Disenado para ser invocado desde la CLI de validacion (opcion 9 del menu).
"""

from __future__ import annotations

import csv
from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import numpy as np

from src.dga.domain.models.sample import Sample
from src.dga.application.services.normative_diagnosis_service import (
    NormativeDiagnosisService,
)
from src.dga.application.services.ai_engine.ai_service import AIService
from src.dga.application.services.ai_engine.data_preparation import (
    FEATURE_NAMES,
    extract_features,
)
from src.dga.application.services.ai_engine.model_evaluator import (
    EvaluationResult,
    ModelEvaluator,
)
from src.dga.application.services.unified_diagnosis_service import (
    ComparisonSummary,
    UnifiedDiagnosisService,
)


# ================================================================== #
#  Dataclasses de resultado
# ================================================================== #


@dataclass(frozen=True, slots=True)
class GasStatistics:
    """Estadisticas descriptivas de un gas en el dataset.

    Attributes:
        gas_name: Nombre del gas (ej.: h2).
        min: Valor minimo (ppm).
        max: Valor maximo (ppm).
        mean: Media aritmetica (ppm).
        std: Desviacion estandar (ppm).
        median: Mediana (ppm).
    """

    gas_name: str
    min: float
    max: float
    mean: float
    std: float
    median: float


@dataclass(frozen=True, slots=True)
class DatasetSummary:
    """Resumen estadistico del dataset.

    Attributes:
        total_samples: Cantidad total de muestras.
        date_range: Rango de fechas (min, max).
        fault_distribution: Conteo por tipo de falla.
        gas_stats: Estadisticas por gas.
        n_transformers: Cantidad de transformadores distintos.
    """

    total_samples: int
    date_range: tuple[date, date] | None
    fault_distribution: dict[str, int]
    gas_stats: list[GasStatistics]
    n_transformers: int


@dataclass(frozen=True, slots=True)
class ModelComparisonRow:
    """Fila de la tabla comparativa de modelos.

    Attributes:
        model_name: Nombre del algoritmo.
        accuracy: Accuracy global.
        macro_precision: Precision macro.
        macro_recall: Recall macro.
        macro_f1: F1-score macro.
        weighted_f1: F1-score ponderado.
    """

    model_name: str
    accuracy: float
    macro_precision: float
    macro_recall: float
    macro_f1: float
    weighted_f1: float


@dataclass(frozen=True, slots=True)
class ValidationReport:
    """Reporte completo de validacion para la tesis.

    Attributes:
        dataset_summary: Resumen del dataset.
        model_comparisons: Tabla comparativa de modelos.
        best_model_eval: Evaluacion detallada del mejor modelo.
        concordance: Resumen de concordancia normativo vs. IA.
    """

    dataset_summary: DatasetSummary
    model_comparisons: list[ModelComparisonRow]
    best_model_eval: EvaluationResult | None
    concordance: ComparisonSummary | None


# ================================================================== #
#  Servicio de validacion
# ================================================================== #


class ValidationService:
    """Genera datos de validacion y reportes para el Capitulo 5."""

    def __init__(
        self,
        normative_service: NormativeDiagnosisService,
        ai_service: AIService,
        unified_service: UnifiedDiagnosisService,
    ) -> None:
        self._normative = normative_service
        self._ai = ai_service
        self._unified = unified_service

    # -------------------------------------------------------------- #
    #  1. Resumen del dataset
    # -------------------------------------------------------------- #

    def build_dataset_summary(
        self, samples: list[Sample]
    ) -> DatasetSummary:
        """Calcula estadisticas descriptivas del dataset.

        Args:
            samples: Todas las muestras cargadas.

        Returns:
            DatasetSummary con distribucion y estadisticas por gas.
        """
        if not samples:
            return DatasetSummary(
                total_samples=0,
                date_range=None,
                fault_distribution={},
                gas_stats=[],
                n_transformers=0,
            )

        # Distribucion de fallas (via consenso normativo)
        fault_counts: Counter[str] = Counter()
        for s in samples:
            diag = self._normative.diagnose_all(s.gas_reading)
            fault_counts[diag.consensus_fault.name] += 1

        # Rango de fechas
        dates = [s.extraction_date for s in samples]
        date_range = (min(dates), max(dates))

        # Transformadores distintos
        n_transformers = len({s.transformer_id for s in samples})

        # Estadisticas por gas
        feature_matrix = np.array(
            [extract_features(s.gas_reading) for s in samples]
        )
        gas_stats: list[GasStatistics] = []
        for i, name in enumerate(FEATURE_NAMES):
            col = feature_matrix[:, i]
            gas_stats.append(GasStatistics(
                gas_name=name,
                min=round(float(np.min(col)), 2),
                max=round(float(np.max(col)), 2),
                mean=round(float(np.mean(col)), 2),
                std=round(float(np.std(col)), 2),
                median=round(float(np.median(col)), 2),
            ))

        return DatasetSummary(
            total_samples=len(samples),
            date_range=date_range,
            fault_distribution=dict(fault_counts.most_common()),
            gas_stats=gas_stats,
            n_transformers=n_transformers,
        )

    # -------------------------------------------------------------- #
    #  2. Tabla comparativa de modelos
    # -------------------------------------------------------------- #

    def evaluate_all_models(
        self, samples: list[Sample] | None = None
    ) -> tuple[list[ModelComparisonRow], list[EvaluationResult]]:
        """Evalua los 4 modelos y retorna tabla comparativa.

        Args:
            samples: Muestras para evaluacion (None = todas del repo).

        Returns:
            Tupla (filas comparativas, evaluaciones detalladas).
        """
        eval_results = self._ai.evaluate_all(samples)

        rows: list[ModelComparisonRow] = []
        for ev in eval_results:
            rows.append(ModelComparisonRow(
                model_name=ev.model_name,
                accuracy=ev.overall_accuracy,
                macro_precision=ev.macro_precision,
                macro_recall=ev.macro_recall,
                macro_f1=ev.macro_f1,
                weighted_f1=ev.weighted_f1,
            ))

        return rows, eval_results

    # -------------------------------------------------------------- #
    #  3. Concordancia normativo vs. IA
    # -------------------------------------------------------------- #

    def concordance_analysis(
        self, samples: list[Sample]
    ) -> ComparisonSummary:
        """Ejecuta el analisis de concordancia normativo vs. IA.

        Args:
            samples: Muestras a comparar.

        Returns:
            ComparisonSummary del servicio unificado.
        """
        return self._unified.compare(samples)

    # -------------------------------------------------------------- #
    #  4. Reporte completo
    # -------------------------------------------------------------- #

    def full_validation(
        self, samples: list[Sample]
    ) -> ValidationReport:
        """Genera el reporte completo de validacion.

        Args:
            samples: Muestras para validar.

        Returns:
            ValidationReport con todas las secciones.
        """
        summary = self.build_dataset_summary(samples)
        rows, eval_results = self.evaluate_all_models(samples)

        best_eval = eval_results[0] if eval_results else None
        concordance = (
            self.concordance_analysis(samples) if self._ai.has_model() else None
        )

        return ValidationReport(
            dataset_summary=summary,
            model_comparisons=rows,
            best_model_eval=best_eval,
            concordance=concordance,
        )

    # -------------------------------------------------------------- #
    #  5. Formateo para consola / tesis
    # -------------------------------------------------------------- #

    @staticmethod
    def format_dataset_summary(ds: DatasetSummary) -> str:
        """Formatea el resumen del dataset como texto tabular."""
        lines: list[str] = []
        lines.append(f"\n{'='*65}")
        lines.append("  RESUMEN DEL DATASET")
        lines.append(f"{'='*65}")
        lines.append(f"  Total de muestras     : {ds.total_samples}")
        lines.append(f"  Transformadores       : {ds.n_transformers}")
        if ds.date_range:
            lines.append(
                f"  Rango de fechas       : "
                f"{ds.date_range[0]} a {ds.date_range[1]}"
            )
        else:
            lines.append("  Rango de fechas       : (sin datos)")

        # Distribucion de fallas
        lines.append(f"\n  {'Tipo de Falla':<25} {'Cantidad':>10} {'%':>8}")
        lines.append(f"  {'-'*45}")
        total = ds.total_samples or 1
        for fault_name, count in ds.fault_distribution.items():
            pct = (count / total) * 100
            lines.append(f"  {fault_name:<25} {count:>10} {pct:>7.1f}%")

        # Estadisticas por gas
        lines.append(f"\n  {'Gas':<8} {'Min':>10} {'Max':>10} {'Media':>10} "
                      f"{'Std':>10} {'Mediana':>10}")
        lines.append(f"  {'-'*60}")
        for gs in ds.gas_stats:
            lines.append(
                f"  {gs.gas_name:<8} {gs.min:>10.1f} {gs.max:>10.1f} "
                f"{gs.mean:>10.1f} {gs.std:>10.1f} {gs.median:>10.1f}"
            )

        lines.append(f"{'='*65}")
        return "\n".join(lines)

    @staticmethod
    def format_model_comparison(rows: list[ModelComparisonRow]) -> str:
        """Formatea la tabla comparativa de modelos."""
        lines: list[str] = []
        lines.append(f"\n{'='*72}")
        lines.append("  COMPARACION DE MODELOS DE IA")
        lines.append(f"{'='*72}")
        header = (
            f"  {'Modelo':<20} {'Acc':>8} {'Prec(M)':>8} "
            f"{'Rec(M)':>8} {'F1(M)':>8} {'F1(W)':>8}"
        )
        lines.append(header)
        lines.append(f"  {'-'*64}")

        for r in rows:
            lines.append(
                f"  {r.model_name:<20} {r.accuracy:>8.2%} "
                f"{r.macro_precision:>8.2%} {r.macro_recall:>8.2%} "
                f"{r.macro_f1:>8.2%} {r.weighted_f1:>8.2%}"
            )

        lines.append(f"{'='*72}")
        return "\n".join(lines)

    @staticmethod
    def format_best_model_detail(ev: EvaluationResult) -> str:
        """Formatea metricas detalladas del mejor modelo."""
        return ModelEvaluator.format_report(ev)

    @staticmethod
    def format_concordance(cs: ComparisonSummary) -> str:
        """Formatea resultados de concordancia."""
        return UnifiedDiagnosisService.format_comparison_table(cs)

    # -------------------------------------------------------------- #
    #  6. Exportacion a CSV
    # -------------------------------------------------------------- #

    @staticmethod
    def export_dataset_summary_csv(
        ds: DatasetSummary, path: str | Path
    ) -> Path:
        """Exporta resumen del dataset a CSV.

        Genera dos archivos:
            - <path>_fallas.csv  (distribucion de fallas)
            - <path>_gases.csv   (estadisticas por gas)

        Args:
            ds: Resumen del dataset.
            path: Ruta base (sin extension).

        Returns:
            Ruta del directorio de salida.
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        # Distribucion de fallas
        faults_path = path.parent / f"{path.stem}_fallas.csv"
        with open(faults_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Tipo_Falla", "Cantidad", "Porcentaje"])
            total = ds.total_samples or 1
            for fault_name, count in ds.fault_distribution.items():
                pct = round((count / total) * 100, 1)
                writer.writerow([fault_name, count, pct])

        # Estadisticas de gases
        gases_path = path.parent / f"{path.stem}_gases.csv"
        with open(gases_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Gas", "Min", "Max", "Media", "Std", "Mediana"])
            for gs in ds.gas_stats:
                writer.writerow([
                    gs.gas_name, gs.min, gs.max, gs.mean, gs.std, gs.median
                ])

        return path.parent

    @staticmethod
    def export_model_comparison_csv(
        rows: list[ModelComparisonRow], path: str | Path
    ) -> Path:
        """Exporta tabla comparativa de modelos a CSV.

        Args:
            rows: Filas de la comparacion.
            path: Ruta del archivo CSV.

        Returns:
            Ruta del archivo creado.
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Modelo", "Accuracy", "Precision_Macro",
                "Recall_Macro", "F1_Macro", "F1_Weighted",
            ])
            for r in rows:
                writer.writerow([
                    r.model_name, r.accuracy, r.macro_precision,
                    r.macro_recall, r.macro_f1, r.weighted_f1,
                ])

        return path

    @staticmethod
    def export_class_metrics_csv(
        ev: EvaluationResult, path: str | Path
    ) -> Path:
        """Exporta metricas por clase del modelo a CSV.

        Args:
            ev: Resultado de evaluacion.
            path: Ruta del archivo CSV.

        Returns:
            Ruta del archivo creado.
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Clase", "Precision", "Recall", "F1_Score", "Soporte",
            ])
            for cm in ev.class_metrics:
                writer.writerow([
                    cm.fault_type.name, cm.precision,
                    cm.recall, cm.f1_score, cm.support,
                ])

        return path

    @staticmethod
    def export_concordance_csv(
        cs: ComparisonSummary, path: str | Path
    ) -> Path:
        """Exporta analisis de concordancia a CSV.

        Args:
            cs: Resumen de comparacion.
            path: Ruta del archivo CSV.

        Returns:
            Ruta del archivo creado.
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Muestra", "Fecha", "Normativo", "IA", "Coinciden",
            ])
            for d in cs.details:
                norm = d.normative.consensus_fault.name
                ai = d.ai_fault.name if d.ai_fault else "---"
                ok = "SI" if d.agree else ("NO" if d.agree is not None else "---")
                writer.writerow([
                    d.sample.sample_code,
                    str(d.sample.extraction_date),
                    norm, ai, ok,
                ])

            # Fila resumen
            writer.writerow([])
            writer.writerow([
                "TOTAL", cs.total, "Coinciden", cs.agreements,
                f"{cs.agreement_pct:.1f}%",
            ])

        return path
