"""Puertos del dominio: interfaces abstractas para repositorios."""

from src.dga.domain.ports.transformer_repository import TransformerRepository
from src.dga.domain.ports.sample_repository import SampleRepository

__all__ = ["TransformerRepository", "SampleRepository"]
