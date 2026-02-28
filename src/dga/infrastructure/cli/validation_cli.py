"""Interfaz CLI para validacion y generacion de reportes (Cap. 5 tesis).

Opciones del submenu:
    1. Resumen estadistico del dataset.
    2. Tabla comparativa de modelos de IA.
    3. Metricas detalladas del mejor modelo.
    4. Analisis de concordancia normativo vs. IA.
    5. Reporte completo (todas las secciones).
    6. Exportar tablas a CSV.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.dga.application.services.sample_service import SampleService
    from src.dga.application.services.transformer_service import (
        TransformerService,
    )
    from src.dga.application.services.validation_service import (
        ValidationService,
    )

# Directorio de salida por defecto
_OUTPUT_DIR = Path("output")


class ValidationCLI:
    """Adaptador CLI para validacion y reportes de la tesis."""

    MENU = (
        "\n--- Validacion y Reportes (Tesis Cap. 5) ---\n"
        "1. Resumen estadistico del dataset\n"
        "2. Tabla comparativa de modelos\n"
        "3. Metricas detalladas del mejor modelo\n"
        "4. Concordancia normativo vs. IA\n"
        "5. Reporte completo\n"
        "6. Exportar tablas a CSV\n"
        "0. Volver\n"
    )

    def __init__(
        self,
        validation_service: "ValidationService",
        sample_service: "SampleService",
        transformer_service: "TransformerService",
    ) -> None:
        self._validation = validation_service
        self._samples = sample_service
        self._transformers = transformer_service
        _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    def run(self) -> None:
        """Ejecuta el bucle del submenu de validacion."""
        while True:
            print(self.MENU)
            choice = input("Seleccione una opcion: ").strip()
            if choice == "0":
                break
            elif choice == "1":
                self._dataset_summary()
            elif choice == "2":
                self._model_comparison()
            elif choice == "3":
                self._best_model_detail()
            elif choice == "4":
                self._concordance()
            elif choice == "5":
                self._full_report()
            elif choice == "6":
                self._export_csv()
            else:
                print("Opcion no valida.")

    # ------------------------------------------------------------------ #
    #  Opciones individuales
    # ------------------------------------------------------------------ #

    def _get_all_samples(self):
        """Obtiene todas las muestras del repositorio."""
        samples = self._samples.list_samples()
        if not samples:
            print("\nNo hay muestras cargadas en la base de datos.")
        return samples

    def _dataset_summary(self) -> None:
        """Muestra resumen estadistico del dataset."""
        samples = self._get_all_samples()
        if not samples:
            return

        print("\nCalculando estadisticas del dataset...")
        summary = self._validation.build_dataset_summary(samples)
        from src.dga.application.services.validation_service import (
            ValidationService,
        )
        print(ValidationService.format_dataset_summary(summary))

    def _model_comparison(self) -> None:
        """Muestra tabla comparativa de los 4 modelos."""
        samples = self._get_all_samples()
        if not samples:
            return

        if len(samples) < 10:
            print(f"\nMuestras insuficientes ({len(samples)}). Minimo 10.")
            return

        print("\nEvaluando 4 modelos (esto puede tardar)...")
        rows, _ = self._validation.evaluate_all_models(samples)
        from src.dga.application.services.validation_service import (
            ValidationService,
        )
        print(ValidationService.format_model_comparison(rows))

    def _best_model_detail(self) -> None:
        """Muestra metricas detalladas del mejor modelo."""
        samples = self._get_all_samples()
        if not samples:
            return

        if len(samples) < 10:
            print(f"\nMuestras insuficientes ({len(samples)}). Minimo 10.")
            return

        print("\nEvaluando modelos...")
        _, eval_results = self._validation.evaluate_all_models(samples)
        if not eval_results:
            print("\nNo se pudieron evaluar los modelos.")
            return

        from src.dga.application.services.validation_service import (
            ValidationService,
        )
        best = eval_results[0]
        print(ValidationService.format_best_model_detail(best))

    def _concordance(self) -> None:
        """Muestra analisis de concordancia normativo vs. IA."""
        samples = self._get_all_samples()
        if not samples:
            return

        if not self._validation._ai.has_model():
            print("\nNo hay modelo de IA entrenado.")
            print("Ejecute primero el entrenamiento desde el menu de IA.")
            return

        print("\nAnalizando concordancia normativo vs. IA...")
        concordance = self._validation.concordance_analysis(samples)
        from src.dga.application.services.validation_service import (
            ValidationService,
        )
        print(ValidationService.format_concordance(concordance))

    def _full_report(self) -> None:
        """Genera y muestra el reporte completo de validacion."""
        samples = self._get_all_samples()
        if not samples:
            return

        if len(samples) < 10:
            print(f"\nMuestras insuficientes ({len(samples)}). Minimo 10.")
            return

        print("\nGenerando reporte completo de validacion...")
        print("(Esto incluye entrenamiento y evaluacion de 4 modelos)")

        report = self._validation.full_validation(samples)
        from src.dga.application.services.validation_service import (
            ValidationService,
        )

        # 1. Dataset
        print(ValidationService.format_dataset_summary(report.dataset_summary))

        # 2. Comparacion de modelos
        print(ValidationService.format_model_comparison(
            report.model_comparisons
        ))

        # 3. Mejor modelo detallado
        if report.best_model_eval:
            print(ValidationService.format_best_model_detail(
                report.best_model_eval
            ))

        # 4. Concordancia
        if report.concordance:
            print(ValidationService.format_concordance(report.concordance))
        else:
            print("\n  (Concordancia no disponible sin modelo IA)")

    def _export_csv(self) -> None:
        """Exporta todas las tablas a archivos CSV."""
        samples = self._get_all_samples()
        if not samples:
            return

        if len(samples) < 10:
            print(f"\nMuestras insuficientes ({len(samples)}). Minimo 10.")
            return

        print("\nGenerando datos para exportacion...")
        report = self._validation.full_validation(samples)

        from src.dga.application.services.validation_service import (
            ValidationService,
        )

        csv_dir = _OUTPUT_DIR / "csv"
        csv_dir.mkdir(parents=True, exist_ok=True)

        # 1. Dataset summary
        ValidationService.export_dataset_summary_csv(
            report.dataset_summary, csv_dir / "dataset"
        )
        print(f"  -> {csv_dir / 'dataset_fallas.csv'}")
        print(f"  -> {csv_dir / 'dataset_gases.csv'}")

        # 2. Comparacion de modelos
        path_models = csv_dir / "comparacion_modelos.csv"
        ValidationService.export_model_comparison_csv(
            report.model_comparisons, path_models
        )
        print(f"  -> {path_models}")

        # 3. Metricas por clase del mejor modelo
        if report.best_model_eval:
            path_class = csv_dir / "metricas_clase.csv"
            ValidationService.export_class_metrics_csv(
                report.best_model_eval, path_class
            )
            print(f"  -> {path_class}")

        # 4. Concordancia
        if report.concordance:
            path_conc = csv_dir / "concordancia.csv"
            ValidationService.export_concordance_csv(
                report.concordance, path_conc
            )
            print(f"  -> {path_conc}")

        print(f"\n  Archivos exportados en: {csv_dir.resolve()}")
