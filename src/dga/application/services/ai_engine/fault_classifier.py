"""Clasificador de fallas para nuevas lecturas de gases.

Carga un modelo entrenado y clasifica lecturas de gas individuales.
Retorna la falla predicha como ``FaultType`` del dominio.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from sklearn.pipeline import Pipeline
import joblib

from src.dga.domain.models.gas_reading import GasReading
from src.dga.domain.models.fault_type import FaultType
from src.dga.application.services.ai_engine.data_preparation import (
    INDEX_TO_FAULT,
    extract_features,
)


class FaultClassifier:
    """Clasificador que envuelve un pipeline de sklearn.

    Convierte lecturas de gases del dominio a predicciones ``FaultType``,
    opcionalmente con probabilidades por clase.
    """

    def __init__(self, pipeline: Pipeline) -> None:
        """Inicializa con un pipeline ya entrenado.

        Args:
            pipeline: Pipeline de sklearn con scaler + clasificador.
        """
        self._pipeline = pipeline

    @classmethod
    def from_file(cls, path: str | Path) -> "FaultClassifier":
        """Carga un clasificador desde archivo .joblib.

        Args:
            path: Ruta al modelo persistido.

        Returns:
            Instancia de FaultClassifier lista para predecir.

        Raises:
            FileNotFoundError: Si el archivo no existe.
        """
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Modelo no encontrado: {p}")
        pipeline: Pipeline = joblib.load(p)
        return cls(pipeline)

    def classify(self, reading: GasReading) -> FaultType:
        """Clasifica una lectura de gases.

        Args:
            reading: Lectura de 9 gases.

        Returns:
            FaultType predicho por el modelo.
        """
        X = self._prepare_single(reading)
        pred = int(self._pipeline.predict(X)[0])
        return INDEX_TO_FAULT[pred]

    def classify_with_probabilities(
        self, reading: GasReading
    ) -> tuple[FaultType, dict[FaultType, float]]:
        """Clasifica con probabilidades por clase.

        Requiere que el clasificador soporte ``predict_proba``.

        Args:
            reading: Lectura de 9 gases.

        Returns:
            Tupla de (FaultType predicho, diccionario fault_type -> probabilidad).

        Raises:
            AttributeError: Si el clasificador no soporta probabilidades.
        """
        X = self._prepare_single(reading)
        pred = int(self._pipeline.predict(X)[0])
        fault = INDEX_TO_FAULT[pred]

        if not hasattr(self._pipeline, "predict_proba"):
            raise AttributeError(
                "El modelo no soporta predict_proba. "
                "Use classify() en su lugar."
            )

        probas = self._pipeline.predict_proba(X)[0]
        classes = self._pipeline.classes_

        prob_dict: dict[FaultType, float] = {}
        for cls_idx, prob in zip(classes, probas):
            ft = INDEX_TO_FAULT[int(cls_idx)]
            prob_dict[ft] = round(float(prob), 4)

        return fault, prob_dict

    def classify_batch(
        self, readings: list[GasReading]
    ) -> list[FaultType]:
        """Clasifica multiples lecturas de una sola vez.

        Args:
            readings: Lista de lecturas de gases.

        Returns:
            Lista de FaultType predichos.
        """
        if not readings:
            return []

        features = [extract_features(r) for r in readings]
        X = np.array(features, dtype=np.float64)
        preds = self._pipeline.predict(X)
        return [INDEX_TO_FAULT[int(p)] for p in preds]

    @staticmethod
    def _prepare_single(reading: GasReading) -> NDArray[np.float64]:
        """Convierte una lectura a matriz (1, 9) para prediccion."""
        features = extract_features(reading)
        return np.array([features], dtype=np.float64)
