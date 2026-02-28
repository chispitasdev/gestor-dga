"""Implementacion SQLite del repositorio de transformadores.

Adaptador concreto que cumple con el contrato definido por el puerto
``TransformerRepository``. Traduce las operaciones de dominio a sentencias
SQL parametrizadas y mapea los resultados a entidades de dominio.
"""

from __future__ import annotations

import sqlite3
from typing import Optional

from src.dga.domain.exceptions import (
    DuplicateTransformerError,
    TransformerNotFoundError,
)
from src.dga.domain.models.transformer import Transformer
from src.dga.domain.ports.transformer_repository import TransformerRepository


class SQLiteTransformerRepository(TransformerRepository):
    """Repositorio de transformadores respaldado por SQLite.

    Args:
        connection: Conexion SQLite activa con foreign keys habilitadas.
    """

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._conn = connection

    # ------------------------------------------------------------------
    # Mapeo fila -> entidad
    # ------------------------------------------------------------------

    @staticmethod
    def _row_to_entity(row: sqlite3.Row) -> Transformer:
        """Convierte una fila SQLite en una entidad Transformer.

        Args:
            row: Fila con columnas ``id`` y ``name``.

        Returns:
            Entidad de dominio poblada.
        """
        return Transformer(id=row["id"], name=row["name"])

    # ------------------------------------------------------------------
    # Operaciones CRUD
    # ------------------------------------------------------------------

    def create(self, transformer: Transformer) -> Transformer:
        """Persiste un nuevo transformador.

        Args:
            transformer: Entidad sin ID.

        Returns:
            Entidad con ``id`` asignado.

        Raises:
            DuplicateTransformerError: Si el nombre ya existe.
        """
        sql = "INSERT INTO transformers (name) VALUES (?)"
        try:
            cursor = self._conn.execute(sql, (transformer.name,))
            self._conn.commit()
        except sqlite3.IntegrityError:
            raise DuplicateTransformerError(transformer.name)
        transformer.id = cursor.lastrowid
        return transformer

    def get_by_id(self, transformer_id: int) -> Optional[Transformer]:
        """Busca un transformador por ID.

        Args:
            transformer_id: ID a buscar.

        Returns:
            Entidad encontrada o ``None``.
        """
        sql = "SELECT id, name FROM transformers WHERE id = ?"
        row = self._conn.execute(sql, (transformer_id,)).fetchone()
        if row is None:
            return None
        return self._row_to_entity(row)

    def get_all(self) -> list[Transformer]:
        """Retorna todos los transformadores ordenados por ID.

        Returns:
            Lista de entidades.
        """
        sql = "SELECT id, name FROM transformers ORDER BY id"
        rows = self._conn.execute(sql).fetchall()
        return [self._row_to_entity(row) for row in rows]

    def update(self, transformer: Transformer) -> Transformer:
        """Actualiza el nombre de un transformador.

        Args:
            transformer: Entidad con ``id`` y nuevo ``name``.

        Returns:
            Entidad actualizada.

        Raises:
            TransformerNotFoundError: Si el ID no existe.
            DuplicateTransformerError: Si el nombre ya esta en uso.
        """
        sql = "UPDATE transformers SET name = ? WHERE id = ?"
        try:
            cursor = self._conn.execute(
                sql, (transformer.name, transformer.id)
            )
            self._conn.commit()
        except sqlite3.IntegrityError:
            raise DuplicateTransformerError(transformer.name)

        if cursor.rowcount == 0:
            assert transformer.id is not None
            raise TransformerNotFoundError(transformer.id)
        return transformer

    def delete(self, transformer_id: int) -> None:
        """Elimina un transformador y sus muestras asociadas (CASCADE).

        Args:
            transformer_id: ID del transformador a eliminar.

        Raises:
            TransformerNotFoundError: Si el ID no existe.
        """
        sql = "DELETE FROM transformers WHERE id = ?"
        cursor = self._conn.execute(sql, (transformer_id,))
        self._conn.commit()
        if cursor.rowcount == 0:
            raise TransformerNotFoundError(transformer_id)
