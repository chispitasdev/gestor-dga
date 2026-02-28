"""Tests de integracion para los repositorios SQLite.

Ejecutan el ciclo CRUD completo contra una base de datos SQLite en memoria
(:memory:) para verificar el comportamiento real de las queries SQL, el
mapeo de entidades, las restricciones de integridad y el borrado en cascada.
"""

from __future__ import annotations

from datetime import date

import pytest

from src.dga.domain.exceptions import (
    DuplicateSampleCodeError,
    DuplicateTransformerError,
    SampleNotFoundError,
    TransformerNotFoundError,
)
from src.dga.domain.models.gas_reading import GasReading
from src.dga.domain.models.sample import Sample
from src.dga.domain.models.transformer import Transformer
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


# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------

@pytest.fixture()
def connection():
    """Conexion SQLite en memoria con esquema inicializado."""
    conn = get_connection(":memory:")
    initialize_database(conn)
    yield conn
    conn.close()


@pytest.fixture()
def transformer_repo(connection) -> SQLiteTransformerRepository:
    """Repositorio de transformadores sobre la BD en memoria."""
    return SQLiteTransformerRepository(connection)


@pytest.fixture()
def sample_repo(connection) -> SQLiteSampleRepository:
    """Repositorio de muestras sobre la BD en memoria."""
    return SQLiteSampleRepository(connection)


def _gas_reading() -> GasReading:
    """Retorna un GasReading valido para los tests."""
    return GasReading(
        h2=10.0, ch4=5.0, c2h6=3.0, c2h4=2.0, c2h2=0.5,
        co=100.0, co2=500.0, o2=3000.0, n2=50000.0,
    )


# ======================================================================
# Transformer Repository
# ======================================================================

class TestSQLiteTransformerRepository:
    """Tests de integracion para SQLiteTransformerRepository."""

    def test_create_and_retrieve(
        self, transformer_repo: SQLiteTransformerRepository,
    ) -> None:
        """Crear y recuperar un transformador por ID."""
        trafo = transformer_repo.create(Transformer(name="T-01"))
        assert trafo.id is not None

        found = transformer_repo.get_by_id(trafo.id)
        assert found is not None
        assert found.name == "T-01"

    def test_get_all_returns_ordered_list(
        self, transformer_repo: SQLiteTransformerRepository,
    ) -> None:
        """get_all retorna la lista ordenada por ID."""
        transformer_repo.create(Transformer(name="T-B"))
        transformer_repo.create(Transformer(name="T-A"))

        all_trafos = transformer_repo.get_all()
        assert len(all_trafos) == 2
        assert all_trafos[0].name == "T-B"
        assert all_trafos[1].name == "T-A"

    def test_update_changes_name(
        self, transformer_repo: SQLiteTransformerRepository,
    ) -> None:
        """update modifica el nombre correctamente."""
        trafo = transformer_repo.create(Transformer(name="T-Old"))
        assert trafo.id is not None
        trafo.name = "T-New"
        updated = transformer_repo.update(trafo)

        assert updated.name == "T-New"
        found = transformer_repo.get_by_id(trafo.id)
        assert found is not None
        assert found.name == "T-New"

    def test_delete_removes_record(
        self, transformer_repo: SQLiteTransformerRepository,
    ) -> None:
        """delete elimina el registro."""
        trafo = transformer_repo.create(Transformer(name="T-Del"))
        assert trafo.id is not None
        transformer_repo.delete(trafo.id)

        assert transformer_repo.get_by_id(trafo.id) is None

    def test_duplicate_name_raises_error(
        self, transformer_repo: SQLiteTransformerRepository,
    ) -> None:
        """Nombre duplicado lanza DuplicateTransformerError."""
        transformer_repo.create(Transformer(name="T-Dup"))
        with pytest.raises(DuplicateTransformerError):
            transformer_repo.create(Transformer(name="T-Dup"))

    def test_delete_nonexistent_raises_error(
        self, transformer_repo: SQLiteTransformerRepository,
    ) -> None:
        """Eliminar un ID inexistente lanza TransformerNotFoundError."""
        with pytest.raises(TransformerNotFoundError):
            transformer_repo.delete(999)

    def test_update_nonexistent_raises_error(
        self, transformer_repo: SQLiteTransformerRepository,
    ) -> None:
        """Actualizar un ID inexistente lanza TransformerNotFoundError."""
        with pytest.raises(TransformerNotFoundError):
            transformer_repo.update(Transformer(name="Ghost", id=999))

    def test_get_by_id_nonexistent_returns_none(
        self, transformer_repo: SQLiteTransformerRepository,
    ) -> None:
        """Buscar un ID inexistente retorna None."""
        assert transformer_repo.get_by_id(999) is None


