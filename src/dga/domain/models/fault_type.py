"""Enumeracion de tipos de falla diagnosticables por AGD.

Codigos estandar segun IEEE C57.104-2019 e IEC 60599:2022.
Cada valor representa una condicion tipica identificable a traves
del analisis de gases disueltos en aceite de transformador.
"""

from __future__ import annotations

from enum import Enum


class FaultType(Enum):
    """Tipo de falla detectada por analisis de gases disueltos.

    Attributes:
        N: Funcionamiento normal (sin falla).
        PD: Descargas parciales (baja energia).
        D1: Descargas de baja energia (chispas).
        D2: Descargas de alta energia (arco electrico).
        T1: Falla termica < 300 °C.
        T2: Falla termica 300 – 700 °C.
        T3: Falla termica > 700 °C.
        DT: Mezcla de descarga y falla termica.
        S: Sobrecalentamiento de celulosa / aceite.
    """

    N = "Normal"
    PD = "Descargas parciales"
    D1 = "Descargas de baja energia"
    D2 = "Descargas de alta energia"
    T1 = "Falla termica < 300 °C"
    T2 = "Falla termica 300-700 °C"
    T3 = "Falla termica > 700 °C"
    DT = "Mezcla termica y electrica"
    S = "Sobrecalentamiento"

    def __str__(self) -> str:
        """Representacion legible: 'CODIGO – Descripcion'."""
        return f"{self.name} – {self.value}"
