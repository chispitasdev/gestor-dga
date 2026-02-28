"""Modelos de dominio: entidades y value objects."""

from src.dga.domain.models.gas_reading import GasReading
from src.dga.domain.models.transformer import Transformer
from src.dga.domain.models.sample import Sample
from src.dga.domain.models.fault_type import FaultType
from src.dga.domain.models.method_result import MethodResult

__all__ = ["GasReading", "Transformer", "Sample", "FaultType", "MethodResult"]
