"""Data Transfer Objects para la entidad Sample.

Encapsulan los datos de entrada del usuario para las operaciones de creacion
y actualizacion de muestras DGA. La ``diagnosis_date`` no aparece en el DTO
de creacion porque se asigna automaticamente con la fecha actual.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class CreateSampleDTO:
    """Datos necesarios para registrar una nueva muestra de aceite.

    Attributes:
        sample_code: Codigo identificador legible de la muestra.
        transformer_id: ID del transformador al que pertenece.
        extraction_date: Fecha en que se tomo la muestra.
        h2: Concentracion de hidrogeno (ppm).
        ch4: Concentracion de metano (ppm).
        c2h6: Concentracion de etano (ppm).
        c2h4: Concentracion de etileno (ppm).
        c2h2: Concentracion de acetileno (ppm).
        co: Concentracion de monoxido de carbono (ppm).
        co2: Concentracion de dioxido de carbono (ppm).
        o2: Concentracion de oxigeno (ppm).
        n2: Concentracion de nitrogeno (ppm).
    """

    sample_code: str
    transformer_id: int
    extraction_date: date
    h2: float
    ch4: float
    c2h6: float
    c2h4: float
    c2h2: float
    co: float
    co2: float
    o2: float
    n2: float


@dataclass(frozen=True, slots=True)
class UpdateSampleDTO:
    """Datos necesarios para actualizar una muestra existente.

    Attributes:
        id: Identificador de la muestra a actualizar.
        sample_code: Codigo identificador legible de la muestra.
        transformer_id: ID del transformador al que pertenece.
        extraction_date: Fecha en que se tomo la muestra.
        diagnosis_date: Fecha del diagnostico.
        h2: Concentracion de hidrogeno (ppm).
        ch4: Concentracion de metano (ppm).
        c2h6: Concentracion de etano (ppm).
        c2h4: Concentracion de etileno (ppm).
        c2h2: Concentracion de acetileno (ppm).
        co: Concentracion de monoxido de carbono (ppm).
        co2: Concentracion de dioxido de carbono (ppm).
        o2: Concentracion de oxigeno (ppm).
        n2: Concentracion de nitrogeno (ppm).
    """

    id: int
    sample_code: str
    transformer_id: int
    extraction_date: date
    diagnosis_date: date
    h2: float
    ch4: float
    c2h6: float
    c2h4: float
    c2h2: float
    co: float
    co2: float
    o2: float
    n2: float
