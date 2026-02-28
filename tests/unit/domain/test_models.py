"""Tests unitarios para los modelos de dominio.

Verifica las invariantes de las entidades Transformer, Sample y del
Value Object GasReading, incluyendo validaciones de datos y
comportamiento esperado ante entradas invalidas.
"""

from __future__ import annotations

from datetime import date

import pytest

from src.dga.domain.exceptions import InvalidGasValueError
from src.dga.domain.models.gas_reading import GasReading
from src.dga.domain.models.sample import Sample
from src.dga.domain.models.transformer import Transformer


# ======================================================================
# GasReading
# ======================================================================

class TestGasReading:
    """Suite de tests para el Value Object GasReading."""

    def _default_kwargs(self, **overrides: float) -> dict[str, float]:
        """Retorna un diccionario con valores validos por defecto.

        Args:
            **overrides: Valores a sobreescribir.

        Returns:
            Kwargs para construir un GasReading valido.
        """
        defaults = {
            "h2": 10.0, "ch4": 5.0, "c2h6": 3.0,
            "c2h4": 2.0, "c2h2": 0.5, "co": 100.0,
            "co2": 500.0, "o2": 3000.0, "n2": 50000.0,
        }
        defaults.update(overrides)
        return defaults

    def test_creation_with_valid_values(self) -> None:
        """Un GasReading con valores validos se crea correctamente."""
        reading = GasReading(**self._default_kwargs())
        assert reading.h2 == 10.0
        assert reading.n2 == 50000.0

    def test_frozen_immutability(self) -> None:
        """No se pueden modificar los atributos tras la creacion."""
        reading = GasReading(**self._default_kwargs())
        with pytest.raises(AttributeError):
            reading.h2 = 999.0  # type: ignore[misc]

    def test_negative_value_raises_error(self) -> None:
        """Un valor negativo lanza InvalidGasValueError."""
        with pytest.raises(InvalidGasValueError, match="negativo"):
            GasReading(**self._default_kwargs(c2h2=-1.0))

    def test_non_numeric_value_raises_error(self) -> None:
        """Un valor no numerico lanza InvalidGasValueError."""
        with pytest.raises(InvalidGasValueError, match="numerico"):
            GasReading(**self._default_kwargs(h2="abc"))  # type: ignore[arg-type]

    def test_zero_values_are_valid(self) -> None:
        """Los valores cero son validos (sin gas detectado)."""
        kwargs = {k: 0.0 for k in GasReading.field_names()}
        reading = GasReading(**kwargs)
        assert reading.h2 == 0.0

    def test_field_names_returns_nine_fields(self) -> None:
        """field_names retorna exactamente 9 campos."""
        fields = GasReading.field_names()
        assert len(fields) == 9
        assert fields[0] == "h2"
        assert fields[-1] == "n2"

    def test_as_dict_returns_all_values(self) -> None:
        """as_dict retorna un diccionario con los 9 valores."""
        reading = GasReading(**self._default_kwargs())
        result = reading.as_dict()
        assert len(result) == 9
        assert result["h2"] == 10.0

    def test_equality_by_value(self) -> None:
        """Dos GasReading con mismos valores son iguales."""
        kwargs = self._default_kwargs()
        reading_a = GasReading(**kwargs)
        reading_b = GasReading(**kwargs)
        assert reading_a == reading_b

    def test_descriptive_labels_has_nine_entries(self) -> None:
        """descriptive_labels retorna 9 etiquetas."""
        labels = GasReading.descriptive_labels()
        assert len(labels) == 9
        assert "Hidrogeno" in labels["h2"]


# ======================================================================
# Transformer
# ======================================================================

class TestTransformer:
    """Suite de tests para la entidad Transformer."""

    def test_creation_with_valid_name(self) -> None:
        """Se crea correctamente con un nombre valido."""
        trafo = Transformer(name="Trafo-01")
        assert trafo.name == "Trafo-01"
        assert trafo.id is None

    def test_name_is_stripped(self) -> None:
        """Los espacios se recortan del nombre."""
        trafo = Transformer(name="  Trafo-02  ")
        assert trafo.name == "Trafo-02"

    def test_empty_name_raises_error(self) -> None:
        """Un nombre vacio lanza ValueError."""
        with pytest.raises(ValueError, match="vacio"):
            Transformer(name="")

    def test_whitespace_only_name_raises_error(self) -> None:
        """Un nombre con solo espacios lanza ValueError."""
        with pytest.raises(ValueError, match="vacio"):
            Transformer(name="   ")

    def test_id_can_be_assigned(self) -> None:
        """Se puede crear con ID explicitamente."""
        trafo = Transformer(name="Trafo-03", id=42)
        assert trafo.id == 42


# ======================================================================
# Sample
# ======================================================================

class TestSample:
    """Suite de tests para la entidad Sample."""

    def _default_gas_reading(self) -> GasReading:
        """Retorna un GasReading valido para usar en samples."""
        return GasReading(
            h2=10.0, ch4=5.0, c2h6=3.0, c2h4=2.0, c2h2=0.5,
            co=100.0, co2=500.0, o2=3000.0, n2=50000.0,
        )

    def test_creation_with_valid_data(self) -> None:
        """Se crea correctamente con datos validos."""
        sample = Sample(
            sample_code="M-001",
            transformer_id=1,
            extraction_date=date(2025, 6, 15),
            gas_reading=self._default_gas_reading(),
        )
        assert sample.sample_code == "M-001"
        assert sample.transformer_id == 1
        assert sample.diagnosis_date == date.today()
        assert sample.id is None

    def test_empty_sample_code_raises_error(self) -> None:
        """Un codigo de muestra vacio lanza ValueError."""
        with pytest.raises(ValueError, match="codigo de muestra"):
            Sample(
                sample_code="",
                transformer_id=1,
                extraction_date=date(2025, 1, 1),
                gas_reading=self._default_gas_reading(),
            )

    def test_invalid_transformer_id_raises_error(self) -> None:
        """Un transformer_id no positivo lanza ValueError."""
        with pytest.raises(ValueError, match="entero positivo"):
            Sample(
                sample_code="M-002",
                transformer_id=0,
                extraction_date=date(2025, 1, 1),
                gas_reading=self._default_gas_reading(),
            )

    def test_future_extraction_date_raises_error(self) -> None:
        """Una fecha de extraccion futura lanza ValueError."""
        future_date = date(2099, 12, 31)
        with pytest.raises(ValueError, match="futura"):
            Sample(
                sample_code="M-003",
                transformer_id=1,
                extraction_date=future_date,
                gas_reading=self._default_gas_reading(),
            )

    def test_diagnosis_date_defaults_to_today(self) -> None:
        """La fecha de diagnostico se asigna como la fecha actual."""
        sample = Sample(
            sample_code="M-004",
            transformer_id=1,
            extraction_date=date(2025, 1, 1),
            gas_reading=self._default_gas_reading(),
        )
        assert sample.diagnosis_date == date.today()

    def test_sample_code_is_stripped(self) -> None:
        """Los espacios del codigo de muestra se recortan."""
        sample = Sample(
            sample_code="  M-005  ",
            transformer_id=1,
            extraction_date=date(2025, 1, 1),
            gas_reading=self._default_gas_reading(),
        )
        assert sample.sample_code == "M-005"
