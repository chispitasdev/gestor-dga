"""Preparacion de datos para el motor de IA.

Convierte muestras del dominio en matrices numericas (features + labels)
aptas para scikit-learn. Las etiquetas se generan automaticamente
mediante el consenso de los 6 metodos normativos, ya que los datos
historicos de ENDE no incluyen diagnosticos manuales.

Pipeline:
    1. Recibe lista de Sample del dominio.
    2. Extrae los 9 gases como features.
    3. Ejecuta los 6 metodos normativos sobre cada lectura.
    4. Asigna la etiqueta por voto mayoritario (consenso).
    5. Retorna arrays X (features) e y (labels) listos para entrenar.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from src.dga.domain.models.fault_type import FaultType
from src.dga.domain.models.gas_reading import GasReading
from src.dga.domain.models.sample import Sample
from src.dga.application.services.normative_diagnosis_service import (
    NormativeDiagnosisService,
)


# Mapeo FaultType.name -> indice numerico (para sklearn)
FAULT_LABELS: list[str] = [ft.name for ft in FaultType]
FAULT_TO_INDEX: dict[str, int] = {name: i for i, name in enumerate(FAULT_LABELS)}
INDEX_TO_FAULT: dict[int, FaultType] = {i: ft for i, ft in enumerate(FaultType)}

# Nombres de features en orden canonico
FEATURE_NAMES: list[str] = list(GasReading.field_names())


@dataclass(frozen=True, slots=True)
class PreparedDataset:
    """Dataset preparado para entrenamiento o prediccion.

    Attributes:
        X: Matriz de features (n_samples, 9). Cada columna es un gas.
        y: Vector de etiquetas numericas (n_samples,).
        fault_labels: Etiquetas textuales correspondientes a y.
        feature_names: Nombres de las columnas de X.
        sample_ids: IDs de las muestras originales (para trazabilidad).
    """

    X: NDArray[np.float64]
    y: NDArray[np.int64]
    fault_labels: list[str]
    feature_names: list[str]
    sample_ids: list[int | None]


def extract_features(reading: GasReading) -> list[float]:
    """Extrae los 9 valores de gas como vector de features.

    Args:
        reading: Lectura de gases.

    Returns:
        Lista de 9 floats en orden canonico.
    """
    return [getattr(reading, name) for name in FEATURE_NAMES]


def auto_label(
    reading: GasReading,
    diagnosis_service: NormativeDiagnosisService,
) -> str:
    """Genera la etiqueta de falla por consenso normativo.

    Ejecuta los 6 metodos normativos y retorna el nombre del
    FaultType mas votado.

    Args:
        reading: Lectura de gases.
        diagnosis_service: Servicio de diagnostico normativo.

    Returns:
        Nombre del FaultType ganador (ej. 'T2', 'D1', 'N').
    """
    result = diagnosis_service.diagnose_all(reading)
    return result.consensus_fault.name


def prepare_dataset(
    samples: list[Sample],
    diagnosis_service: NormativeDiagnosisService | None = None,
) -> PreparedDataset:
    """Convierte una lista de muestras en un dataset numerico.

    Si se proporciona diagnosis_service, genera etiquetas por consenso.
    Si no, asigna etiqueta 'N' (normal) a todas — util para prediccion.

    Args:
        samples: Lista de muestras del dominio.
        diagnosis_service: Servicio normativo (None para solo features).

    Returns:
        PreparedDataset con X, y, y metadatos.
    """
    if not samples:
        return PreparedDataset(
            X=np.empty((0, len(FEATURE_NAMES)), dtype=np.float64),
            y=np.empty(0, dtype=np.int64),
            fault_labels=[],
            feature_names=FEATURE_NAMES,
            sample_ids=[],
        )

    features: list[list[float]] = []
    labels: list[str] = []
    ids: list[int | None] = []

    for sample in samples:
        features.append(extract_features(sample.gas_reading))
        ids.append(sample.id)

        if diagnosis_service is not None:
            label = auto_label(sample.gas_reading, diagnosis_service)
        else:
            label = FaultType.N.name
        labels.append(label)

    X = np.array(features, dtype=np.float64)
    y = np.array([FAULT_TO_INDEX[lbl] for lbl in labels], dtype=np.int64)

    return PreparedDataset(
        X=X,
        y=y,
        fault_labels=labels,
        feature_names=FEATURE_NAMES,
        sample_ids=ids,
    )
