"""Interfaz CLI para el diagnostico unificado.

Permite al usuario:
    1. Diagnosticar una muestra (normativo + IA combinados).
    2. Diagnosticar todas las muestras de un transformador.
    3. Comparar normativo vs. IA con tabla resumen.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.dga.application.services.unified_diagnosis_service import (
        UnifiedDiagnosisService,
    )
    from src.dga.application.services.sample_service import SampleService
    from src.dga.application.services.transformer_service import (
        TransformerService,
    )


class UnifiedDiagnosisCLI:
    """Adaptador CLI para diagnostico unificado.

    Args:
        unified_service: Servicio de diagnostico unificado.
        sample_service: Servicio de muestras.
        transformer_service: Servicio de transformadores.
    """

    MENU = (
        "\n--- Diagnostico Unificado (Normativo + IA) ---\n"
        "1. Diagnosticar muestra por ID\n"
        "2. Diagnosticar muestras de transformador\n"
        "3. Comparar Normativo vs. IA\n"
        "0. Volver\n"
    )

    def __init__(
        self,
        unified_service: "UnifiedDiagnosisService",
        sample_service: "SampleService",
        transformer_service: "TransformerService",
    ) -> None:
        self._unified = unified_service
        self._samples = sample_service
        self._transformers = transformer_service

    def run(self) -> None:
        """Ejecuta el bucle del submenu."""
        while True:
            print(self.MENU)
            choice = input("Seleccione una opcion: ").strip()
            if choice == "0":
                break
            elif choice == "1":
                self._diagnose_by_id()
            elif choice == "2":
                self._diagnose_by_transformer()
            elif choice == "3":
                self._compare()
            else:
                print("Opcion no valida.")

    # ------------------------------------------------------------------ #
    #  Diagnosticar por ID
    # ------------------------------------------------------------------ #

    def _diagnose_by_id(self) -> None:
        """Diagnostica una muestra individual con ambos enfoques."""
        try:
            sid = int(input("ID de la muestra: ").strip())
        except ValueError:
            print("ID invalido.")
            return

        try:
            sample = self._samples.get_sample(sid)
        except Exception:
            print(f"Muestra con ID {sid} no encontrada.")
            return

        from src.dga.application.services.unified_diagnosis_service import (
            UnifiedDiagnosisService,
        )

        result = self._unified.diagnose(sample)
        print(UnifiedDiagnosisService.format_unified_report(result))

    # ------------------------------------------------------------------ #
    #  Diagnosticar por transformador
    # ------------------------------------------------------------------ #

    def _diagnose_by_transformer(self) -> None:
        """Diagnostica todas las muestras de un transformador."""
        transformers = self._transformers.list_transformers()
        if not transformers:
            print("\nNo hay transformadores registrados.")
            return

        print("\nTransformadores disponibles:")
        for t in transformers:
            print(f"  [{t.id}] {t.name}")

        try:
            tid = int(input("ID del transformador: ").strip())
        except ValueError:
            print("ID invalido.")
            return

        try:
            samples = self._samples.list_samples_by_transformer(tid)
        except Exception:
            print(f"Transformador ID {tid} no encontrado.")
            return
        if not samples:
            print(f"No hay muestras para el transformador ID {tid}.")
            return

        from src.dga.application.services.unified_diagnosis_service import (
            UnifiedDiagnosisService,
        )

        for s in samples:
            result = self._unified.diagnose(s)
            print(UnifiedDiagnosisService.format_unified_report(result))

    # ------------------------------------------------------------------ #
    #  Comparar normativo vs. IA
    # ------------------------------------------------------------------ #

    def _compare(self) -> None:
        """Compara normativo vs. IA para todas las muestras."""
        all_samples = self._samples.list_samples()
        if not all_samples:
            print("\nNo hay muestras registradas.")
            return

        from src.dga.application.services.unified_diagnosis_service import (
            UnifiedDiagnosisService,
        )

        summary = self._unified.compare(all_samples)
        print(UnifiedDiagnosisService.format_comparison_table(summary))
