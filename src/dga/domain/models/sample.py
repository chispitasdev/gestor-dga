"""Entidad de dominio que representa una muestra de aceite con su lectura DGA.

Cada muestra esta vinculada a un transformador de potencia y contiene las
concentraciones de los 9 gases disueltos medidos por cromatografia, junto
con las fechas de extraccion y diagnostico.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from src.dga.domain.models.gas_reading import GasReading


@dataclass(slots=True)
class Sample:
    """Muestra de aceite con lectura de gases disueltos.

    Attributes:
        sample_code: Codigo o identificador legible de la muestra.
        transformer_id: Identificador del transformador asociado.
        extraction_date: Fecha en que se extrajo la muestra de aceite.
        gas_reading: Value object con las concentraciones de gases.
        diagnosis_date: Fecha del diagnostico. Por defecto, la fecha actual.
        id: Identificador unico autogenerado por la base de datos.
            Es ``None`` cuando la entidad aun no ha sido persistida.
    """

    sample_code: str
    transformer_id: int
    extraction_date: date
    gas_reading: GasReading
    diagnosis_date: date = field(default_factory=date.today)
    id: Optional[int] = None

    def __post_init__(self) -> None:
        """Valida las invariantes de la entidad."""
        self.sample_code = self.sample_code.strip()
        if not self.sample_code:
            raise ValueError(
                "El codigo de muestra no puede estar vacio."
            )
        if self.transformer_id is None or self.transformer_id < 1:
            raise ValueError(
                "El identificador del transformador debe ser un entero positivo."
            )
        if self.extraction_date > date.today():
            raise ValueError(
                "La fecha de extraccion no puede ser futura."
            )
