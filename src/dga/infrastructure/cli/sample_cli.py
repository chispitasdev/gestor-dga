"""Adaptador CLI para la gestion de muestras DGA.

Presenta un submenu interactivo por consola que permite al usuario
realizar operaciones CRUD sobre muestras de aceite y sus lecturas de
gases disueltos. Delega toda la logica al servicio ``SampleService``.
"""

from __future__ import annotations

from datetime import date, datetime

from src.dga.application.dto.sample_dto import CreateSampleDTO, UpdateSampleDTO
from src.dga.application.services.sample_service import SampleService
from src.dga.application.services.transformer_service import TransformerService
from src.dga.domain.exceptions import DGADomainError
from src.dga.domain.models.gas_reading import GasReading
from src.dga.domain.models.sample import Sample


# Formato de fecha esperado en la entrada del usuario.
_DATE_FORMAT = "%d/%m/%Y"


class SampleCLI:
    """Interfaz de linea de comandos para muestras de aceite.

    Args:
        sample_service: Servicio de aplicacion de muestras.
        transformer_service: Servicio de transformadores (para listar equipos).
    """

    MENU = (
        "\n--- Gestion de Muestras DGA ---\n"
        "1. Registrar muestra\n"
        "2. Listar todas las muestras\n"
        "3. Buscar muestra por ID\n"
        "4. Filtrar muestras por transformador\n"
        "5. Actualizar muestra\n"
        "6. Eliminar muestra\n"
        "0. Volver al menu principal\n"
    )

    def __init__(
        self,
        sample_service: SampleService,
        transformer_service: TransformerService,
    ) -> None:
        self._sample_svc = sample_service
        self._transformer_svc = transformer_service

    def run(self) -> None:
        """Ejecuta el bucle del submenu de muestras."""
        actions = {
            "1": self._create,
            "2": self._list_all,
            "3": self._get_by_id,
            "4": self._filter_by_transformer,
            "5": self._update,
            "6": self._delete,
        }
        while True:
            print(self.MENU)
            choice = input("Seleccione una opcion: ").strip()
            if choice == "0":
                break
            action = actions.get(choice)
            if action is None:
                print("Opcion no valida. Intente de nuevo.")
                continue
            try:
                action()
            except DGADomainError as exc:
                print(f"\n[Error] {exc}")
            except ValueError as exc:
                print(f"\n[Error de validacion] {exc}")

    # ------------------------------------------------------------------
    # Utilidades de entrada
    # ------------------------------------------------------------------

    @staticmethod
    def _read_date(prompt: str) -> date:
        """Solicita una fecha al usuario en formato DD/MM/YYYY.

        Args:
            prompt: Texto a mostrar al usuario.

        Returns:
            Objeto ``date`` parseado.

        Raises:
            ValueError: Si el formato es incorrecto.
        """
        raw = input(prompt).strip()
        try:
            return datetime.strptime(raw, _DATE_FORMAT).date()
        except ValueError:
            raise ValueError(
                f"Formato de fecha invalido: '{raw}'. Use DD/MM/YYYY."
            )

    @staticmethod
    def _read_float(prompt: str) -> float:
        """Solicita un valor numerico (ppm) al usuario.

        Args:
            prompt: Texto a mostrar.

        Returns:
            Valor flotante.

        Raises:
            ValueError: Si no es numerico.
        """
        raw = input(prompt).strip()
        try:
            return float(raw)
        except ValueError:
            raise ValueError(
                f"Valor numerico invalido: '{raw}'."
            )

    def _read_gas_values(self) -> dict[str, float]:
        """Solicita las 9 concentraciones de gas al usuario.

        Presenta cada gas con su nombre descriptivo y espera un valor
        en ppm.

        Returns:
            Diccionario con los 9 valores de gas.
        """
        labels = GasReading.descriptive_labels()
        values: dict[str, float] = {}
        print("\nIngrese las concentraciones de gases (en ppm):")
        for field_name in GasReading.field_names():
            label = labels[field_name]
            values[field_name] = self._read_float(f"  {label}: ")
        return values

    def _select_transformer_id(self) -> int:
        """Lista los transformadores y solicita seleccionar uno.

        Returns:
            ID del transformador seleccionado.

        Raises:
            ValueError: Si no hay transformadores o la seleccion es invalida.
        """
        transformers = self._transformer_svc.list_transformers()
        if not transformers:
            raise ValueError(
                "No hay transformadores registrados. "
                "Registre al menos uno primero."
            )
        print("\nTransformadores disponibles:")
        print(f"  {'ID':<6} {'Nombre'}")
        print("  " + "-" * 36)
        for t in transformers:
            print(f"  {t.id:<6} {t.name}")
        raw_id = input("\nID del transformador: ").strip()
        if not raw_id.isdigit():
            raise ValueError("El ID debe ser un numero entero positivo.")
        return int(raw_id)

    # ------------------------------------------------------------------
    # Presentacion
    # ------------------------------------------------------------------

    @staticmethod
    def _display_sample(sample: Sample) -> None:
        """Muestra los detalles de una muestra en consola.

        Args:
            sample: Entidad a mostrar.
        """
        labels = GasReading.descriptive_labels()
        print(f"\n{'='*50}")
        print(f"  ID Muestra       : {sample.id}")
        print(f"  Codigo Muestra   : {sample.sample_code}")
        print(f"  ID Transformador : {sample.transformer_id}")
        print(f"  Fecha Extraccion : {sample.extraction_date.strftime(_DATE_FORMAT)}")
        print(f"  Fecha Diagnostico: {sample.diagnosis_date.strftime(_DATE_FORMAT)}")
        print(f"  {'--- Gases Disueltos (ppm) ---':^46}")
        for field_name in GasReading.field_names():
            label = labels[field_name]
            value = getattr(sample.gas_reading, field_name)
            print(f"  {label:<30}: {value:>10.2f}")
        print(f"{'='*50}")

    def _display_samples_table(self, samples: list[Sample]) -> None:
        """Muestra una tabla resumida de muestras.

        Args:
            samples: Lista de muestras a mostrar.
        """
        if not samples:
            print("\nNo se encontraron muestras.")
            return

        header = (
            f"{'ID':<5} {'Codigo':<15} {'Trafo ID':<10} "
            f"{'F. Extraccion':<15} {'F. Diagnostico':<15}"
        )
        print(f"\n{header}")
        print("-" * len(header))
        for s in samples:
            print(
                f"{s.id:<5} {s.sample_code:<15} {s.transformer_id:<10} "
                f"{s.extraction_date.strftime(_DATE_FORMAT):<15} "
                f"{s.diagnosis_date.strftime(_DATE_FORMAT):<15}"
            )
        print(f"\nTotal: {len(samples)} muestra(s).")

    # ------------------------------------------------------------------
    # Acciones CRUD
    # ------------------------------------------------------------------

    def _create(self) -> None:
        """Solicita datos y registra una nueva muestra."""
        sample_code = input("Codigo de la muestra: ").strip()
        if not sample_code:
            print("El codigo de muestra no puede estar vacio.")
            return

        transformer_id = self._select_transformer_id()
        extraction_date = self._read_date("Fecha de extraccion (DD/MM/YYYY): ")
        gas_values = self._read_gas_values()

        dto = CreateSampleDTO(
            sample_code=sample_code,
            transformer_id=transformer_id,
            extraction_date=extraction_date,
            **gas_values,
        )
        sample = self._sample_svc.register_sample(dto)
        print(
            f"\nMuestra registrada exitosamente. ID: {sample.id}"
        )
        print(
            f"Fecha de diagnostico asignada: "
            f"{sample.diagnosis_date.strftime(_DATE_FORMAT)}"
        )

    def _list_all(self) -> None:
        """Lista todas las muestras registradas."""
        samples = self._sample_svc.list_samples()
        self._display_samples_table(samples)

    def _get_by_id(self) -> None:
        """Busca y muestra una muestra por su ID."""
        raw_id = input("ID de la muestra: ").strip()
        if not raw_id.isdigit():
            print("El ID debe ser un numero entero positivo.")
            return
        sample = self._sample_svc.get_sample(int(raw_id))
        self._display_sample(sample)

    def _filter_by_transformer(self) -> None:
        """Filtra y muestra las muestras de un transformador especifico."""
        transformer_id = self._select_transformer_id()
        samples = self._sample_svc.list_samples_by_transformer(transformer_id)
        self._display_samples_table(samples)

    def _update(self) -> None:
        """Solicita datos actualizados y modifica una muestra existente."""
        raw_id = input("ID de la muestra a actualizar: ").strip()
        if not raw_id.isdigit():
            print("El ID debe ser un numero entero positivo.")
            return

        sample_id = int(raw_id)
        current = self._sample_svc.get_sample(sample_id)
        self._display_sample(current)

        print("\nIngrese los nuevos datos (deje vacio para conservar el actual):")

        # Codigo de muestra
        new_code = input(
            f"Codigo de muestra [{current.sample_code}]: "
        ).strip()
        sample_code = new_code if new_code else current.sample_code

        # Transformador
        change_trafo = input(
            f"Cambiar transformador (actual: {current.transformer_id})? (s/n): "
        ).strip().lower()
        if change_trafo == "s":
            transformer_id = self._select_transformer_id()
        else:
            transformer_id = current.transformer_id

        # Fecha de extraccion
        new_date_str = input(
            f"Fecha de extraccion [{current.extraction_date.strftime(_DATE_FORMAT)}] "
            f"(DD/MM/YYYY): "
        ).strip()
        if new_date_str:
            extraction_date = datetime.strptime(
                new_date_str, _DATE_FORMAT
            ).date()
        else:
            extraction_date = current.extraction_date

        # Fecha de diagnostico
        new_diag_str = input(
            f"Fecha de diagnostico [{current.diagnosis_date.strftime(_DATE_FORMAT)}] "
            f"(DD/MM/YYYY, vacio = mantener): "
        ).strip()
        if new_diag_str:
            diagnosis_date = datetime.strptime(
                new_diag_str, _DATE_FORMAT
            ).date()
        else:
            diagnosis_date = current.diagnosis_date

        # Gases
        update_gases = input(
            "Actualizar concentraciones de gases? (s/n): "
        ).strip().lower()
        if update_gases == "s":
            gas_values = self._read_gas_values()
        else:
            gas_values = current.gas_reading.as_dict()

        dto = UpdateSampleDTO(
            id=sample_id,
            sample_code=sample_code,
            transformer_id=transformer_id,
            extraction_date=extraction_date,
            diagnosis_date=diagnosis_date,
            **gas_values,
        )
        updated = self._sample_svc.update_sample(dto)
        print("\nMuestra actualizada exitosamente.")
        self._display_sample(updated)

    def _delete(self) -> None:
        """Solicita un ID y elimina la muestra con confirmacion."""
        raw_id = input("ID de la muestra a eliminar: ").strip()
        if not raw_id.isdigit():
            print("El ID debe ser un numero entero positivo.")
            return
        confirm = input("Confirmar eliminacion (s/n): ").strip().lower()
        if confirm != "s":
            print("Operacion cancelada.")
            return
        self._sample_svc.remove_sample(int(raw_id))
        print("\nMuestra eliminada exitosamente.")
