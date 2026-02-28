"""Implementacion SQLite del repositorio de muestras DGA.

Adaptador concreto que cumple con el contrato definido por el puerto
``SampleRepository``. Gestiona la serializacion de las fechas en formato
ISO 8601 (TEXT) y la reconstruccion del Value Object ``GasReading`` a
partir de las 9 columnas de gas.
"""

from __future__ import annotations

import sqlite3
from datetime import date
from typing import Optional

from src.dga.domain.exceptions import (
    DuplicateSampleCodeError,
    SampleNotFoundError,
)
from src.dga.domain.models.gas_reading import GasReading
from src.dga.domain.models.sample import Sample
from src.dga.domain.ports.sample_repository import SampleRepository

# Nombres de las columnas de gas en el orden canonico de la tabla.
_GAS_COLUMNS = ("h2", "ch4", "c2h6", "c2h4", "c2h2", "co", "co2", "o2", "n2")


class SQLiteSampleRepository(SampleRepository):
    """Repositorio de muestras de aceite respaldado por SQLite.

    Args:
        connection: Conexion SQLite activa con foreign keys habilitadas.
    """

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._conn = connection

    # ------------------------------------------------------------------
    # Mapeo fila -> entidad
    # ------------------------------------------------------------------

    @staticmethod
    def _row_to_entity(row: sqlite3.Row) -> Sample:
        """Convierte una fila SQLite en una entidad Sample con GasReading.

        Args:
            row: Fila con todas las columnas de la tabla ``samples``.

        Returns:
            Entidad de dominio poblada.
        """
        gas_reading = GasReading(
            **{col: row[col] for col in _GAS_COLUMNS}
        )
        return Sample(
            id=row["id"],
            sample_code=row["sample_code"],
            transformer_id=row["transformer_id"],
            extraction_date=date.fromisoformat(row["extraction_date"]),
            diagnosis_date=date.fromisoformat(row["diagnosis_date"]),
            gas_reading=gas_reading,
        )

    # ------------------------------------------------------------------
    # Construccion de parametros SQL
    # ------------------------------------------------------------------

    @staticmethod
    def _entity_to_params(sample: Sample) -> tuple:
        """Extrae los parametros de una entidad para una sentencia INSERT/UPDATE.

        El orden coincide con los placeholders de las sentencias SQL definidas
        en los metodos ``create`` y ``update``.

        Args:
            sample: Entidad de muestra.

        Returns:
            Tupla de valores en el orden esperado por las sentencias SQL.
        """
        reading = sample.gas_reading
        return (
            sample.sample_code,
            sample.transformer_id,
            sample.extraction_date.isoformat(),
            sample.diagnosis_date.isoformat(),
            reading.h2,
            reading.ch4,
            reading.c2h6,
            reading.c2h4,
            reading.c2h2,
            reading.co,
            reading.co2,
            reading.o2,
            reading.n2,
        )

    # ------------------------------------------------------------------
    # Operaciones CRUD
    # ------------------------------------------------------------------

    def create(self, sample: Sample) -> Sample:
        """Persiste una nueva muestra de aceite.

        Args:
            sample: Entidad sin ID.

        Returns:
            Entidad con ``id`` asignado.

        Raises:
            DuplicateSampleCodeError: Si el codigo de muestra ya existe.
        """
        sql = (
            "INSERT INTO samples "
            "(sample_code, transformer_id, extraction_date, diagnosis_date, "
            "h2, ch4, c2h6, c2h4, c2h2, co, co2, o2, n2) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        )
        try:
            cursor = self._conn.execute(sql, self._entity_to_params(sample))
            self._conn.commit()
        except sqlite3.IntegrityError as exc:
            error_msg = str(exc).lower()
            if "unique" in error_msg and "sample_code" in error_msg:
                raise DuplicateSampleCodeError(sample.sample_code)
            raise
        sample.id = cursor.lastrowid
        return sample

    def get_by_id(self, sample_id: int) -> Optional[Sample]:
        """Busca una muestra por su ID.

        Args:
            sample_id: ID a buscar.

        Returns:
            Entidad encontrada o ``None``.
        """
        sql = "SELECT * FROM samples WHERE id = ?"
        row = self._conn.execute(sql, (sample_id,)).fetchone()
        if row is None:
            return None
        return self._row_to_entity(row)

    def get_by_transformer_id(self, transformer_id: int) -> list[Sample]:
        """Retorna las muestras de un transformador, ordenadas por fecha.

        Args:
            transformer_id: ID del transformador.

        Returns:
            Lista de muestras ordenadas por fecha de extraccion descendente.
        """
        sql = (
            "SELECT * FROM samples "
            "WHERE transformer_id = ? "
            "ORDER BY extraction_date DESC"
        )
        rows = self._conn.execute(sql, (transformer_id,)).fetchall()
        return [self._row_to_entity(row) for row in rows]

    def get_all(self) -> list[Sample]:
        """Retorna todas las muestras ordenadas por ID.

        Returns:
            Lista de entidades.
        """
        sql = "SELECT * FROM samples ORDER BY id"
        rows = self._conn.execute(sql).fetchall()
        return [self._row_to_entity(row) for row in rows]

    def update(self, sample: Sample) -> Sample:
        """Actualiza los datos de una muestra existente.

        Args:
            sample: Entidad con ``id`` y datos actualizados.

        Returns:
            Entidad actualizada.

        Raises:
            SampleNotFoundError: Si el ID no existe.
            DuplicateSampleCodeError: Si el codigo ya esta en uso.
        """
        sql = (
            "UPDATE samples SET "
            "sample_code = ?, transformer_id = ?, extraction_date = ?, "
            "diagnosis_date = ?, h2 = ?, ch4 = ?, c2h6 = ?, c2h4 = ?, "
            "c2h2 = ?, co = ?, co2 = ?, o2 = ?, n2 = ? "
            "WHERE id = ?"
        )
        params = self._entity_to_params(sample) + (sample.id,)
        try:
            cursor = self._conn.execute(sql, params)
            self._conn.commit()
        except sqlite3.IntegrityError as exc:
            error_msg = str(exc).lower()
            if "unique" in error_msg and "sample_code" in error_msg:
                raise DuplicateSampleCodeError(sample.sample_code)
            raise

        if cursor.rowcount == 0:
            assert sample.id is not None
            raise SampleNotFoundError(sample.id)
        return sample

    def delete(self, sample_id: int) -> None:
        """Elimina una muestra por su ID.

        Args:
            sample_id: ID de la muestra a eliminar.

        Raises:
            SampleNotFoundError: Si el ID no existe.
        """
        sql = "DELETE FROM samples WHERE id = ?"
        cursor = self._conn.execute(sql, (sample_id,))
        self._conn.commit()
        if cursor.rowcount == 0:
            raise SampleNotFoundError(sample_id)
