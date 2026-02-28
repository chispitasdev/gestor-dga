"""Tests unitarios para ImportService."""

import csv
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.dga.application.services.import_service import (
    ImportService,
    ImportResult,
    _normalize_columns,
    _parse_date,
    _parse_float,
)


def _make_csv(tmp_dir: Path, rows: list[dict[str, str]], filename: str = "test.csv") -> Path:
    """Crea un archivo CSV temporal con las filas dadas."""
    path = tmp_dir / filename
    if not rows:
        path.write_text("", encoding="utf-8")
        return path
    fieldnames = list(rows[0].keys())
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return path


class TestNormalizeColumns:

    def test_valid_columns(self) -> None:
        columns = [
            "sample_code", "extraction_date",
            "h2", "ch4", "c2h6", "c2h4", "c2h2", "co", "co2", "o2", "n2",
        ]
        result = _normalize_columns(columns)
        assert result["sample_code"] == "sample_code"
        assert result["extraction_date"] == "extraction_date"

    def test_aliases(self) -> None:
        columns = [
            "codigo_muestra", "fecha_extraccion",
            "h2", "ch4", "c2h6", "c2h4", "c2h2", "co", "co2", "o2", "n2",
        ]
        result = _normalize_columns(columns)
        assert result["codigo_muestra"] == "sample_code"

    def test_missing_columns_raises(self) -> None:
        with pytest.raises(ValueError, match="Columnas faltantes"):
            _normalize_columns(["h2", "ch4"])


class TestParseDate:

    def test_dd_mm_yyyy(self) -> None:
        assert _parse_date("15/03/2024") == date(2024, 3, 15)

    def test_yyyy_mm_dd(self) -> None:
        assert _parse_date("2024-03-15") == date(2024, 3, 15)

    def test_date_object(self) -> None:
        d = date(2024, 1, 1)
        assert _parse_date(d) == d

    def test_invalid_raises(self) -> None:
        with pytest.raises(ValueError):
            _parse_date("not-a-date")


class TestParseFloat:

    def test_valid_number(self) -> None:
        assert _parse_float("10.5", "h2", 2) == 10.5

    def test_negative_raises(self) -> None:
        with pytest.raises(ValueError, match="invalido"):
            _parse_float("-5", "h2", 2)

    def test_invalid_raises(self) -> None:
        with pytest.raises(ValueError, match="invalido"):
            _parse_float("abc", "h2", 2)


class TestImportService:

    def setup_method(self) -> None:
        self.mock_sample_service = MagicMock()
        # register_sample returns a fake Sample
        self.mock_sample_service.register_sample.return_value = MagicMock(id=1)
        self.service = ImportService(self.mock_sample_service)

    def test_import_csv_success(self, tmp_path: Path) -> None:
        rows = [
            {
                "sample_code": "M-001", "extraction_date": "15/03/2024",
                "h2": "100", "ch4": "50", "c2h6": "30", "c2h4": "20",
                "c2h2": "5", "co": "200", "co2": "3000", "o2": "18000", "n2": "50000",
            },
            {
                "sample_code": "M-002", "extraction_date": "20/04/2024",
                "h2": "120", "ch4": "60", "c2h6": "35", "c2h4": "25",
                "c2h2": "8", "co": "250", "co2": "3500", "o2": "17000", "n2": "49000",
            },
        ]
        csv_path = _make_csv(tmp_path, rows)

        result = self.service.import_from_file(csv_path, transformer_id=1)

        assert isinstance(result, ImportResult)
        assert result.total_rows == 2
        assert result.imported == 2
        assert result.skipped == 0
        assert result.errors == []
        assert self.mock_sample_service.register_sample.call_count == 2

    def test_import_csv_with_errors(self, tmp_path: Path) -> None:
        rows = [
            {
                "sample_code": "M-001", "extraction_date": "15/03/2024",
                "h2": "100", "ch4": "50", "c2h6": "30", "c2h4": "20",
                "c2h2": "5", "co": "200", "co2": "3000", "o2": "18000", "n2": "50000",
            },
            {
                "sample_code": "M-002", "extraction_date": "invalid-date",
                "h2": "abc", "ch4": "50", "c2h6": "30", "c2h4": "20",
                "c2h2": "5", "co": "200", "co2": "3000", "o2": "18000", "n2": "50000",
            },
        ]
        csv_path = _make_csv(tmp_path, rows)

        result = self.service.import_from_file(csv_path, transformer_id=1)

        assert result.imported == 1
        assert result.skipped == 1
        assert len(result.errors) == 1

    def test_file_not_found(self) -> None:
        with pytest.raises(FileNotFoundError):
            self.service.import_from_file("nonexistent.csv", transformer_id=1)

    def test_unsupported_format(self, tmp_path: Path) -> None:
        path = tmp_path / "data.txt"
        path.write_text("data")
        with pytest.raises(ValueError, match="Formato no soportado"):
            self.service.import_from_file(path, transformer_id=1)

    def test_empty_csv(self, tmp_path: Path) -> None:
        path = tmp_path / "empty.csv"
        path.write_text("", encoding="utf-8")
        result = self.service.import_from_file(path, transformer_id=1)
        assert result.total_rows == 0

    def test_alias_columns(self, tmp_path: Path) -> None:
        """Verifica que columnas con nombres en espanol funcionan."""
        rows = [
            {
                "codigo_muestra": "M-001", "fecha_extraccion": "15/03/2024",
                "h2": "100", "ch4": "50", "c2h6": "30", "c2h4": "20",
                "c2h2": "5", "co": "200", "co2": "3000", "o2": "18000", "n2": "50000",
            },
        ]
        csv_path = _make_csv(tmp_path, rows)

        result = self.service.import_from_file(csv_path, transformer_id=1)
        assert result.imported == 1
