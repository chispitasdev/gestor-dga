# Guia Paso a Paso: Como Construir un CRUD con Arquitectura Hexagonal

Manual practico para construir un sistema CRUD profesional desde cero.
Incluye el orden exacto de directorios, el primer archivo que debes crear,
y la plantilla completa que puedes reutilizar en cualquier proyecto.

---

## Indice

1. [Antes de escribir codigo: planificar en papel](#1-antes-de-escribir-codigo-planificar-en-papel)
2. [Estructura de directorios (orden de creacion)](#2-estructura-de-directorios-orden-de-creacion)
3. [Orden exacto de archivos a crear](#3-orden-exacto-de-archivos-a-crear)
4. [Paso 1: Excepciones de dominio](#paso-1-excepciones-de-dominio)
5. [Paso 2: Modelos (entidades y value objects)](#paso-2-modelos-entidades-y-value-objects)
6. [Paso 3: Puertos (interfaces abstractas)](#paso-3-puertos-interfaces-abstractas)
7. [Paso 4: DTOs (paquetes de datos)](#paso-4-dtos-paquetes-de-datos)
8. [Paso 5: Servicios (logica de negocio)](#paso-5-servicios-logica-de-negocio)
9. [Paso 6: Conexion a la base de datos](#paso-6-conexion-a-la-base-de-datos)
10. [Paso 7: Repositorios concretos (SQLite)](#paso-7-repositorios-concretos-sqlite)
11. [Paso 8: CLI (interfaz de consola)](#paso-8-cli-interfaz-de-consola)
12. [Paso 9: main.py (conectar todo)](#paso-9-mainpy-conectar-todo)
13. [Paso 10: Tests](#paso-10-tests)
14. [Checklist final](#checklist-final)
15. [Plantilla reutilizable para entidades nuevas](#plantilla-reutilizable-para-entidades-nuevas)
16. [Reglas de oro de la arquitectura hexagonal](#reglas-de-oro-de-la-arquitectura-hexagonal)

---

## 1. Antes de escribir codigo: planificar en papel

Antes de abrir el editor, responde estas preguntas en un papel o bloc de notas:

### Pregunta 1: Que datos manejo?

Escribe cada entidad como si fuera un formulario:

```
Ejemplo: Sistema de Biblioteca

Libro:
  - id (automatico)
  - titulo (texto, obligatorio)
  - autor (texto, obligatorio)
  - isbn (texto, unico)
  - disponible (si/no)

Prestamo:
  - id (automatico)
  - id_libro (a cual libro pertenece)
  - nombre_persona (texto)
  - fecha_prestamo (fecha)
  - fecha_devolucion (fecha, puede estar vacia)
```

### Pregunta 2: Que operaciones necesita cada entidad?

```
Con un Libro puedo:
  - Crear uno nuevo
  - Ver todos
  - Buscar por ID
  - Actualizar datos
  - Eliminar

Con un Prestamo puedo:
  - Registrar un prestamo
  - Ver prestamos de un libro
  - Marcar como devuelto
  - Ver todos los prestamos activos
```

### Pregunta 3: Que validaciones hacen falta?

```
Libro:
  - El titulo no puede estar vacio
  - El ISBN no puede repetirse
  - El ISBN debe tener 13 caracteres

Prestamo:
  - El libro debe existir
  - El libro debe estar disponible
  - El nombre no puede estar vacio
```

### Pregunta 4: Que errores pueden pasar?

```
  - Libro no encontrado
  - Prestamo no encontrado
  - ISBN duplicado
  - Libro no disponible para prestamo
```

**Con estas 4 respuestas ya sabes todo lo que necesitas para empezar a codificar.**

---

## 2. Estructura de directorios (orden de creacion)

Crea los directorios en este orden exacto. Cada uno lleva un archivo
`__init__.py` vacio (para que Python reconozca la carpeta como paquete).

```
mi_proyecto/                    <-- Carpeta raiz del proyecto
|
|-- main.py                     <-- Se crea AL FINAL (Paso 9)
|-- requirements.txt            <-- Dependencias (ej: pytest>=7.0)
|
|-- src/                        <-- Todo el codigo fuente
|   |-- __init__.py
|   |-- mi_app/                 <-- Nombre de tu aplicacion
|       |-- __init__.py
|       |
|       |-- domain/             <-- CAPA 1: se crea PRIMERO
|       |   |-- __init__.py
|       |   |-- exceptions.py   <-- Archivo 1
|       |   |-- models/
|       |   |   |-- __init__.py
|       |   |   |-- libro.py    <-- Archivo 2 (tus entidades)
|       |   |-- ports/
|       |       |-- __init__.py
|       |       |-- libro_repository.py  <-- Archivo 3
|       |
|       |-- application/        <-- CAPA 2: se crea SEGUNDO
|       |   |-- __init__.py
|       |   |-- dto/
|       |   |   |-- __init__.py
|       |   |   |-- libro_dto.py         <-- Archivo 4
|       |   |-- services/
|       |       |-- __init__.py
|       |       |-- libro_service.py     <-- Archivo 5
|       |
|       |-- infrastructure/     <-- CAPA 3: se crea TERCERO
|           |-- __init__.py
|           |-- persistence/
|           |   |-- __init__.py
|           |   |-- sqlite_connection.py          <-- Archivo 6
|           |   |-- sqlite_libro_repository.py    <-- Archivo 7
|           |-- cli/
|               |-- __init__.py
|               |-- main_menu.py                  <-- Archivo 8
|               |-- libro_cli.py                  <-- Archivo 9
|
|-- tests/                      <-- Se crean AL FINAL (Paso 10)
    |-- __init__.py
    |-- unit/
    |   |-- __init__.py
    |   |-- domain/
    |   |   |-- __init__.py
    |   |   |-- test_models.py
    |   |-- application/
    |       |-- __init__.py
    |       |-- test_libro_service.py
    |-- integration/
        |-- __init__.py
        |-- test_sqlite_repositories.py
```

### Por que este orden?

```
PRIMERO: domain/     --> No depende de nadie. Es el nucleo.
SEGUNDO: application/ --> Solo depende de domain.
TERCERO: infrastructure/ --> Depende de domain y application.
ULTIMO:  main.py     --> Conecta todo. Depende de las 3 capas.
```

Siempre de adentro hacia afuera. Nunca al reves.

---

## 3. Orden exacto de archivos a crear

| Orden | Archivo                          | Capa           | Que defines ahi                          |
|-------|----------------------------------|----------------|------------------------------------------|
| 1     | `exceptions.py`                  | domain         | Todos los errores posibles del negocio    |
| 2     | `libro.py` (modelo)              | domain/models  | Que ES una entidad, sus campos, validacion|
| 3     | `libro_repository.py` (puerto)   | domain/ports   | Que operaciones de guardado DEBEN existir |
| 4     | `libro_dto.py`                   | application/dto| Que datos viajan del CLI al servicio      |
| 5     | `libro_service.py`               | application    | Que se puede HACER (logica CRUD)          |
| 6     | `sqlite_connection.py`           | infrastructure | Como conectar a la BD y crear tablas      |
| 7     | `sqlite_libro_repository.py`     | infrastructure | Como ejecutar SQL real                    |
| 8     | `main_menu.py`                   | infrastructure | El menu principal de consola              |
| 9     | `libro_cli.py`                   | infrastructure | Pedir datos y mostrar resultados          |
| 10    | `main.py`                        | raiz           | Conectar todas las piezas                 |
| 11    | `test_*.py`                      | tests          | Verificar que todo funciona               |

**Regla: nunca avances al siguiente archivo si el anterior no esta terminado.**

---

## Paso 1: Excepciones de dominio

Es el PRIMER archivo porque todos los demas lo van a necesitar.

### Que pensar

"Que errores especificos del negocio pueden pasar?"

Para cada error, crea una clase que herede de una clase base comun.

### Plantilla

```python
"""Excepciones de dominio del sistema."""


class AppDomainError(Exception):
    """Clase base para todas las excepciones de dominio."""


class LibroNotFoundError(AppDomainError):
    """El libro solicitado no existe."""

    def __init__(self, libro_id: int) -> None:
        self.libro_id = libro_id
        super().__init__(f"No se encontro el libro con ID {libro_id}.")


class DuplicateISBNError(AppDomainError):
    """Ya existe un libro con ese ISBN."""

    def __init__(self, isbn: str) -> None:
        self.isbn = isbn
        super().__init__(f"Ya existe un libro con ISBN '{isbn}'.")
```

### Patron a seguir

```
1. Una clase base (hereda de Exception)
2. Una clase por cada error especifico (hereda de la base)
3. Cada clase recibe el dato relevante y arma un mensaje claro
```

### Por que una clase base comun?

Porque en el CLI podes atrapar TODOS los errores de dominio con un solo except:

```python
try:
    action()
except AppDomainError as exc:    # Atrapa CUALQUIER error de dominio
    print(f"Error: {exc}")
```

---

## Paso 2: Modelos (entidades y value objects)

### Que pensar

"Que ES esta cosa? Que campos tiene? Que reglas debe cumplir al nacer?"

### Plantilla para una entidad

```python
"""Entidad que representa un libro."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class Libro:
    """Entidad con identidad propia (tiene ID).

    Attributes:
        titulo: Titulo del libro.
        autor: Nombre del autor.
        isbn: Codigo ISBN unico de 13 caracteres.
        disponible: Si esta disponible para prestamo.
        id: Identificador unico (None si aun no se guardo).
    """

    titulo: str
    autor: str
    isbn: str
    disponible: bool = True
    id: Optional[int] = None

    def __post_init__(self) -> None:
        """Valida las reglas de negocio al crear el objeto."""
        self.titulo = self.titulo.strip()
        self.autor = self.autor.strip()
        self.isbn = self.isbn.strip()

        if not self.titulo:
            raise ValueError("El titulo no puede estar vacio.")
        if not self.autor:
            raise ValueError("El autor no puede estar vacio.")
        if len(self.isbn) != 13:
            raise ValueError("El ISBN debe tener 13 caracteres.")
```

### Plantilla para un value object (dato sin identidad)

```python
"""Value Object que representa una direccion."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)    # frozen=True: inmutable, no se puede cambiar
class Direccion:
    calle: str
    ciudad: str
    codigo_postal: str

    def __post_init__(self) -> None:
        # Validaciones aca...
```

### Diferencia entre entidad y value object

| Caracteristica    | Entidad                  | Value Object              |
|-------------------|--------------------------|---------------------------|
| Tiene ID?         | Si                       | No                        |
| Se puede cambiar? | Si (`@dataclass`)        | No (`frozen=True`)        |
| Dos iguales son?  | Diferentes (distinto ID) | El mismo (mismos valores) |
| Ejemplo           | Libro, Transformador     | GasReading, Direccion     |

### Regla clave

**Toda validacion de negocio va en `__post_init__`.** Asi el objeto se valida
a si mismo al nacer. No puede existir un objeto invalido.

---

## Paso 3: Puertos (interfaces abstractas)

### Que pensar

"Que operaciones de guardado/lectura necesito, SIN pensar en SQL ni en la BD?"

### Plantilla

```python
"""Puerto abstracto del repositorio de libros."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from src.mi_app.domain.models.libro import Libro


class LibroRepository(ABC):
    """Contrato que cualquier base de datos debe cumplir."""

    @abstractmethod
    def create(self, libro: Libro) -> Libro:
        """Guarda un libro nuevo. Devuelve el libro con ID asignado."""

    @abstractmethod
    def get_by_id(self, libro_id: int) -> Optional[Libro]:
        """Busca un libro por ID. Devuelve None si no existe."""

    @abstractmethod
    def get_all(self) -> list[Libro]:
        """Devuelve todos los libros."""

    @abstractmethod
    def update(self, libro: Libro) -> Libro:
        """Actualiza un libro existente. Devuelve el libro actualizado."""

    @abstractmethod
    def delete(self, libro_id: int) -> None:
        """Elimina un libro por ID."""
```

### Las 5 operaciones minimas de cualquier CRUD

Siempre son las mismas:

| Operacion  | Metodo del puerto   | SQL equivalente  |
|------------|---------------------|------------------|
| Create     | `create(entidad)`   | INSERT INTO      |
| Read (uno) | `get_by_id(id)`     | SELECT WHERE id  |
| Read (all) | `get_all()`         | SELECT *         |
| Update     | `update(entidad)`   | UPDATE WHERE id  |
| Delete     | `delete(id)`        | DELETE WHERE id  |

Si ademas necesitas buscar por otro campo (ej: por nombre),
agregas un metodo mas: `get_by_name(name)`.

### Por que usar ABC (clase abstracta)?

Porque te OBLIGA a implementar todos los metodos. Si creas
un SQLiteLibroRepository y te olvidas de implementar `delete`,
Python te lanza error al ejecutar. No hay forma de que se te pase.

---

## Paso 4: DTOs (paquetes de datos)

### Que pensar

"Que datos necesita cada operacion? Solo esos, nada mas."

### Plantilla

```python
"""DTOs para la entidad Libro."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CreateLibroDTO:
    """Datos para crear un libro nuevo.
    NO tiene 'id' porque todavia no existe.
    NO tiene 'disponible' porque siempre empieza en True.
    """
    titulo: str
    autor: str
    isbn: str


@dataclass(frozen=True, slots=True)
class UpdateLibroDTO:
    """Datos para actualizar un libro.
    SI tiene 'id' porque necesitas saber cual actualizar.
    """
    id: int
    titulo: str
    autor: str
    isbn: str
```

### Regla para decidir que campos lleva cada DTO

| Campo       | En CreateDTO? | En UpdateDTO? | Por que?                          |
|-------------|---------------|---------------|-----------------------------------|
| id          | NO            | SI            | Al crear no existe, al editar si  |
| titulo      | SI            | SI            | Se necesita en ambos              |
| autor       | SI            | SI            | Se necesita en ambos              |
| isbn        | SI            | SI            | Se necesita en ambos              |
| disponible  | NO            | OPCIONAL      | Al crear siempre es True          |
| created_at  | NO            | NO            | Lo genera la BD automaticamente   |

### Por que usar DTOs y no pasar los datos sueltos?

Porque si manana la entidad necesita un campo mas, lo agregas al DTO
y todos los metodos que usan ese DTO automaticamente reciben el campo.
Si pasaras datos sueltos, tendrias que agregar un parametro en 10 lugares.

---

## Paso 5: Servicios (logica de negocio)

### Que pensar

"Para cada operacion CRUD, que pasos debo seguir?
Validar, actuar, responder. Siempre en ese orden."

### Plantilla

```python
"""Servicio de aplicacion para la gestion de libros."""

from __future__ import annotations

from src.mi_app.application.dto.libro_dto import CreateLibroDTO, UpdateLibroDTO
from src.mi_app.domain.exceptions import LibroNotFoundError
from src.mi_app.domain.models.libro import Libro
from src.mi_app.domain.ports.libro_repository import LibroRepository


class LibroService:
    """Orquesta las operaciones CRUD de libros."""

    def __init__(self, repository: LibroRepository) -> None:
        self._repository = repository

    # -- CREATE --
    def register_libro(self, dto: CreateLibroDTO) -> Libro:
        libro = Libro(titulo=dto.titulo, autor=dto.autor, isbn=dto.isbn)
        return self._repository.create(libro)

    # -- READ (todos) --
    def list_libros(self) -> list[Libro]:
        return self._repository.get_all()

    # -- READ (uno) --
    def get_libro(self, libro_id: int) -> Libro:
        libro = self._repository.get_by_id(libro_id)
        if libro is None:
            raise LibroNotFoundError(libro_id)
        return libro

    # -- UPDATE --
    def update_libro(self, dto: UpdateLibroDTO) -> Libro:
        libro = Libro(id=dto.id, titulo=dto.titulo, autor=dto.autor, isbn=dto.isbn)
        return self._repository.update(libro)

    # -- DELETE --
    def remove_libro(self, libro_id: int) -> None:
        self._repository.delete(libro_id)
```

### El patron de cada metodo (siempre igual)

```
CREATE:   Abrir DTO --> Crear entidad --> repository.create()
READ:     repository.get_by_id() --> Si None, lanzar error --> Devolver
LIST:     repository.get_all() --> Devolver lista
UPDATE:   Abrir DTO --> Crear entidad con ID --> repository.update()
DELETE:   repository.delete(id)
```

### Regla clave

El servicio **NUNCA** sabe de SQL, ni de SQLite, ni de la base de datos.
Solo conoce al repositorio a traves de la interfaz abstracta (puerto).
Recibe el repositorio por parametro en el constructor.

---

## Paso 6: Conexion a la base de datos

### Que pensar

"Necesito una funcion que me de la conexion y otra que cree las tablas."

### Plantilla

```python
"""Gestion de la conexion SQLite y esquema de base de datos."""

from __future__ import annotations

import sqlite3
from pathlib import Path

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS libros (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo      TEXT    NOT NULL,
    autor       TEXT    NOT NULL,
    isbn        TEXT    NOT NULL UNIQUE,
    disponible  INTEGER NOT NULL DEFAULT 1
);
"""


def get_connection(db_path: str | Path = "app.db") -> sqlite3.Connection:
    """Crea y retorna una conexion SQLite."""
    connection = sqlite3.connect(str(db_path))
    connection.execute("PRAGMA foreign_keys = ON;")
    connection.row_factory = sqlite3.Row       # Para acceder columnas por nombre
    return connection


def initialize_database(connection: sqlite3.Connection) -> None:
    """Crea las tablas si no existen."""
    connection.executescript(_SCHEMA_SQL)
    connection.commit()
```

### Cosas a recordar siempre

| Configuracion                    | Para que sirve                                    |
|----------------------------------|---------------------------------------------------|
| `PRAGMA foreign_keys = ON`       | Que las relaciones entre tablas se respeten        |
| `sqlite3.Row` como row_factory   | Acceder a columnas por nombre: `row["titulo"]`     |
| `IF NOT EXISTS` en CREATE TABLE  | Que no falle si la tabla ya existe                 |
| `AUTOINCREMENT` en id            | Que el ID se genere solo, sin que lo pases         |
| `NOT NULL`                       | Que la columna no acepte valores vacios            |
| `UNIQUE`                         | Que no se repitan valores (ej: ISBN)               |

---

## Paso 7: Repositorios concretos (SQLite)

### Que pensar

"Tengo que implementar cada metodo del puerto con SQL real."

### Plantilla

```python
"""Implementacion SQLite del repositorio de libros."""

from __future__ import annotations

import sqlite3
from typing import Optional

from src.mi_app.domain.exceptions import DuplicateISBNError, LibroNotFoundError
from src.mi_app.domain.models.libro import Libro
from src.mi_app.domain.ports.libro_repository import LibroRepository


class SQLiteLibroRepository(LibroRepository):
    """Repositorio de libros respaldado por SQLite."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._conn = connection

    # -- Convertir fila SQL a objeto Python --
    @staticmethod
    def _row_to_entity(row: sqlite3.Row) -> Libro:
        return Libro(
            id=row["id"],
            titulo=row["titulo"],
            autor=row["autor"],
            isbn=row["isbn"],
            disponible=bool(row["disponible"]),
        )

    # -- CREATE --
    def create(self, libro: Libro) -> Libro:
        sql = "INSERT INTO libros (titulo, autor, isbn, disponible) VALUES (?, ?, ?, ?)"
        try:
            cursor = self._conn.execute(
                sql, (libro.titulo, libro.autor, libro.isbn, int(libro.disponible))
            )
            self._conn.commit()
        except sqlite3.IntegrityError:
            raise DuplicateISBNError(libro.isbn)
        libro.id = cursor.lastrowid
        return libro

    # -- READ (uno) --
    def get_by_id(self, libro_id: int) -> Optional[Libro]:
        sql = "SELECT * FROM libros WHERE id = ?"
        row = self._conn.execute(sql, (libro_id,)).fetchone()
        if row is None:
            return None
        return self._row_to_entity(row)

    # -- READ (todos) --
    def get_all(self) -> list[Libro]:
        sql = "SELECT * FROM libros ORDER BY id"
        rows = self._conn.execute(sql).fetchall()
        return [self._row_to_entity(row) for row in rows]

    # -- UPDATE --
    def update(self, libro: Libro) -> Libro:
        sql = "UPDATE libros SET titulo = ?, autor = ?, isbn = ? WHERE id = ?"
        try:
            cursor = self._conn.execute(
                sql, (libro.titulo, libro.autor, libro.isbn, libro.id)
            )
            self._conn.commit()
        except sqlite3.IntegrityError:
            raise DuplicateISBNError(libro.isbn)
        if cursor.rowcount == 0:
            raise LibroNotFoundError(libro.id)
        return libro

    # -- DELETE --
    def delete(self, libro_id: int) -> None:
        sql = "DELETE FROM libros WHERE id = ?"
        cursor = self._conn.execute(sql, (libro_id,))
        self._conn.commit()
        if cursor.rowcount == 0:
            raise LibroNotFoundError(libro_id)
```

### El SQL de cada operacion (siempre los mismos 4)

```sql
-- CREATE
INSERT INTO tabla (campo1, campo2) VALUES (?, ?)

-- READ (uno)
SELECT * FROM tabla WHERE id = ?

-- READ (todos)
SELECT * FROM tabla ORDER BY id

-- UPDATE
UPDATE tabla SET campo1 = ?, campo2 = ? WHERE id = ?

-- DELETE
DELETE FROM tabla WHERE id = ?
```

### Patron del repositorio

Cada metodo hace 4 cosas:

```
1. Armar el SQL con ? como marcadores
2. Ejecutar con self._conn.execute(sql, (valores,))
3. Si es INSERT o UPDATE o DELETE: self._conn.commit()
4. Convertir el resultado a un objeto Python (o lanzar error si no existe)
```

### NUNCA concatenar valores directo en el SQL

```python
# MAL (vulnerable a inyeccion SQL):
sql = f"INSERT INTO libros (titulo) VALUES ('{titulo}')"

# BIEN (parametros seguros):
sql = "INSERT INTO libros (titulo) VALUES (?)"
self._conn.execute(sql, (titulo,))
```

---

## Paso 8: CLI (interfaz de consola)

### Que pensar

"Necesito un menu que se repita, que pida datos, que llame al servicio,
y que muestre resultados o errores."

### Plantilla del menu principal

```python
"""Menu principal de la aplicacion."""

from __future__ import annotations


class MainMenu:
    """Punto de entrada de la interfaz de consola."""

    BANNER = (
        "\n========================================\n"
        "   Sistema de Gestion de Biblioteca\n"
        "========================================\n"
    )

    MENU = (
        "1. Gestion de Libros\n"
        "2. Gestion de Prestamos\n"
        "0. Salir\n"
    )

    def __init__(self, libro_cli, prestamo_cli) -> None:
        self._libro_cli = libro_cli
        self._prestamo_cli = prestamo_cli

    def run(self) -> None:
        print(self.BANNER)
        actions = {
            "1": self._libro_cli.run,
            "2": self._prestamo_cli.run,
        }
        while True:
            print(self.MENU)
            choice = input("Opcion: ").strip()
            if choice == "0":
                print("\nHasta luego.")
                break
            action = actions.get(choice)
            if action is None:
                print("Opcion no valida.")
                continue
            action()
```

### Plantilla del CLI de una entidad

```python
"""CLI para la gestion de libros."""

from __future__ import annotations

from src.mi_app.application.dto.libro_dto import CreateLibroDTO, UpdateLibroDTO
from src.mi_app.application.services.libro_service import LibroService
from src.mi_app.domain.exceptions import AppDomainError


class LibroCLI:

    MENU = (
        "\n--- Gestion de Libros ---\n"
        "1. Registrar libro\n"
        "2. Listar libros\n"
        "3. Buscar libro por ID\n"
        "4. Actualizar libro\n"
        "5. Eliminar libro\n"
        "0. Volver\n"
    )

    def __init__(self, service: LibroService) -> None:
        self._service = service

    def run(self) -> None:
        actions = {
            "1": self._create,
            "2": self._list_all,
            "3": self._get_by_id,
            "4": self._update,
            "5": self._delete,
        }
        while True:
            print(self.MENU)
            choice = input("Opcion: ").strip()
            if choice == "0":
                break
            action = actions.get(choice)
            if action is None:
                print("Opcion no valida.")
                continue
            try:
                action()
            except AppDomainError as exc:
                print(f"\n[Error] {exc}")
            except ValueError as exc:
                print(f"\n[Error de validacion] {exc}")

    # -- CREATE --
    def _create(self) -> None:
        titulo = input("Titulo: ").strip()
        if not titulo:
            print("El titulo no puede estar vacio.")
            return
        autor = input("Autor: ").strip()
        if not autor:
            print("El autor no puede estar vacio.")
            return
        isbn = input("ISBN (13 caracteres): ").strip()

        dto = CreateLibroDTO(titulo=titulo, autor=autor, isbn=isbn)
        libro = self._service.register_libro(dto)
        print(f"\nLibro registrado. ID: {libro.id}")

    # -- READ (todos) --
    def _list_all(self) -> None:
        libros = self._service.list_libros()
        if not libros:
            print("\nNo hay libros registrados.")
            return
        print(f"\n{'ID':<6} {'Titulo':<30} {'Autor':<20} {'ISBN'}")
        print("-" * 70)
        for libro in libros:
            print(f"{libro.id:<6} {libro.titulo:<30} {libro.autor:<20} {libro.isbn}")
        print(f"\nTotal: {len(libros)} libro(s).")

    # -- READ (uno) --
    def _get_by_id(self) -> None:
        raw_id = input("ID del libro: ").strip()
        if not raw_id.isdigit():
            print("El ID debe ser un numero.")
            return
        libro = self._service.get_libro(int(raw_id))
        print(f"\nID:     {libro.id}")
        print(f"Titulo: {libro.titulo}")
        print(f"Autor:  {libro.autor}")
        print(f"ISBN:   {libro.isbn}")

    # -- UPDATE --
    def _update(self) -> None:
        raw_id = input("ID del libro a actualizar: ").strip()
        if not raw_id.isdigit():
            print("El ID debe ser un numero.")
            return
        titulo = input("Nuevo titulo: ").strip()
        if not titulo:
            print("El titulo no puede estar vacio.")
            return
        autor = input("Nuevo autor: ").strip()
        if not autor:
            print("El autor no puede estar vacio.")
            return
        isbn = input("Nuevo ISBN: ").strip()

        dto = UpdateLibroDTO(id=int(raw_id), titulo=titulo, autor=autor, isbn=isbn)
        libro = self._service.update_libro(dto)
        print(f"\nLibro actualizado. ID: {libro.id}, Titulo: {libro.titulo}")

    # -- DELETE --
    def _delete(self) -> None:
        raw_id = input("ID del libro a eliminar: ").strip()
        if not raw_id.isdigit():
            print("El ID debe ser un numero.")
            return
        confirm = input("Confirmar eliminacion (s/n): ").strip().lower()
        if confirm != "s":
            print("Operacion cancelada.")
            return
        self._service.remove_libro(int(raw_id))
        print("\nLibro eliminado.")
```

### Patron del CLI (siempre igual para cada metodo)

```
1. Pedir datos con input().strip()
2. Validar que no esten vacios y que sean del tipo correcto
3. Empaquetar en un DTO
4. Llamar al servicio
5. Mostrar el resultado con print()
```

---

## Paso 9: main.py (conectar todo)

### Que pensar

"Creo una instancia de cada pieza y se las paso a la siguiente."

### Plantilla

```python
"""Punto de entrada de la aplicacion."""

from pathlib import Path

from src.mi_app.application.services.libro_service import LibroService
from src.mi_app.infrastructure.cli.libro_cli import LibroCLI
from src.mi_app.infrastructure.cli.main_menu import MainMenu
from src.mi_app.infrastructure.persistence.sqlite_connection import (
    get_connection,
    initialize_database,
)
from src.mi_app.infrastructure.persistence.sqlite_libro_repository import (
    SQLiteLibroRepository,
)

_DB_PATH = Path(__file__).resolve().parent / "app.db"


def main() -> None:
    # 1. INFRAESTRUCTURA: conexion
    connection = get_connection(_DB_PATH)
    initialize_database(connection)

    # 2. INFRAESTRUCTURA: repositorios
    libro_repo = SQLiteLibroRepository(connection)

    # 3. APLICACION: servicios
    libro_service = LibroService(libro_repo)

    # 4. INFRAESTRUCTURA: CLIs
    libro_cli = LibroCLI(libro_service)

    # 5. ARRANQUE
    menu = MainMenu(libro_cli)
    try:
        menu.run()
    finally:
        connection.close()


if __name__ == "__main__":
    main()
```

### El orden de creacion en main.py (siempre el mismo)

```
1. Conexion a la BD
2. Repositorios (reciben la conexion)
3. Servicios (reciben los repositorios)
4. CLIs (reciben los servicios)
5. Menu (recibe los CLIs)
6. Ejecutar menu.run()
```

Es como armar un tren: enganchar los vagones de atras hacia adelante.

---

## Paso 10: Tests

### Que pensar

"Para cada operacion, verifico que hace lo que debe
y que falla como debe cuando algo esta mal."

### Tests unitarios (sin base de datos)

```python
"""Tests para los modelos de dominio."""

import pytest
from src.mi_app.domain.models.libro import Libro


class TestLibro:

    def test_crear_libro_valido(self):
        libro = Libro(titulo="Don Quijote", autor="Cervantes", isbn="1234567890123")
        assert libro.titulo == "Don Quijote"
        assert libro.autor == "Cervantes"
        assert libro.disponible is True
        assert libro.id is None

    def test_titulo_vacio_lanza_error(self):
        with pytest.raises(ValueError, match="titulo"):
            Libro(titulo="", autor="Cervantes", isbn="1234567890123")

    def test_isbn_incorrecto_lanza_error(self):
        with pytest.raises(ValueError, match="ISBN"):
            Libro(titulo="Test", autor="Test", isbn="123")
```

### Tests de integracion (con base de datos real en memoria)

```python
"""Tests de integracion para el repositorio SQLite."""

import pytest
from src.mi_app.domain.models.libro import Libro
from src.mi_app.infrastructure.persistence.sqlite_connection import (
    get_connection,
    initialize_database,
)
from src.mi_app.infrastructure.persistence.sqlite_libro_repository import (
    SQLiteLibroRepository,
)


@pytest.fixture
def repo():
    """Crea un repositorio con BD en memoria para cada test."""
    conn = get_connection(":memory:")     # BD temporal que se borra sola
    initialize_database(conn)
    repository = SQLiteLibroRepository(conn)
    yield repository
    conn.close()


class TestSQLiteLibroRepository:

    def test_create_and_get(self, repo):
        libro = Libro(titulo="Test", autor="Autor", isbn="1234567890123")
        created = repo.create(libro)
        assert created.id is not None

        found = repo.get_by_id(created.id)
        assert found is not None
        assert found.titulo == "Test"

    def test_get_all_empty(self, repo):
        assert repo.get_all() == []

    def test_delete(self, repo):
        libro = Libro(titulo="Test", autor="Autor", isbn="1234567890123")
        created = repo.create(libro)
        repo.delete(created.id)
        assert repo.get_by_id(created.id) is None
```

### Que testear como minimo

| Operacion | Test positivo (funciona)         | Test negativo (falla bien)         |
|-----------|-----------------------------------|------------------------------------|
| Create    | Crear y verificar que tiene ID    | Crear con dato duplicado           |
| Read      | Buscar uno que existe             | Buscar uno que NO existe           |
| List      | Listar con datos y sin datos      | --                                 |
| Update    | Actualizar y verificar cambio     | Actualizar uno que no existe       |
| Delete    | Eliminar y verificar que no esta  | Eliminar uno que no existe         |
| Modelo    | Crear con datos validos           | Crear con datos invalidos          |

---

## Checklist final

Antes de dar por terminado tu CRUD, verifica:

| #  | Verificacion                                        | Hecho? |
|----|-----------------------------------------------------|--------|
| 1  | Cree excepciones para cada error de negocio          |        |
| 2  | Cada modelo se valida a si mismo en __post_init__    |        |
| 3  | El puerto tiene las 5 operaciones minimas (CRUD+list)|        |
| 4  | Cada DTO tiene SOLO los campos que necesita           |        |
| 5  | El servicio no sabe de SQL ni de la BD                |        |
| 6  | El repositorio usa parametros (?) en vez de f-strings |        |
| 7  | El CLI valida input antes de empaquetar en DTO        |        |
| 8  | main.py conecta todo en el orden correcto             |        |
| 9  | Los tests cubren casos positivos y negativos          |        |
| 10 | Ningun archivo de domain importa de infrastructure    |        |

---

## Plantilla reutilizable para entidades nuevas

Cuando necesites agregar una entidad nueva (ej: Prestamo) a un proyecto
que ya tiene la estructura armada, crea estos 5 archivos en este orden:

```
1. domain/models/prestamo.py           --> Que ES un prestamo
2. domain/ports/prestamo_repository.py --> Que operaciones necesita
3. application/dto/prestamo_dto.py     --> Que datos viajan
4. application/services/prestamo_service.py --> Que se puede hacer
5. infrastructure/persistence/sqlite_prestamo_repository.py --> SQL real
6. infrastructure/cli/prestamo_cli.py  --> Menu de consola
7. Agregar al main.py                  --> Conectar la pieza nueva
8. Tests
```

Siempre el mismo orden. Siempre los mismos archivos.

---

## Reglas de oro de la arquitectura hexagonal

### Regla 1: La dependencia siempre va hacia adentro

```
infrastructure --> application --> domain
     (afuera)       (medio)       (centro)
```

- infrastructure puede importar de application y domain.
- application puede importar de domain.
- domain NO importa de nadie.

### Regla 2: El dominio no sabe que existe una base de datos

`transformer.py` no sabe si sus datos se guardan en SQLite, PostgreSQL,
un archivo, o en la luna. Solo define QUE es un transformador.

### Regla 3: Los servicios hablan con interfaces, no con implementaciones

```python
# BIEN: el servicio recibe la interfaz abstracta
def __init__(self, repository: LibroRepository) -> None:

# MAL: el servicio recibe la implementacion concreta
def __init__(self, repository: SQLiteLibroRepository) -> None:
```

### Regla 4: main.py es el unico que conoce todo

Es el unico archivo que importa de las 3 capas. Es el que arma
las piezas como un LEGO. Si cambias la base de datos, solo tocas main.py
y el repositorio nuevo. Nada mas.

### Regla 5: Si sacas la infraestructura, el dominio sigue funcionando

Si borras todos los archivos de `infrastructure/`, los modelos,
los puertos, los DTOs y los servicios siguen compilando perfectamente.
No les falta nada. Eso prueba que la arquitectura esta bien hecha.

---

## Resumen: el proceso completo en una pagina

```
1. PLANIFICAR en papel
   - Que datos? (campos de cada entidad)
   - Que operaciones? (create, read, update, delete, otras)
   - Que validaciones? (campos vacios, duplicados, rangos)
   - Que errores? (no encontrado, duplicado, invalido)

2. CREAR directorios
   domain/ --> application/ --> infrastructure/ --> tests/

3. CODIFICAR en orden
   exceptions --> modelos --> puertos --> DTOs --> servicios
   --> conexion BD --> repositorios --> CLI --> main.py

4. TESTEAR
   - Modelos: se crean bien, se validan bien
   - Servicios: cada operacion funciona
   - Repositorios: SQL funciona, errores se manejan

5. VERIFICAR la arquitectura
   - domain no importa de nadie?
   - El servicio solo habla con interfaces?
   - main.py es el unico que arma las piezas?

Si todo cumple: el CRUD esta terminado profesionalmente.
```
