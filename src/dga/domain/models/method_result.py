"""Value Object que encapsula el resultado de un metodo de diagnostico normativo.

Cada instancia contiene el tipo de falla identificado, el nombre del metodo
que lo produjo y un diccionario opcional con datos intermedios del analisis
(relaciones de gas, coordenadas, etc.) para trazabilidad.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.dga.domain.models.fault_type import FaultType


@dataclass(frozen=True, slots=True)
class MethodResult:
    """Resultado inmutable de un diagnostico normativo.

    Attributes:
        method_name: Nombre estandarizado del metodo diagnostico.
        fault_type: Tipo de falla detectada.
        description: Descripcion textual del diagnostico.
        details: Datos intermedios del calculo (relaciones, coordenadas, etc.).
    """

    method_name: str
    fault_type: FaultType
    description: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return f"[{self.method_name}] {self.fault_type.name}: {self.description}"
