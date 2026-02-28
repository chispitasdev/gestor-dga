"""Adaptador CLI para diagnostico normativo de muestras DGA.

Presenta un submenu interactivo que permite al usuario ejecutar los
6 metodos normativos sobre una muestra seleccionada, ver resultados
individuales y el diagnostico por consenso.
"""

from __future__ import annotations

from src.dga.application.services.normative_diagnosis_service import (
    NormativeDiagnosisService,
    NormativeDiagnosisResult,
)
from src.dga.application.services.sample_service import SampleService
from src.dga.domain.exceptions import DGADomainError
from src.dga.domain.models.sample import Sample


class DiagnosisCLI:
    """Interfaz de linea de comandos para diagnostico normativo.

    Args:
        sample_service: Servicio de muestras (para obtener lecturas).
        diagnosis_service: Servicio de diagnostico normativo.
    """

    MENU = (
        "\n--- Diagnostico Normativo ---\n"
        "1. Diagnosticar muestra por ID\n"
        "2. Diagnosticar todas las muestras de un transformador\n"
        "3. Ver metodos disponibles\n"
        "0. Volver al menu principal\n"
    )

    def __init__(
        self,
        sample_service: SampleService,
        diagnosis_service: NormativeDiagnosisService,
    ) -> None:
        self._sample_svc = sample_service
        self._diagnosis_svc = diagnosis_service

    def run(self) -> None:
        """Ejecuta el bucle del submenu de diagnostico."""
        actions = {
            "1": self._diagnose_by_id,
            "2": self._diagnose_by_transformer,
            "3": self._show_methods,
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

    def _diagnose_by_id(self) -> None:
        """Diagnostica una muestra individual."""
        raw_id = input("ID de la muestra: ").strip()
        if not raw_id.isdigit():
            print("El ID debe ser un numero entero positivo.")
            return

        sample = self._sample_svc.get_sample(int(raw_id))
        result = self._diagnosis_svc.diagnose_all(sample.gas_reading)
        self._display_diagnosis(sample, result)

    def _diagnose_by_transformer(self) -> None:
        """Diagnostica todas las muestras de un transformador."""
        raw_id = input("ID del transformador: ").strip()
        if not raw_id.isdigit():
            print("El ID debe ser un numero entero positivo.")
            return

        samples = self._sample_svc.list_samples_by_transformer(int(raw_id))
        if not samples:
            print("\nNo se encontraron muestras para este transformador.")
            return

        for sample in samples:
            result = self._diagnosis_svc.diagnose_all(sample.gas_reading)
            self._display_diagnosis(sample, result)
            print()

    def _show_methods(self) -> None:
        """Muestra los metodos normativos disponibles."""
        methods = NormativeDiagnosisService.available_methods()
        print("\nMetodos normativos implementados:")
        for i, name in enumerate(methods, start=1):
            print(f"  {i}. {name}")

    # ------------------------------------------------------------------
    # Presentacion
    # ------------------------------------------------------------------

    @staticmethod
    def _display_diagnosis(
        sample: Sample, result: NormativeDiagnosisResult
    ) -> None:
        """Muestra en pantalla el resultado completo del diagnostico."""
        print(f"\n{'='*60}")
        print("  DIAGNOSTICO NORMATIVO")
        print(f"  Muestra: {sample.sample_code} (ID: {sample.id})")
        print(f"  Fecha extraccion: {sample.extraction_date}")
        print(f"{'='*60}")

        # Resultados individuales
        print(f"\n  {'Metodo':<25} {'Falla':<8} {'Descripcion'}")
        print(f"  {'-'*25} {'-'*8} {'-'*30}")
        for r in result.results:
            print(f"  {r.method_name:<25} {r.fault_type.name:<8} {r.description}")

        # Consenso
        print(f"\n  {'─'*55}")
        print(f"  CONSENSO: {result.consensus_fault}")
        print(f"  Acuerdo : {result.agreement_pct}%")
        print(f"  Votos   : {result.vote_counts}")
        print(f"{'='*60}")
