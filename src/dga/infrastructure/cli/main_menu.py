"""Menu principal de la aplicacion CLI.

Coordina la navegacion entre los submenus del sistema DGA:
transformadores, muestras, diagnostico normativo, importacion,
tendencias, inteligencia artificial, diagnostico unificado, graficos
y validacion para la tesis.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.dga.infrastructure.cli.transformer_cli import TransformerCLI
    from src.dga.infrastructure.cli.sample_cli import SampleCLI
    from src.dga.infrastructure.cli.diagnosis_cli import DiagnosisCLI
    from src.dga.infrastructure.cli.import_cli import ImportCLI
    from src.dga.infrastructure.cli.trend_cli import TrendCLI
    from src.dga.infrastructure.cli.ai_cli import AICli
    from src.dga.infrastructure.cli.unified_diagnosis_cli import (
        UnifiedDiagnosisCLI,
    )
    from src.dga.infrastructure.cli.charts_cli import ChartsCLI
    from src.dga.infrastructure.cli.validation_cli import ValidationCLI


class MainMenu:
    """Menu principal que agrupa los submenus del sistema DGA.

    Args:
        transformer_cli: Adaptador CLI de transformadores.
        sample_cli: Adaptador CLI de muestras.
        diagnosis_cli: Adaptador CLI de diagnostico normativo.
        import_cli: Adaptador CLI de importacion de datos.
        trend_cli: Adaptador CLI de tendencias.
        ai_cli: Adaptador CLI del motor de IA.
        unified_cli: Adaptador CLI de diagnostico unificado.
        charts_cli: Adaptador CLI de graficos.
        validation_cli: Adaptador CLI de validacion para la tesis.
    """

    BANNER = (
        "\n============================================\n"
        "  Sistema de Diagnostico DGA\n"
        "  Gases Disueltos en Aceite\n"
        "  de Transformadores de Potencia\n"
        "============================================"
    )

    MENU = (
        "\n--- Menu Principal ---\n"
        "1. Gestion de Transformadores\n"
        "2. Gestion de Muestras DGA\n"
        "3. Diagnostico Normativo\n"
        "4. Importar Datos (CSV/Excel)\n"
        "5. Analisis de Tendencias\n"
        "6. Motor de Inteligencia Artificial\n"
        "7. Diagnostico Unificado (Normativo + IA)\n"
        "8. Generacion de Graficos\n"
        "9. Validacion y Reportes (Tesis Cap. 5)\n"
        "0. Salir\n"
    )

    def __init__(
        self,
        transformer_cli: TransformerCLI,
        sample_cli: SampleCLI,
        diagnosis_cli: DiagnosisCLI,
        import_cli: ImportCLI,
        trend_cli: TrendCLI,
        ai_cli: AICli,
        unified_cli: UnifiedDiagnosisCLI,
        charts_cli: ChartsCLI,
        validation_cli: ValidationCLI,
    ) -> None:
        self._transformer_cli = transformer_cli
        self._sample_cli = sample_cli
        self._diagnosis_cli = diagnosis_cli
        self._import_cli = import_cli
        self._trend_cli = trend_cli
        self._ai_cli = ai_cli
        self._unified_cli = unified_cli
        self._charts_cli = charts_cli
        self._validation_cli = validation_cli

    def run(self) -> None:
        """Ejecuta el bucle principal del menu."""
        print(self.BANNER)
        while True:
            print(self.MENU)
            choice = input("Seleccione una opcion: ").strip()
            if choice == "0":
                print("\nSesion finalizada.")
                break
            elif choice == "1":
                self._transformer_cli.run()
            elif choice == "2":
                self._sample_cli.run()
            elif choice == "3":
                self._diagnosis_cli.run()
            elif choice == "4":
                self._import_cli.run()
            elif choice == "5":
                self._trend_cli.run()
            elif choice == "6":
                self._ai_cli.run()
            elif choice == "7":
                self._unified_cli.run()
            elif choice == "8":
                self._charts_cli.run()
            elif choice == "9":
                self._validation_cli.run()
            else:
                print("Opcion no valida. Intente de nuevo.")
