"""Punto de entrada del sistema de diagnostico DGA.

Composition Root: instancia todos los componentes concretos de
infraestructura, los inyecta en los servicios de aplicacion y estos
a su vez en los adaptadores CLI. Centraliza la configuracion de
dependencias sin necesidad de un framework de inyeccion.

Uso:
    python main.py
"""

from __future__ import annotations

from pathlib import Path

from src.dga.application.services.sample_service import SampleService
from src.dga.application.services.transformer_service import TransformerService
from src.dga.application.services.normative_diagnosis_service import (
    NormativeDiagnosisService,
)
from src.dga.application.services.import_service import ImportService
from src.dga.application.services.trend_service import TrendService
from src.dga.application.services.ai_engine.ai_service import AIService
from src.dga.infrastructure.cli.main_menu import MainMenu
from src.dga.infrastructure.cli.sample_cli import SampleCLI
from src.dga.infrastructure.cli.transformer_cli import TransformerCLI
from src.dga.infrastructure.cli.diagnosis_cli import DiagnosisCLI
from src.dga.infrastructure.cli.import_cli import ImportCLI
from src.dga.infrastructure.cli.trend_cli import TrendCLI
from src.dga.infrastructure.cli.ai_cli import AICli
from src.dga.application.services.unified_diagnosis_service import (
    UnifiedDiagnosisService,
)
from src.dga.infrastructure.cli.unified_diagnosis_cli import (
    UnifiedDiagnosisCLI,
)
from src.dga.infrastructure.cli.charts_cli import ChartsCLI
from src.dga.application.services.validation_service import (
    ValidationService,
)
from src.dga.infrastructure.cli.validation_cli import ValidationCLI
from src.dga.infrastructure.persistence.sqlite_connection import (
    get_connection,
    initialize_database,
)
from src.dga.infrastructure.persistence.sqlite_sample_repository import (
    SQLiteSampleRepository,
)
from src.dga.infrastructure.persistence.sqlite_transformer_repository import (
    SQLiteTransformerRepository,
)

# Ruta de la base de datos junto al ejecutable.
_DB_PATH = Path(__file__).resolve().parent / "dga.db"


def main() -> None:
    """Configura las dependencias y arranca la aplicacion CLI."""
    # -- Infraestructura: conexion y esquema --
    connection = get_connection(_DB_PATH)
    initialize_database(connection)

    # -- Infraestructura: repositorios concretos --
    transformer_repo = SQLiteTransformerRepository(connection)
    sample_repo = SQLiteSampleRepository(connection)

    # -- Aplicacion: servicios --
    transformer_service = TransformerService(transformer_repo)
    sample_service = SampleService(sample_repo, transformer_repo)
    diagnosis_service = NormativeDiagnosisService()
    import_service = ImportService(sample_service)
    trend_service = TrendService()
    ai_service = AIService(sample_repo, diagnosis_service)
    unified_service = UnifiedDiagnosisService(diagnosis_service, ai_service)
    validation_service = ValidationService(
        diagnosis_service, ai_service, unified_service,
    )

    # -- Infraestructura: adaptadores CLI --
    transformer_cli = TransformerCLI(transformer_service)
    sample_cli = SampleCLI(sample_service, transformer_service)
    diagnosis_cli = DiagnosisCLI(sample_service, diagnosis_service)
    import_cli = ImportCLI(import_service, transformer_service)
    trend_cli = TrendCLI(sample_service, transformer_service, trend_service)
    ai_cli = AICli(ai_service, sample_service, transformer_service)
    unified_cli = UnifiedDiagnosisCLI(
        unified_service, sample_service, transformer_service,
    )
    charts_cli = ChartsCLI(
        sample_service, transformer_service, trend_service, ai_service,
    )
    validation_cli = ValidationCLI(
        validation_service, sample_service, transformer_service,
    )

    # -- Arranque --
    menu = MainMenu(
        transformer_cli, sample_cli,
        diagnosis_cli, import_cli, trend_cli, ai_cli,
        unified_cli, charts_cli, validation_cli,
    )
    try:
        menu.run()
    finally:
        connection.close()


if __name__ == "__main__":
    main()
