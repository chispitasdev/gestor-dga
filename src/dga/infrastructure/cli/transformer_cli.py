"""Adaptador CLI para la gestion de transformadores.

Presenta un submenu interactivo por consola que permite al usuario
realizar operaciones CRUD sobre transformadores de potencia. Delega
toda la logica al servicio de aplicacion ``TransformerService``.
"""

from __future__ import annotations

from src.dga.application.dto.transformer_dto import (
    CreateTransformerDTO,
    UpdateTransformerDTO,
)
from src.dga.application.services.transformer_service import TransformerService
from src.dga.domain.exceptions import DGADomainError


class TransformerCLI:
    """Interfaz de linea de comandos para transformadores.

    Args:
        service: Servicio de aplicacion de transformadores.
    """

    MENU = (
        "\n--- Gestion de Transformadores ---\n"
        "1. Registrar transformador\n"
        "2. Listar transformadores\n"
        "3. Buscar transformador por ID\n"
        "4. Actualizar transformador\n"
        "5. Eliminar transformador\n"
        "0. Volver al menu principal\n"
    )

    def __init__(self, service: TransformerService) -> None:
        self._service = service

    def run(self) -> None:
        """Ejecuta el bucle del submenu de transformadores."""
        actions = {
            "1": self._create,
            "2": self._list_all,
            "3": self._get_by_id,
            "4": self._update,
            "5": self._delete,
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
    # Acciones CRUD
    # ------------------------------------------------------------------

    def _create(self) -> None:
        """Solicita datos y registra un nuevo transformador."""
        name = input("Nombre del transformador: ").strip()
        if not name:
            print("El nombre no puede estar vacio.")
            return
        dto = CreateTransformerDTO(name=name)
        transformer = self._service.register_transformer(dto)
        print(
            f"\nTransformador registrado exitosamente. "
            f"ID: {transformer.id}, Nombre: {transformer.name}"
        )

    def _list_all(self) -> None:
        """Muestra todos los transformadores en formato tabular."""
        transformers = self._service.list_transformers()
        if not transformers:
            print("\nNo hay transformadores registrados.")
            return
        print(f"\n{'ID':<6} {'Nombre'}")
        print("-" * 40)
        for t in transformers:
            print(f"{t.id:<6} {t.name}")
        print(f"\nTotal: {len(transformers)} transformador(es).")

    def _get_by_id(self) -> None:
        """Solicita un ID y muestra el transformador correspondiente."""
        raw_id = input("ID del transformador: ").strip()
        if not raw_id.isdigit():
            print("El ID debe ser un numero entero positivo.")
            return
        transformer = self._service.get_transformer(int(raw_id))
        print(f"\nID: {transformer.id}")
        print(f"Nombre: {transformer.name}")

    def _update(self) -> None:
        """Solicita ID y nuevo nombre para actualizar un transformador."""
        raw_id = input("ID del transformador a actualizar: ").strip()
        if not raw_id.isdigit():
            print("El ID debe ser un numero entero positivo.")
            return
        new_name = input("Nuevo nombre: ").strip()
        if not new_name:
            print("El nombre no puede estar vacio.")
            return
        dto = UpdateTransformerDTO(id=int(raw_id), name=new_name)
        transformer = self._service.update_transformer(dto)
        print(
            f"\nTransformador actualizado. "
            f"ID: {transformer.id}, Nombre: {transformer.name}"
        )

    def _delete(self) -> None:
        """Solicita un ID y elimina el transformador con confirmacion."""
        raw_id = input("ID del transformador a eliminar: ").strip()
        if not raw_id.isdigit():
            print("El ID debe ser un numero entero positivo.")
            return
        confirm = input(
            "Se eliminaran tambien todas las muestras asociadas. "
            "Confirmar (s/n): "
        ).strip().lower()
        if confirm != "s":
            print("Operacion cancelada.")
            return
        self._service.remove_transformer(int(raw_id))
        print("\nTransformador eliminado exitosamente.")
