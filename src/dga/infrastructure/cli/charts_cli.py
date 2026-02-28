"""Interfaz CLI para la generacion de graficos DGA.

Permite al usuario generar:
    1. Triangulo de Duval con puntos de muestra.
    2. Tendencias de gases en el tiempo.
    3. Matriz de confusion del mejor modelo.
    4. Comparacion de accuracy entre modelos.
    5. Metricas por clase (precision/recall/F1).

Todos los graficos se guardan como archivos PNG en la carpeta output/.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.dga.application.services.sample_service import SampleService
    from src.dga.application.services.transformer_service import (
        TransformerService,
    )
    from src.dga.application.services.trend_service import TrendService
    from src.dga.application.services.ai_engine.ai_service import AIService


# Directorio de salida por defecto
_OUTPUT_DIR = Path("output")


class ChartsCLI:
    """Adaptador CLI para generacion de graficos."""

    MENU = (
        "\n--- Generacion de Graficos ---\n"
        "1. Triangulo de Duval\n"
        "2. Tendencias de gases\n"
        "3. Tendencias individuales por gas\n"
        "4. Comparacion de modelos IA\n"
        "5. Matriz de confusion\n"
        "6. Metricas por clase\n"
        "0. Volver\n"
    )

    def __init__(
        self,
        sample_service: "SampleService",
        transformer_service: "TransformerService",
        trend_service: "TrendService",
        ai_service: "AIService",
    ) -> None:
        self._samples = sample_service
        self._transformers = transformer_service
        self._trends = trend_service
        self._ai = ai_service
        _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    def run(self) -> None:
        """Ejecuta el bucle del submenu."""
        while True:
            print(self.MENU)
            choice = input("Seleccione una opcion: ").strip()
            if choice == "0":
                break
            elif choice == "1":
                self._duval_triangle()
            elif choice == "2":
                self._trend_chart()
            elif choice == "3":
                self._trend_individual()
            elif choice == "4":
                self._model_comparison()
            elif choice == "5":
                self._confusion_matrix()
            elif choice == "6":
                self._class_metrics()
            else:
                print("Opcion no valida.")

    # ------------------------------------------------------------------ #
    #  Triangulo de Duval
    # ------------------------------------------------------------------ #

    def _duval_triangle(self) -> None:
        """Genera el Triangulo de Duval con muestras de un transformador."""
        tid = self._select_transformer()
        if tid is None:
            return

        try:
            samples = self._samples.list_samples_by_transformer(tid)
        except Exception:
            print(f"Transformador ID {tid} no encontrado.")
            return
        if not samples:
            print("No hay muestras para este transformador.")
            return

        from src.dga.infrastructure.charts.duval_triangle_chart import (
            plot_duval_triangle,
        )

        readings = [s.gas_reading for s in samples]
        labels_list = [f"{s.sample_code}" for s in samples]

        try:
            transformer = self._transformers.get_transformer(tid)
            t_name = transformer.name
        except Exception:
            t_name = f"ID {tid}"

        path = _OUTPUT_DIR / f"duval_triangle_{tid}.png"
        fig = plot_duval_triangle(
            readings, labels=labels_list,
            title=f"Triangulo de Duval 1 — {t_name}",
            save_path=path,
        )
        plt_close(fig)
        print(f"\n  Grafico guardado en: {path.resolve()}")

    # ------------------------------------------------------------------ #
    #  Tendencias
    # ------------------------------------------------------------------ #

    def _trend_chart(self) -> None:
        """Genera grafico de tendencias de gases."""
        tid = self._select_transformer()
        if tid is None:
            return

        try:
            samples = self._samples.list_samples_by_transformer(tid)
        except Exception:
            print(f"Transformador ID {tid} no encontrado.")
            return
        if len(samples) < 2:
            print("Se necesitan al menos 2 muestras para tendencias.")
            return

        from src.dga.infrastructure.charts.trend_chart import plot_gas_trends

        histories = self._trends.build_gas_history(samples)

        try:
            transformer = self._transformers.get_transformer(tid)
            t_name = transformer.name
        except Exception:
            t_name = f"ID {tid}"

        path = _OUTPUT_DIR / f"tendencias_{tid}.png"
        fig = plot_gas_trends(
            histories,
            title=f"Tendencias de Gases — {t_name}",
            save_path=path,
        )
        plt_close(fig)
        print(f"\n  Grafico guardado en: {path.resolve()}")

    def _trend_individual(self) -> None:
        """Genera subplots individuales de tendencia por gas."""
        tid = self._select_transformer()
        if tid is None:
            return

        try:
            samples = self._samples.list_samples_by_transformer(tid)
        except Exception:
            print(f"Transformador ID {tid} no encontrado.")
            return
        if len(samples) < 2:
            print("Se necesitan al menos 2 muestras.")
            return

        from src.dga.infrastructure.charts.trend_chart import (
            plot_gas_trends_individual,
        )

        histories = self._trends.build_gas_history(samples)

        path = _OUTPUT_DIR / f"tendencias_ind_{tid}.png"
        fig = plot_gas_trends_individual(
            histories,
            title=f"Tendencias Individuales — Transformador {tid}",
            save_path=path,
        )
        plt_close(fig)
        print(f"\n  Grafico guardado en: {path.resolve()}")

    # ------------------------------------------------------------------ #
    #  Modelos IA
    # ------------------------------------------------------------------ #

    def _model_comparison(self) -> None:
        """Genera grafico comparativo de accuracy de los 4 modelos."""
        all_samples = self._samples.list_samples()
        if len(all_samples) < 10:
            print(f"Muestras insuficientes ({len(all_samples)}). Minimo 10.")
            return

        print("\nEntrenando modelos para comparacion...")
        try:
            result = self._ai.train(all_samples, save=True)
        except ValueError as e:
            print(f"Error: {e}")
            return

        from src.dga.infrastructure.charts.model_charts import (
            plot_model_comparison,
        )

        path = _OUTPUT_DIR / "comparacion_modelos.png"
        fig = plot_model_comparison(result, save_path=path)
        plt_close(fig)
        print(f"\n  Grafico guardado en: {path.resolve()}")

        # Mostrar resumen
        for m in result.models:
            marker = " <<" if m.name == result.best_model.name else ""
            print(f"  {m.name:<20} {m.cv_accuracy:.2%} ± {m.cv_std:.4f}{marker}")

    def _confusion_matrix(self) -> None:
        """Genera heatmap de la matriz de confusion."""
        all_samples = self._samples.list_samples()
        if len(all_samples) < 10:
            print(f"Muestras insuficientes ({len(all_samples)}). Minimo 10.")
            return

        print("\nEvaluando modelos...")
        try:
            evaluations = self._ai.evaluate_all(all_samples)
        except ValueError as e:
            print(f"Error: {e}")
            return

        from src.dga.infrastructure.charts.model_charts import (
            plot_confusion_matrix,
        )

        # Generar para el mejor modelo (primer resultado, ya ordenado)
        best = evaluations[0]
        path = _OUTPUT_DIR / f"confusion_{best.model_name.replace(' ', '_').lower()}.png"
        fig = plot_confusion_matrix(best, save_path=path)
        plt_close(fig)
        print(f"\n  Matriz de confusion ({best.model_name})")
        print(f"  Accuracy: {best.overall_accuracy:.2%}")
        print(f"  Guardado en: {path.resolve()}")

    def _class_metrics(self) -> None:
        """Genera grafico de metricas por clase."""
        all_samples = self._samples.list_samples()
        if len(all_samples) < 10:
            print(f"Muestras insuficientes ({len(all_samples)}). Minimo 10.")
            return

        print("\nEvaluando modelos...")
        try:
            evaluations = self._ai.evaluate_all(all_samples)
        except ValueError as e:
            print(f"Error: {e}")
            return

        from src.dga.infrastructure.charts.model_charts import (
            plot_class_metrics,
        )

        best = evaluations[0]
        path = _OUTPUT_DIR / f"metricas_clase_{best.model_name.replace(' ', '_').lower()}.png"
        fig = plot_class_metrics(best, save_path=path)
        plt_close(fig)
        print(f"\n  Metricas por clase ({best.model_name})")
        print(f"  Guardado en: {path.resolve()}")

    # ------------------------------------------------------------------ #
    #  Utilidades
    # ------------------------------------------------------------------ #

    def _select_transformer(self) -> int | None:
        """Muestra transformadores y pide seleccionar uno."""
        transformers = self._transformers.list_transformers()
        if not transformers:
            print("\nNo hay transformadores registrados.")
            return None

        print("\nTransformadores disponibles:")
        for t in transformers:
            print(f"  [{t.id}] {t.name}")

        try:
            return int(input("ID del transformador: ").strip())
        except ValueError:
            print("ID invalido.")
            return None


def plt_close(fig) -> None:
    """Cierra una figura para liberar memoria."""
    import matplotlib.pyplot as plt
    plt.close(fig)