# ======================================================================
# Sample Repository
# ======================================================================

class TestSQLiteSampleRepository:
    """Tests de integracion para SQLiteSampleRepository."""

    def _create_transformer(
        self, repo: SQLiteTransformerRepository, name: str = "T-01",
    ) -> Transformer:
        """Helper para crear un transformador prerequisito."""
        trafo = repo.create(Transformer(name=name))
        assert trafo.id is not None
        return trafo

    def test_create_and_retrieve(
        self,
        sample_repo: SQLiteSampleRepository,
        transformer_repo: SQLiteTransformerRepository,
    ) -> None:
        """Crear y recuperar una muestra por ID."""
        trafo = self._create_transformer(transformer_repo)
        assert trafo.id is not None
        sample = Sample(
            sample_code="M-001",
            transformer_id=trafo.id,
            extraction_date=date(2025, 6, 15),
            gas_reading=_gas_reading(),
        )
        created = sample_repo.create(sample)
        assert created.id is not None

        found = sample_repo.get_by_id(created.id)
        assert found is not None
        assert found.sample_code == "M-001"
        assert found.gas_reading.h2 == 10.0
        assert found.extraction_date == date(2025, 6, 15)

    def test_get_by_transformer_id(
        self,
        sample_repo: SQLiteSampleRepository,
        transformer_repo: SQLiteTransformerRepository,
    ) -> None:
        """Filtrar muestras por transformador."""
        t1 = self._create_transformer(transformer_repo, "T-1")
        t2 = self._create_transformer(transformer_repo, "T-2")
        assert t1.id is not None
        assert t2.id is not None

        sample_repo.create(Sample(
            sample_code="M-A", transformer_id=t1.id,
            extraction_date=date(2025, 1, 1), gas_reading=_gas_reading(),
        ))
        sample_repo.create(Sample(
            sample_code="M-B", transformer_id=t2.id,
            extraction_date=date(2025, 2, 1), gas_reading=_gas_reading(),
        ))
        sample_repo.create(Sample(
            sample_code="M-C", transformer_id=t1.id,
            extraction_date=date(2025, 3, 1), gas_reading=_gas_reading(),
        ))

        t1_samples = sample_repo.get_by_transformer_id(t1.id)
        assert len(t1_samples) == 2

        t2_samples = sample_repo.get_by_transformer_id(t2.id)
        assert len(t2_samples) == 1

    def test_update_changes_data(
        self,
        sample_repo: SQLiteSampleRepository,
        transformer_repo: SQLiteTransformerRepository,
    ) -> None:
        """update modifica los datos correctamente."""
        trafo = self._create_transformer(transformer_repo)
        assert trafo.id is not None
        sample = sample_repo.create(Sample(
            sample_code="M-U1", transformer_id=trafo.id,
            extraction_date=date(2025, 1, 1), gas_reading=_gas_reading(),
        ))
        assert sample.id is not None

        new_reading = GasReading(
            h2=99.0, ch4=5.0, c2h6=3.0, c2h4=2.0, c2h2=0.5,
            co=100.0, co2=500.0, o2=3000.0, n2=50000.0,
        )
        sample.sample_code = "M-U1-MOD"
        sample.gas_reading = new_reading
        updated = sample_repo.update(sample)

        assert updated.id is not None
        found = sample_repo.get_by_id(updated.id)
        assert found is not None
        assert found.sample_code == "M-U1-MOD"
        assert found.gas_reading.h2 == 99.0

    def test_delete_removes_record(
        self,
        sample_repo: SQLiteSampleRepository,
        transformer_repo: SQLiteTransformerRepository,
    ) -> None:
        """delete elimina la muestra."""
        trafo = self._create_transformer(transformer_repo)
        assert trafo.id is not None
        sample = sample_repo.create(Sample(
            sample_code="M-D1", transformer_id=trafo.id,
            extraction_date=date(2025, 1, 1), gas_reading=_gas_reading(),
        ))
        assert sample.id is not None
        sample_repo.delete(sample.id)

        assert sample_repo.get_by_id(sample.id) is None

    def test_duplicate_code_raises_error(
        self,
        sample_repo: SQLiteSampleRepository,
        transformer_repo: SQLiteTransformerRepository,
    ) -> None:
        """Codigo duplicado lanza DuplicateSampleCodeError."""
        trafo = self._create_transformer(transformer_repo)
        assert trafo.id is not None
        sample_repo.create(Sample(
            sample_code="DUP", transformer_id=trafo.id,
            extraction_date=date(2025, 1, 1), gas_reading=_gas_reading(),
        ))
        with pytest.raises(DuplicateSampleCodeError):
            sample_repo.create(Sample(
                sample_code="DUP", transformer_id=trafo.id,
                extraction_date=date(2025, 2, 1), gas_reading=_gas_reading(),
            ))

    def test_delete_nonexistent_raises_error(
        self, sample_repo: SQLiteSampleRepository,
    ) -> None:
        """Eliminar un ID inexistente lanza SampleNotFoundError."""
        with pytest.raises(SampleNotFoundError):
            sample_repo.delete(999)

    def test_cascade_delete_on_transformer(
        self,
        sample_repo: SQLiteSampleRepository,
        transformer_repo: SQLiteTransformerRepository,
    ) -> None:
        """Eliminar un transformador elimina sus muestras en cascada."""
        trafo = self._create_transformer(transformer_repo, "T-Cascade")
        assert trafo.id is not None
        sample_repo.create(Sample(
            sample_code="M-CAS-1", transformer_id=trafo.id,
            extraction_date=date(2025, 1, 1), gas_reading=_gas_reading(),
        ))
        sample_repo.create(Sample(
            sample_code="M-CAS-2", transformer_id=trafo.id,
            extraction_date=date(2025, 2, 1), gas_reading=_gas_reading(),
        ))

        transformer_repo.delete(trafo.id)

        remaining = sample_repo.get_by_transformer_id(trafo.id)
        assert len(remaining) == 0

    def test_gas_reading_values_round_trip(
        self,
        sample_repo: SQLiteSampleRepository,
        transformer_repo: SQLiteTransformerRepository,
    ) -> None:
        """Los 9 valores de gas sobreviven el ciclo persist/retrieve."""
        trafo = self._create_transformer(transformer_repo, "T-RT")
        assert trafo.id is not None
        reading = GasReading(
            h2=1.1, ch4=2.2, c2h6=3.3, c2h4=4.4, c2h2=5.5,
            co=6.6, co2=7.7, o2=8.8, n2=9.9,
        )
        sample = sample_repo.create(Sample(
            sample_code="M-RT", transformer_id=trafo.id,
            extraction_date=date(2025, 5, 20), gas_reading=reading,
        ))
        assert sample.id is not None

        found = sample_repo.get_by_id(sample.id)
        assert found is not None
        assert found.gas_reading == reading
