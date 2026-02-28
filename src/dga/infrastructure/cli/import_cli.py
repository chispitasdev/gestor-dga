"""Adaptador CLI para importacion masiva de muestras desde archivos.

Permite al usuario seleccionar un archivo CSV o Excel y un transformador
destino, ejecuta la importacion y muestra el resumen.
"""

from __future__ import annotations

from src.dga.application.services.import_service import ImportService
from src.dga.application.services.transformer_service import TransformerService
from src.dga.domain.exceptions import DGADomainError


class ImportCLI:
    """Interfaz de linea de comandos para importacion de datos.

    Args:
        import_service: Servicio de importacion masiva.
        transformer_service: Servicio de transformadores (para listar equipos).
    """

    MENU = (
        "\n--- Importacion de Datos ---\n"
        "1. Importar muestras desde archivo (CSV/Excel)\n"
        "0. Volver al menu principal\n"
    )

    def __init__(
        self,
        import_service: ImportService,
        transformer_service: TransformerService,
    ) -> None:
        self._import_svc = import_service
        self._transformer_svc = transformer_service

    def run(self) -> None:
        """Ejecuta el bucle del submenu de importacion."""
        while True:
            print(self.MENU)
            choice = input("Seleccione una opcion: ").strip()
            if choice == "0":
                break
            elif choice == "1":
                try:
                    self._import_from_file()
                except (DGADomainError, ValueError, FileNotFoundError) as exc:
                    print(f"\n[Error] {exc}")
                except ImportError as exc:
                    print(f"\n[Error de dependencia] {exc}")
            else:
                print("Opcion no valida. Intente de nuevo.")

    def _import_from_file(self) -> None:
        """Solicita ruta y transformador, ejecuta la importacion."""
        # Listar transformadores
        transformers = self._transformer_svc.list_transformers()
        if not transformers:
            print(
                "\nNo hay transformadores registrados. "
                "Registre al menos uno primero."
            )
            return

        print("\nTransformadores disponibles:")
        print(f"  {'ID':<6} {'Nombre'}")
        print("  " + "-" * 36)
        for t in transformers:
            print(f"  {t.id:<6} {t.name}")

        raw_id = input("\nID del transformador destino: ").strip()
        if not raw_id.isdigit():
            print("El ID debe ser un numero entero positivo.")
            return
        transformer_id = int(raw_id)

        file_path = input("Ruta del archivo (CSV o Excel): ").strip()
        if not file_path:
            print("La ruta no puede estar vacia.")
            return

        # Quitar comillas si las pego
        file_path = file_path.strip('"').strip("'")

        print(f"\nImportando datos desde: {file_path}")
        print(f"Transformador destino: ID {transformer_id}")

        result = self._import_svc.import_from_file(file_path, transformer_id)

        # Mostrar resultado
        print(f"\n{'='*50}")
        print("  RESULTADO DE IMPORTACION")
        print(f"{'='*50}")
        print(f"  Filas leidas   : {result.total_rows}")
        print(f"  Importadas     : {result.imported}")
        print(f"  Omitidas       : {result.skipped}")

        if result.errors:
            print(f"\n  Errores ({len(result.errors)}):")
            for err in result.errors[:20]:   # Mostrar max 20 errores
                print(f"    - {err}")
            if len(result.errors) > 20:
                print(
                    f"    ... y {len(result.errors) - 20} errores mas."
                )
        print(f"{'='*50}")
