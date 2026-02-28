"""Dependencias compartidas para inyeccion en los routers FastAPI.

Centraliza la creacion de servicios y repositorios para que todos los
routers accedan a las mismas instancias. Usa el patron Singleton a nivel
de modulo (las instancias se crean al importar).
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
from src.dga.application.services.unified_diagnosis_service import (
    UnifiedDiagnosisService,
)
from src.dga.application.services.validation_service import ValidationService
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

# ── Ruta de la base de datos ───────────────────────────────────────
_DB_PATH = Path(__file__).resolve().parents[4] / "dga.db"

# ── Infraestructura ────────────────────────────────────────────────
connection = get_connection(_DB_PATH)
initialize_database(connection)

transformer_repo = SQLiteTransformerRepository(connection)
sample_repo = SQLiteSampleRepository(connection)

# ── Servicios de aplicacion ────────────────────────────────────────
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
