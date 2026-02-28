"""Data Transfer Objects para la entidad Transformer.

Los DTOs desacoplan los datos de entrada del usuario de las entidades
de dominio, asegurando que cambios en la interfaz no afecten al dominio
(Principio Abierto/Cerrado).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CreateTransformerDTO:
    """Datos necesarios para registrar un nuevo transformador.

    Attributes:
        name: Nombre o designacion del transformador.
    """

    name: str


@dataclass(frozen=True, slots=True)
class UpdateTransformerDTO:
    """Datos necesarios para actualizar un transformador existente.

    Attributes:
        id: Identificador del transformador a actualizar.
        name: Nuevo nombre del transformador.
    """

    id: int
    name: str
