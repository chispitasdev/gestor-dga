"""Interfaz CLI para el motor de Inteligencia Artificial.

Permite al usuario:
    1. Entrenar modelos de IA con las muestras almacenadas.
    2. Evaluar y comparar los 4 algoritmos.
    3. Clasificar una muestra individual con IA.
    4. Clasificar todas las muestras de un transformador.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.dga.application.services.ai_engine.ai_service import AIService
    from src.dga.application.services.sample_service import SampleService
    from src.dga.application.services.transformer_service import (
        TransformerService,
    )


class AICli:
    """Adaptador CLI para el motor de IA.

    Args:
        ai_service: Servicio orquestador de IA.
        sample_service: Servicio de muestras (para listar/buscar).
        transformer_service: Servicio de transformadores.
    """

    MENU = (
        "\n--- Motor de Inteligencia Artificial ---\n"
        "1. Entrenar modelos\n"
        "2. Evaluar y comparar modelos\n"
        "3. Clasificar muestra por ID\n"
        "4. Clasificar muestras de transformador\n"
        "0. Volver\n"
    )

    def __init__(
        self,
        ai_service: "AIService",
        sample_service: "SampleService",
        transformer_service: "TransformerService",
    ) -> None:
        self._ai = ai_service
        self._samples = sample_service
        self._transformers = transformer_service

    def run(self) -> None:
        """Ejecuta el bucle del submenu de IA."""
        while True:
            print(self.MENU)
            choice = input("Seleccione una opcion: ").strip()
            if choice == "0":
                break
            elif choice == "1":
                self._train()
            elif choice == "2":
                self._evaluate()
            elif choice == "3":
                self._classify_by_id()
            elif choice == "4":
                self._classify_by_transformer()
            else:
                print("Opcion no valida.")

    # ------------------------------------------------------------------ #
    #  Entrenar
    # ------------------------------------------------------------------ #

    def _train(self) -> None:
        """Entrena los 4 modelos con todas las muestras."""
        all_samples = self._samples.list_samples()
        if len(all_samples) < 10:
            print(
                f"\nSe necesitan al menos 10 muestras para entrenar. "
                f"Actualmente hay {len(all_samples)}."
            )
            return

        print(f"\nPreparando {len(all_samples)} muestras...")
        try:
            result = self._ai.train(all_samples, save=True)
        except ValueError as e:
            print(f"\nError de entrenamiento: {e}")
            return

        print(f"\n{'='*55}")
        print("  RESULTADOS DE ENTRENAMIENTO")
        print(f"{'='*55}")
        print(f"  Muestras: {result.n_samples}  |  Clases: {result.n_classes}")
        print(f"{'-'*55}")
        print(f"  {'Modelo':<20} {'Accuracy':>10} {'± Std':>10}")
        print(f"  {'-'*42}")
        for m in result.models:
            marker = " <<" if m.name == result.best_model.name else ""
            print(f"  {m.name:<20} {m.cv_accuracy:>10.2%} {m.cv_std:>10.4f}{marker}")
        print(f"{'-'*55}")
        print(f"  Mejor modelo: {result.best_model.name}")
        print(f"  Guardado en: {self._ai.model_path()}")
        print(f"{'='*55}")

    # ------------------------------------------------------------------ #
    #  Evaluar
    # ------------------------------------------------------------------ #

    def _evaluate(self) -> None:
        """Evalua los 4 modelos con metricas detalladas."""
        all_samples = self._samples.list_samples()
        if len(all_samples) < 10:
            print(f"\nMuestras insuficientes ({len(all_samples)}). Minimo 10.")
            return

        print(f"\nEvaluando 4 modelos con {len(all_samples)} muestras...")

        try:
            from src.dga.application.services.ai_engine.model_evaluator import (
                ModelEvaluator,
            )

            results = self._ai.evaluate_all(all_samples)
        except ValueError as e:
            print(f"\nError de evaluacion: {e}")
            return

        for r in results:
            print(ModelEvaluator.format_report(r))

    # ------------------------------------------------------------------ #
    #  Clasificar por ID
    # ------------------------------------------------------------------ #

    def _classify_by_id(self) -> None:
        """Clasifica una muestra individual por su ID."""
        if not self._ai.has_model():
            print("\nNo hay modelo entrenado. Entrene primero (opcion 1).")
            return

        try:
            sid = int(input("ID de la muestra: ").strip())
        except ValueError:
            print("ID invalido.")
            return

        try:
            sample = self._samples.get_sample(sid)
        except Exception:
            print(f"Muestra con ID {sid} no encontrada.")
            return

        fault = self._ai.classify(sample.gas_reading)
        print(f"\n  Muestra  : {sample.sample_code} (ID {sample.id})")
        print(f"  Prediccion IA: {fault}")

        # Intentar mostrar probabilidades
        try:
            _, probs = self._ai.classify_with_proba(sample.gas_reading)
            print(f"\n  {'Clase':<25} {'Probabilidad':>12}")
            print(f"  {'-'*38}")
            for ft, p in sorted(probs.items(), key=lambda x: x[1], reverse=True):
                if p > 0.01:
                    print(f"  {ft!s:<25} {p:>12.2%}")
        except (AttributeError, RuntimeError):
            pass

    # ------------------------------------------------------------------ #
    #  Clasificar por transformador
    # ------------------------------------------------------------------ #

    def _classify_by_transformer(self) -> None:
        """Clasifica todas las muestras de un transformador."""
        if not self._ai.has_model():
            print("\nNo hay modelo entrenado. Entrene primero (opcion 1).")
            return

        # Listar transformadores
        transformers = self._transformers.list_transformers()
        if not transformers:
            print("\nNo hay transformadores registrados.")
            return

        print("\nTransformadores disponibles:")
        for t in transformers:
            print(f"  [{t.id}] {t.name}")

        try:
            tid = int(input("ID del transformador: ").strip())
        except ValueError:
            print("ID invalido.")
            return

        try:
            samples = self._samples.list_samples_by_transformer(tid)
        except Exception:
            print(f"Transformador ID {tid} no encontrado.")
            return
        if not samples:
            print(f"No hay muestras para el transformador ID {tid}.")
            return

        readings = [s.gas_reading for s in samples]
        faults = self._ai.classify_batch(readings)

        print(f"\n  {'Muestra':<15} {'Fecha':>12} {'Prediccion IA':<30}")
        print(f"  {'-'*58}")
        for s, f in zip(samples, faults):
            print(f"  {s.sample_code:<15} {s.extraction_date!s:>12} {f!s:<30}")
