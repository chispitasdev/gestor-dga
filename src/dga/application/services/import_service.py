"""Servicio de importacion masiva de muestras desde archivos Excel/CSV.

Permite cargar multiples lecturas de gases disueltos desde un archivo
tabular (Excel .xlsx o CSV .csv) y persistirlas como muestras asociadas
a un transformador. Valida el formato de columnas y los datos antes de
insertar.

Columnas esperadas (nombres sin tildes, insensible a mayusculas):
    sample_code | codigo_muestra
    extraction_date | fecha_extraccion   (formato DD/MM/YYYY o YYYY-MM-DD)
    h2, ch4, c2h6, c2h4, c2h2, co, co2, o2, n2   (ppm)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

from src.dga.application.dto.sample_dto import CreateSampleDTO
from src.dga.application.services.sample_service import SampleService


@dataclass(frozen=True, slots=True)
class ImportResult:
    """Resultado de una operacion de importacion masiva.

    Attributes:
        total_rows: Total de filas leidas del archivo.
        imported: Cantidad de muestras insertadas exitosamente.
        skipped: Cantidad de filas omitidas por error.
        errors: Lista de mensajes de error por fila.
    """

    total_rows: int
    imported: int
    skipped: int
    errors: list[str]


# ── Mapeo de nombres de columna aceptados ──────────────────────────
_COLUMN_ALIASES: dict[str, str] = {
    "sample_code": "sample_code",
    "codigo_muestra": "sample_code",
    "codigo": "sample_code",
    "extraction_date": "extraction_date",
    "fecha_extraccion": "extraction_date",
    "fecha": "extraction_date",
    "h2": "h2", "ch4": "ch4", "c2h6": "c2h6", "c2h4": "c2h4",
    "c2h2": "c2h2", "co": "co", "co2": "co2", "o2": "o2", "n2": "n2",
    "hidrogeno": "h2", "metano": "ch4", "etano": "c2h6",
    "etileno": "c2h4", "acetileno": "c2h2",
}

_REQUIRED_FIELDS = {
    "sample_code", "extraction_date",
    "h2", "ch4", "c2h6", "c2h4", "c2h2", "co", "co2", "o2", "n2",
}

_GAS_FIELDS = ("h2", "ch4", "c2h6", "c2h4", "c2h2", "co", "co2", "o2", "n2")


def _normalize_columns(columns: list[str]) -> dict[str, str]:
    """Mapea las columnas del archivo a nombres canonicos.

    Returns:
        Diccionario: nombre_original -> nombre_canonico.

    Raises:
        ValueError: Si faltan columnas requeridas.
    """
    mapping: dict[str, str] = {}
    for col in columns:
        normalized = col.strip().lower().replace(" ", "_")
        canonical = _COLUMN_ALIASES.get(normalized)
        if canonical:
            mapping[col] = canonical

    found = set(mapping.values())
    missing = _REQUIRED_FIELDS - found
    if missing:
        raise ValueError(
            f"Columnas faltantes en el archivo: {', '.join(sorted(missing))}. "
            f"Columnas encontradas: {', '.join(columns)}"
        )
    return mapping


def _parse_date(value: Any) -> date:
    """Parsea un valor a fecha. Acepta varios formatos."""
    if isinstance(value, date):
        return value
    if isinstance(value, datetime):
        return value.date()

    raw = str(value).strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"No se pudo interpretar la fecha: '{raw}'")


def _parse_float(value: Any, field: str, row_num: int) -> float:
    """Convierte un valor a float con mensaje de error descriptivo."""
    try:
        result = float(value)
        if result < 0:
            raise ValueError(f"Valor negativo para '{field}'")
        return result
    except (ValueError, TypeError):
        raise ValueError(
            f"Fila {row_num}: valor invalido para '{field}': {value!r}"
        )


class ImportService:
    """Servicio para importar muestras desde archivos tabulares.

    Args:
        sample_service: Servicio de aplicacion de muestras.
    """

    def __init__(self, sample_service: SampleService) -> None:
        self._sample_svc = sample_service

    def import_from_file(
        self, file_path: str | Path, transformer_id: int
    ) -> ImportResult:
        """Importa muestras desde un archivo Excel (.xlsx) o CSV (.csv).

        Args:
            file_path: Ruta al archivo de datos.
            transformer_id: ID del transformador al que se asignaran las muestras.

        Returns:
            ImportResult con el resumen de la operacion.

        Raises:
            FileNotFoundError: Si el archivo no existe.
            ValueError: Si el formato no es soportado o faltan columnas.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {path}")

        suffix = path.suffix.lower()
        if suffix == ".csv":
            rows = self._read_csv(path)
        elif suffix in (".xlsx", ".xls"):
            rows = self._read_excel(path)
        else:
            raise ValueError(
                f"Formato no soportado: '{suffix}'. Use .csv o .xlsx"
            )

        if not rows:
            return ImportResult(total_rows=0, imported=0, skipped=0, errors=[])

        return self._process_rows(rows, transformer_id)

    @staticmethod
    def _read_csv(path: Path) -> list[dict[str, Any]]:
        """Lee un archivo CSV y retorna lista de diccionarios."""
        import csv

        with open(path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            return list(reader)

    @staticmethod
    def _read_excel(path: Path) -> list[dict[str, Any]]:
        """Lee un archivo Excel y retorna lista de diccionarios."""
        try:
            import openpyxl
        except ImportError:
            raise ImportError(
                "Se requiere 'openpyxl' para leer archivos Excel. "
                "Instale con: pip install openpyxl"
            )

        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        ws = wb.active
        if ws is None:
            wb.close()
            raise ValueError("El archivo Excel no tiene una hoja activa.")
        rows_iter = ws.iter_rows(values_only=True)

        try:
            header = next(rows_iter)
        except StopIteration:
            wb.close()
            return []

        columns = [str(h).strip() if h else f"col_{i}" for i, h in enumerate(header)]
        data = []
        for row in rows_iter:
            if all(cell is None for cell in row):
                continue
            data.append(dict(zip(columns, row)))
        wb.close()
        return data

    def _process_rows(
        self, rows: list[dict[str, Any]], transformer_id: int
    ) -> ImportResult:
        """Procesa las filas normalizadas y crea muestras."""
        # Normalizar columnas usando la primera fila
        raw_columns = list(rows[0].keys())
        col_map = _normalize_columns(raw_columns)

        imported = 0
        skipped = 0
        errors: list[str] = []

        for i, row in enumerate(rows, start=2):  # fila 2 en adelante (1=header)
            try:
                # Mapear valores
                mapped: dict[str, Any] = {}
                for original_col, canonical in col_map.items():
                    mapped[canonical] = row.get(original_col)

                # Parsear campos
                sample_code = str(mapped["sample_code"]).strip()
                if not sample_code:
                    raise ValueError("Codigo de muestra vacio")

                extraction_date = _parse_date(mapped["extraction_date"])

                gas_values = {
                    field: _parse_float(mapped[field], field, i)
                    for field in _GAS_FIELDS
                }

                dto = CreateSampleDTO(
                    sample_code=sample_code,
                    transformer_id=transformer_id,
                    extraction_date=extraction_date,
                    **gas_values,
                )
                self._sample_svc.register_sample(dto)
                imported += 1

            except Exception as exc:
                skipped += 1
                errors.append(f"Fila {i}: {exc}")

        return ImportResult(
            total_rows=len(rows),
            imported=imported,
            skipped=skipped,
            errors=errors,
        )
