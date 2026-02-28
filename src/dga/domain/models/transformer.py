"""Entidad de dominio que representa un transformador de potencia.

Un transformador es el equipo fisico cuyo aceite es sometido a analisis
cromatografico de gases disueltos (DGA). Cada transformador puede tener
multiples muestras asociadas a lo largo del tiempo.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class Transformer:
    """Entidad que identifica a un transformador de potencia.

    Attributes:
        id: Identificador unico autogenerado por la base de datos.
            Es ``None`` cuando la entidad aun no ha sido persistida.
        name: Nombre o designacion unica del transformador.
    """

    name: str
    id: Optional[int] = None

    def __post_init__(self) -> None:
        """Valida las invariantes de la entidad."""
        self.name = self.name.strip()
        if not self.name:
            raise ValueError(
                "El nombre del transformador no puede estar vacio."
            )
