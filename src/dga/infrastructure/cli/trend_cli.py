"""Adaptador CLI para analisis de tendencias de gases disueltos.

Permite al usuario visualizar tasas de generacion de gas entre pares
de muestras y el historial completo de gases por transformador.
"""

from __future__ import annotations

from src.dga.application.services.sample_service import SampleService
from src.dga.application.services.transformer_service import TransformerService
from src.dga.application.services.trend_service import (
    TrendService,
    TrendAnalysis,
    GasHistory,
)
from src.dga.domain.exceptions import DGADomainError
from src.dga.domain.models.gas_reading import GasReading


_DATE_FORMAT = "%d/%m/%Y"


class TrendCLI:
    """Interfaz de linea de comandos para tendencias de gas.

    Args:
        sample_service: Servicio de muestras.
        transformer_service: Servicio de transformadores.
        trend_service: Servicio de tendencias.
    """

    MENU = (
        "\n--- Analisis de Tendencias ---\n"
        "1. Tasas de generacion entre dos muestras\n"
        "2. Tasas de generacion de todo un transformador\n"
        "3. Historial de gases de un transformador\n"
        "0. Volver al menu principal\n"
    )

    def __init__(
        self,
        sample_service: SampleService,
        transformer_service: TransformerService,
        trend_service: TrendService,
    ) -> None:
        self._sample_svc = sample_service
        self._transformer_svc = transformer_service
        self._trend_svc = trend_service

    def run(self) -> None:
        """Ejecuta el bucle del submenu de tendencias."""
        actions = {
            "1": self._pair_analysis,
            "2": self._full_transformer_rates,
            "3": self._gas_history,
        }
        while True:
            print(self.MENU)
            choice = input("Seleccione una opcion: ").strip()
            if choice == "0":
                break
            action = actions.get(choice)
            if action is None:
                print("Opcion no valida. Intente de nuevo.")
                continue
            try:
                action()
            except DGADomainError as exc:
                print(f"\n[Error] {exc}")
            except ValueError as exc:
                print(f"\n[Error de validacion] {exc}")

    # ------------------------------------------------------------------
    # Acciones
    # ------------------------------------------------------------------

    def _pair_analysis(self) -> None:
        """Calcula tasas entre dos muestras especificas."""
        print("\nIngrese los IDs de las dos muestras a comparar:")
        raw_prev = input("  ID muestra anterior: ").strip()
        raw_curr = input("  ID muestra actual  : ").strip()

        if not raw_prev.isdigit() or not raw_curr.isdigit():
            print("Los IDs deben ser numeros enteros positivos.")
            return

        previous = self._sample_svc.get_sample(int(raw_prev))
        current = self._sample_svc.get_sample(int(raw_curr))

        analysis = self._trend_svc.analyze_pair(previous, current)
        self._display_analysis(analysis)

    def _full_transformer_rates(self) -> None:
        """Muestra todas las tasas consecutivas de un transformador."""
        raw_id = input("ID del transformador: ").strip()
        if not raw_id.isdigit():
            print("El ID debe ser un numero entero positivo.")
            return

        samples = self._sample_svc.list_samples_by_transformer(int(raw_id))
        if len(samples) < 2:
            print("\nSe necesitan al menos 2 muestras para calcular tendencias.")
            return

        analyses = self._trend_svc.compute_all_rates(samples)
        for analysis in analyses:
            self._display_analysis(analysis)
            print()

    def _gas_history(self) -> None:
        """Muestra el historial temporal de cada gas."""
        raw_id = input("ID del transformador: ").strip()
        if not raw_id.isdigit():
            print("El ID debe ser un numero entero positivo.")
            return

        samples = self._sample_svc.list_samples_by_transformer(int(raw_id))
        if not samples:
            print("\nNo se encontraron muestras para este transformador.")
            return

        histories = self._trend_svc.build_gas_history(samples)
        self._display_history(histories)

    # ------------------------------------------------------------------
    # Presentacion
    # ------------------------------------------------------------------

    @staticmethod
    def _display_analysis(analysis: TrendAnalysis) -> None:
        """Muestra el resultado de una comparacion entre dos muestras."""
        sf = analysis.sample_from
        st = analysis.sample_to
        print(f"\n{'='*65}")
        print("  TASAS DE GENERACION DE GAS")
        print(f"  Muestra anterior: {sf.sample_code} ({sf.extraction_date.strftime(_DATE_FORMAT)})")
        print(f"  Muestra actual  : {st.sample_code} ({st.extraction_date.strftime(_DATE_FORMAT)})")
        print(f"  Dias transcurridos: {analysis.days_between}")
        print(f"{'='*65}")

        print(f"\n  {'Gas':<28} {'Prev':>8} {'Actual':>8} {'Δ ppm':>8} {'ppm/dia':>10} {'Estado'}")
        print(f"  {'-'*28} {'-'*8} {'-'*8} {'-'*8} {'-'*10} {'-'*10}")

        for gr in analysis.gas_rates:
            arrow = "↑" if gr.is_increasing else ("↓" if gr.delta_ppm < 0 else "=")
            crit = " ¡CRITICO!" if gr.gas_name in analysis.critical_gases else ""
            print(
                f"  {gr.gas_label:<28} {gr.previous_ppm:>8.1f} {gr.current_ppm:>8.1f} "
                f"{gr.delta_ppm:>+8.1f} {gr.rate_ppm_day:>+10.4f} {arrow}{crit}"
            )

        if analysis.critical_gases:
            labels = GasReading.descriptive_labels()
            print("\n  ⚠ GASES CRITICOS: ", end="")
            print(", ".join(labels[g] for g in analysis.critical_gases))

    @staticmethod
    def _display_history(histories: list[GasHistory]) -> None:
        """Muestra el historial de cada gas en formato tabla."""
        if not histories:
            return

        num_samples = len(histories[0].dates)
        dates = histories[0].dates

        print(f"\n{'='*80}")
        print(f"  HISTORIAL DE GASES DISUELTOS ({num_samples} muestras)")
        print(f"{'='*80}")

        # Cabecera con fechas
        header = f"  {'Gas':<28}"
        for d in dates:
            header += f" {d.strftime(_DATE_FORMAT):>12}"
        print(header)
        print("  " + "-" * (28 + 13 * num_samples))

        for hist in histories:
            row = f"  {hist.gas_label:<28}"
            for val in hist.values:
                row += f" {val:>12.1f}"
            print(row)

        print(f"{'='*80}")
