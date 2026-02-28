"""Gestion de la conexion SQLite y esquema de base de datos.

Provee una factoria de conexiones y la inicializacion del esquema DDL.
Cada conexion activa las claves foraneas (PRAGMA foreign_keys = ON) para
garantizar la integridad referencial, incluyendo borrado en cascada.

Tablas:
    - transformers: Equipos de potencia.
    - samples: Muestras de aceite con lecturas de gases disueltos.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS transformers (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT    NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS samples (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    sample_code     TEXT    NOT NULL UNIQUE,
    transformer_id  INTEGER NOT NULL
        REFERENCES transformers(id) ON DELETE CASCADE,
    extraction_date TEXT    NOT NULL,
    diagnosis_date  TEXT    NOT NULL,
    h2              REAL    NOT NULL,
    ch4             REAL    NOT NULL,
    c2h6            REAL    NOT NULL,
    c2h4            REAL    NOT NULL,
    c2h2            REAL    NOT NULL,
    co              REAL    NOT NULL,
    co2             REAL    NOT NULL,
    o2              REAL    NOT NULL,
    n2              REAL    NOT NULL
);
"""


def get_connection(db_path: str | Path = "dga.db") -> sqlite3.Connection:
    """Crea y retorna una conexion SQLite con claves foraneas habilitadas.

    Args:
        db_path: Ruta al archivo de base de datos. Tambien acepta
            ``\":memory:\"`` para bases de datos en memoria (util en tests).

    Returns:
        Conexion SQLite lista para operar.
    """
    connection = sqlite3.connect(str(db_path), check_same_thread=False)
    connection.execute("PRAGMA foreign_keys = ON;")
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database(connection: sqlite3.Connection) -> None:
    """Ejecuta el esquema DDL para crear las tablas si no existen.

    Es idempotente: puede invocarse multiples veces sin efecto adverso
    gracias a ``CREATE TABLE IF NOT EXISTS``.

    Args:
        connection: Conexion SQLite activa.
    """
    connection.executescript(_SCHEMA_SQL)
    connection.commit()
