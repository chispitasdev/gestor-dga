"""Value Object que encapsula las concentraciones de los 9 gases disueltos.

Cada instancia representa una lectura inmutable de cromatografia de gases
realizada sobre una muestra de aceite de transformador de potencia. Los valores
se expresan en partes por millon (ppm).

Gases combustibles (de falla):
    - H2  : Hidrogeno
    - CH4 : Metano
    - C2H6: Etano
    - C2H4: Etileno
    - C2H2: Acetileno
    - CO  : Monoxido de carbono

Gases no combustibles (atmosfericos / degradacion):
    - CO2 : Dioxido de carbono
    - O2  : Oxigeno
    - N2  : Nitrogeno
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from src.dga.domain.exceptions import InvalidGasValueError


@dataclass(frozen=True, slots=True)
class GasReading:
    """Lectura inmutable de concentraciones de gases disueltos en ppm.

    Al ser un Value Object (frozen dataclass), dos instancias con los mismos
    valores se consideran iguales y no poseen identidad propia.

    Attributes:
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

    h2: float
    ch4: float
    c2h6: float
    c2h4: float
    c2h2: float
    co: float
    co2: float
    o2: float
    n2: float

    # Nombres descriptivos para presentacion, indexados por atributo.
    GAS_LABELS: ClassVar[dict[str, str]] = {
        "h2": "Hidrogeno (H2)",
        "ch4": "Metano (CH4)",
        "c2h6": "Etano (C2H6)",
        "c2h4": "Etileno (C2H4)",
        "c2h2": "Acetileno (C2H2)",
        "co": "Monoxido de Carbono (CO)",
        "co2": "Dioxido de Carbono (CO2)",
        "o2": "Oxigeno (O2)",
        "n2": "Nitrogeno (N2)",
    }

    def __post_init__(self) -> None:
        """Valida que todas las concentraciones sean no negativas."""
        gas_fields = (
            "h2", "ch4", "c2h6", "c2h4", "c2h2", "co", "co2", "o2", "n2"
        )
        for field_name in gas_fields:
            value = getattr(self, field_name)
            if not isinstance(value, (int, float)):
                raise InvalidGasValueError(
                    f"El gas '{field_name}' debe ser numerico, "
                    f"se recibio: {type(value).__name__}."
                )
            if value < 0:
                raise InvalidGasValueError(
                    f"El gas '{field_name}' no puede ser negativo "
                    f"(valor recibido: {value})."
                )



    @classmethod
    def field_names(cls) -> tuple[str, ...]:
        """Retorna los nombres de los campos de gas en orden canonico.

        Returns:
            Tupla con los 9 nombres de atributo.
        """
        return ("h2", "ch4", "c2h6", "c2h4", "c2h2", "co", "co2", "o2", "n2")

    @classmethod
    def descriptive_labels(cls) -> dict[str, str]:
        """Retorna el mapeo de nombre de campo a etiqueta descriptiva.

        Returns:
            Diccionario campo -> etiqueta legible.
        """
        return {
            "h2": "Hidrogeno (H2)",
            "ch4": "Metano (CH4)",
            "c2h6": "Etano (C2H6)",
            "c2h4": "Etileno (C2H4)",
            "c2h2": "Acetileno (C2H2)",
            "co": "Monoxido de Carbono (CO)",
            "co2": "Dioxido de Carbono (CO2)",
            "o2": "Oxigeno (O2)",
            "n2": "Nitrogeno (N2)",
        }

    def as_dict(self) -> dict[str, float]:
        """Convierte la lectura a un diccionario campo -> valor.

        Returns:
            Diccionario con los 9 valores de gas.
        """
        return {name: getattr(self, name) for name in self.field_names()}
