# Referencia Python Esencial para Desarrollo Profesional

Guia rapida de todas las herramientas de Python que se usan
al construir un CRUD con arquitectura hexagonal.
Cada seccion incluye la sintaxis exacta, que hace, cuando usarla,
y errores comunes a evitar.

---

## Indice

1. [Dataclasses](#1-dataclasses)
2. [\_\_post\_init\_\_](#2-__post_init__)
3. [\_\_init\_\_](#3-__init__)
4. [super()](#4-super)
5. [ABC y abstractmethod](#5-abc-y-abstractmethod)
6. [Excepciones: raise, try, except, finally](#6-excepciones-raise-try-except-finally)
7. [Type Hints (anotaciones de tipo)](#7-type-hints-anotaciones-de-tipo)
8. [Optional](#8-optional)
9. [from \_\_future\_\_ import annotations](#9-from-__future__-import-annotations)
10. [ClassVar](#10-classvar)
11. [staticmethod](#11-staticmethod)
12. [Property](#12-property)
13. [List Comprehensions](#13-list-comprehensions)
14. [Dictionary .get()](#14-dictionary-get)
15. [f-strings](#15-f-strings)
16. [Metodos de string: strip, isdigit, lower, upper](#16-metodos-de-string)
17. [Path (pathlib)](#17-path-pathlib)
18. [with (context managers)](#18-with-context-managers)
19. [yield y fixtures de pytest](#19-yield-y-fixtures-de-pytest)
20. [pytest.raises](#20-pytestraises)
21. [\_\_name\_\_ == "\_\_main\_\_"](#21-__name__--__main__)
22. [Docstrings](#22-docstrings)
23. [Tuplas de un solo elemento](#23-tuplas-de-un-solo-elemento)
24. [Operador walrus :=](#24-operador-walrus)
25. [Enum](#25-enum)
26. [slots](#26-slots)
27. [Tabla resumen rapida](#27-tabla-resumen-rapida)

---

## 1. Dataclasses

### Que es

Un decorador que convierte una clase en un contenedor de datos.
Te genera automaticamente `__init__`, `__repr__` y `__eq__`
sin que los escribas.

### Sintaxis

```python
from dataclasses import dataclass

@dataclass
class Libro:
    titulo: str
    autor: str
    isbn: str
    disponible: bool = True       # Valor por defecto
    id: int | None = None         # Valor por defecto
```

### Que genera automaticamente

```python
# Python crea esto por ti detras de escena:

def __init__(self, titulo, autor, isbn, disponible=True, id=None):
    self.titulo = titulo
    self.autor = autor
    self.isbn = isbn
    self.disponible = disponible
    self.id = id

def __repr__(self):
    return "Libro(titulo='...', autor='...', ...)"

def __eq__(self, other):
    return self.titulo == other.titulo and self.autor == other.autor and ...
```

### Opciones del decorador

| Opcion      | Que hace                                    | Cuando usarla                       |
|-------------|---------------------------------------------|-------------------------------------|
| (nada)      | Clase mutable normal                        | Entidades (Libro, Transformador)    |
| `frozen=True` | No se pueden cambiar los campos despues de crear | Value Objects, DTOs           |
| `slots=True`  | Usa menos memoria y es mas rapido          | Siempre que puedas                  |

### Ejemplos

```python
# Entidad mutable (se puede cambiar)
@dataclass(slots=True)
class Libro:
    titulo: str
    id: int | None = None

libro = Libro(titulo="Test")
libro.id = 5                     # OK, se puede cambiar


# Value Object inmutable (NO se puede cambiar)
@dataclass(frozen=True, slots=True)
class CreateLibroDTO:
    titulo: str
    autor: str

dto = CreateLibroDTO(titulo="Test", autor="Ana")
dto.titulo = "Otro"              # ERROR: frozen no permite cambios
```

### Regla para el orden de los campos

Los campos SIN valor por defecto van PRIMERO.
Los campos CON valor por defecto van DESPUES.

```python
# BIEN:
@dataclass
class Libro:
    titulo: str                   # Sin default --> primero
    autor: str                    # Sin default --> primero
    disponible: bool = True       # Con default --> despues
    id: int | None = None         # Con default --> despues

# MAL (da error):
@dataclass
class Libro:
    disponible: bool = True       # Con default
    titulo: str                   # Sin default DESPUES de uno con default --> ERROR
```

### Error comun

```python
# MAL: olvidar los dos puntos y el tipo
@dataclass
class Libro:
    titulo            # ERROR: falta el tipo
    autor             # ERROR: falta el tipo

# BIEN:
@dataclass
class Libro:
    titulo: str
    autor: str
```

---

## 2. \_\_post\_init\_\_

### Que es

Un metodo especial que se ejecuta AUTOMATICAMENTE justo despues
de que `__init__` termina de asignar los campos. Es donde pones
las validaciones de negocio.

### Sintaxis

```python
@dataclass(slots=True)
class Libro:
    titulo: str
    autor: str
    isbn: str
    id: int | None = None

    def __post_init__(self) -> None:
        self.titulo = self.titulo.strip()
        self.autor = self.autor.strip()

        if not self.titulo:
            raise ValueError("El titulo no puede estar vacio.")
        if len(self.isbn) != 13:
            raise ValueError("El ISBN debe tener 13 caracteres.")
```

### Cuando se ejecuta

```
libro = Libro(titulo="  Don Quijote  ", autor="Cervantes", isbn="1234567890123")

Internamente pasa esto:
  1. __init__ asigna:  self.titulo = "  Don Quijote  "
  2. __init__ asigna:  self.autor = "Cervantes"
  3. __init__ asigna:  self.isbn = "1234567890123"
  4. __init__ termina
  5. __post_init__ se ejecuta automaticamente:
     - self.titulo = "  Don Quijote  ".strip()  -->  "Don Quijote"
     - Valida que titulo no este vacio  -->  OK
     - Valida que isbn tenga 13 chars   -->  OK
  6. El objeto esta listo para usar
```

### Para que usarlo

| Uso                    | Ejemplo                                          |
|------------------------|--------------------------------------------------|
| Limpiar datos          | `self.titulo = self.titulo.strip()`              |
| Validar reglas         | `if not self.titulo: raise ValueError(...)`      |
| Calcular valores       | `self.nombre_completo = f"{self.nombre} {self.apellido}"` |
| Convertir tipos        | `self.fecha = str(self.fecha)`                   |

### Error comun

```python
# MAL: escribir __postinit__ (falta los guiones bajos dobles)
def __postinit__(self):     # NUNCA se ejecuta, nombre incorrecto

# BIEN:
def __post_init__(self):    # Dos guiones antes y despues de post_init
```

### Se puede usar con frozen?

Si, pero con un truco. En frozen no puedes hacer `self.campo = valor`.
Tienes que usar `object.__setattr__`:

```python
@dataclass(frozen=True, slots=True)
class GasReading:
    hydrogen: float

    def __post_init__(self) -> None:
        if self.hydrogen < 0:
            raise ValueError("El hidrogeno no puede ser negativo.")
        # Si necesitaras modificar un campo:
        # object.__setattr__(self, "hydrogen", round(self.hydrogen, 2))
```

---

## 3. \_\_init\_\_

### Que es

El constructor de la clase. Se ejecuta cuando creas un objeto con
`MiClase(...)`. Es donde recibes parametros y los guardas dentro
del objeto.

### Sintaxis

```python
class LibroService:
    def __init__(self, repository: LibroRepository) -> None:
        self._repository = repository
```

### Cuando se ejecuta

```python
servicio = LibroService(mi_repo)

Internamente:
  1. Python crea el objeto vacio
  2. Llama a __init__(self, repository=mi_repo)
  3. self._repository = mi_repo  (guarda la referencia)
  4. El objeto esta listo
```

### self: que es

`self` es UNA REFERENCIA AL PROPIO OBJETO que se esta creando o usando.
Python lo pone automaticamente como primer parametro de cada metodo.

```python
class Caja:
    def __init__(self, color: str) -> None:
        self.color = color          # "Yo (la caja) tengo este color"

    def mostrar(self) -> None:
        print(self.color)           # "Yo (la caja) muestro mi color"

c = Caja("rojo")
c.mostrar()                         # Imprime: rojo
```

### Cuando escribes __init__ vs cuando NO

| Situacion                              | Escribes __init__? |
|----------------------------------------|--------------------|
| Clase normal (servicio, CLI, repo)     | SI, tu lo escribes |
| Clase con @dataclass                   | NO, se genera solo |
| Clase de excepcion con datos extra     | SI, tu lo escribes |

### Error comun

```python
# MAL: olvidar self
class LibroService:
    def __init__(repository):       # ERROR: falta self
        self._repository = repository

# BIEN:
class LibroService:
    def __init__(self, repository):
        self._repository = repository
```

---

## 4. super()

### Que es

Llama al `__init__` de la clase padre. Lo usas cuando tu clase
hereda de otra y necesitas que la clase padre tambien se inicialice.

### Sintaxis

```python
class LibroNotFoundError(AppDomainError):
    def __init__(self, libro_id: int) -> None:
        self.libro_id = libro_id
        super().__init__(f"No se encontro el libro con ID {libro_id}.")
```

### Que pasa internamente

```python
error = LibroNotFoundError(99)

Paso 1: Python entra a LibroNotFoundError.__init__(self, 99)
Paso 2: self.libro_id = 99               (guarda el dato propio)
Paso 3: super().__init__("No se encontro el libro con ID 99.")
         Esto llama a Exception.__init__ con el mensaje de texto
Paso 4: Ahora print(error) muestra: "No se encontro el libro con ID 99."
         Porque Exception guarda ese texto internamente
```

### Cuando usarlo

| Situacion                                  | Necesitas super()? |
|--------------------------------------------|---------------------|
| Tu clase hereda de Exception               | SI                  |
| Tu clase hereda de ABC                     | Normalmente NO      |
| Tu clase hereda de otra clase propia       | SI, si el padre tiene __init__ |
| Tu clase no hereda de nadie                | NO aplica           |

### Error comun

```python
# MAL: olvidar los parentesis de super
super.__init__("mensaje")          # ERROR: falta ()

# MAL: olvidar llamar a super
class MiError(AppDomainError):
    def __init__(self, dato):
        self.dato = dato
        # Falta super().__init__(...) --> print(error) no muestra nada util

# BIEN:
class MiError(AppDomainError):
    def __init__(self, dato):
        self.dato = dato
        super().__init__(f"Error con dato: {dato}")
```

---

## 5. ABC y abstractmethod

### Que es

`ABC` (Abstract Base Class) te permite crear interfaces: clases que
definen QUE metodos deben existir, pero no los implementan.

`@abstractmethod` marca un metodo como "obligatorio de implementar".

### Sintaxis

```python
from abc import ABC, abstractmethod
from typing import Optional

class LibroRepository(ABC):

    @abstractmethod
    def create(self, libro: Libro) -> Libro:
        """Guarda un libro nuevo."""

    @abstractmethod
    def get_by_id(self, libro_id: int) -> Optional[Libro]:
        """Busca por ID."""

    @abstractmethod
    def get_all(self) -> list[Libro]:
        """Devuelve todos."""

    @abstractmethod
    def update(self, libro: Libro) -> Libro:
        """Actualiza un libro."""

    @abstractmethod
    def delete(self, libro_id: int) -> None:
        """Elimina un libro."""
```

### Como se implementa

```python
class SQLiteLibroRepository(LibroRepository):    # Hereda del ABC

    def create(self, libro: Libro) -> Libro:      # Implementa cada metodo
        sql = "INSERT INTO ..."
        # ...

    def get_by_id(self, libro_id: int) -> Optional[Libro]:
        sql = "SELECT ..."
        # ...

    # ... todos los demas metodos
```

### Que pasa si olvidas implementar un metodo

```python
class SQLiteLibroRepository(LibroRepository):
    def create(self, libro: Libro) -> Libro:
        pass
    # Me olvide de get_by_id, get_all, update, delete

repo = SQLiteLibroRepository()
# TypeError: Can't instantiate abstract class SQLiteLibroRepository
#            with abstract methods 'delete', 'get_all', 'get_by_id', 'update'
```

Python te dice EXACTAMENTE cuales te faltaron. No hay forma de que se te pase.

### Reglas clave

```
1. Los metodos abstractos NO tienen cuerpo (solo docstring o pass)
2. La clase que hereda DEBE implementar TODOS los metodos abstractos
3. No puedes crear una instancia de la clase abstracta directamente:
       repo = LibroRepository()   # ERROR, es abstracta
4. Solo puedes crear instancias de las clases concretas:
       repo = SQLiteLibroRepository(conn)   # OK
```

---

## 6. Excepciones: raise, try, except, finally

### raise: lanzar un error

```python
# Lanzar un error general
raise ValueError("El titulo no puede estar vacio.")

# Lanzar un error personalizado
raise LibroNotFoundError(libro_id)
```

`raise` DETIENE la ejecucion inmediatamente y busca un `except`
que lo atrape. Si nadie lo atrapa, el programa se cae.

### try / except: atrapar errores

```python
try:
    # Codigo que PUEDE fallar
    libro = servicio.get_libro(99)
except LibroNotFoundError as exc:
    # Que hacer si falla con ESE error
    print(f"Error: {exc}")
except ValueError as exc:
    # Que hacer si falla con OTRO error
    print(f"Dato invalido: {exc}")
```

### try / except / finally: limpiar siempre

```python
try:
    menu.run()
finally:
    connection.close()     # Se ejecuta SIEMPRE, haya error o no
```

`finally` es para limpieza. Se ejecuta pase lo que pase:
si todo sale bien, si hay error, o si el usuario cierra el programa.

### as exc: que es

`as exc` guarda el error en una variable para poder usarlo:

```python
except AppDomainError as exc:
    print(exc)              # Imprime el mensaje del error
    print(exc.libro_id)     # Accede a los datos del error
```

Puedes ponerle cualquier nombre en vez de `exc`:
`as e`, `as error`, `as err`. Todos significan lo mismo.

### Orden de los except (importante)

Van del MAS ESPECIFICO al MAS GENERAL:

```python
try:
    action()
except LibroNotFoundError as exc:     # Especifico primero
    print(f"No se encontro: {exc}")
except AppDomainError as exc:         # General despues
    print(f"Error de dominio: {exc}")
except Exception as exc:              # Muy general al final
    print(f"Error inesperado: {exc}")
```

Si pones el general primero, el especifico nunca se ejecuta:

```python
# MAL:
except AppDomainError as exc:         # Atrapa TODO, incluyendo LibroNotFound
    print(...)
except LibroNotFoundError as exc:     # NUNCA llega aca
    print(...)
```

### Tabla resumen

| Palabra   | Que hace                              | Obligatorio? |
|-----------|---------------------------------------|--------------|
| `try`     | Encierra el codigo que puede fallar   | SI           |
| `except`  | Atrapa un tipo de error               | SI (al menos uno) |
| `else`    | Se ejecuta si NO hubo error           | NO           |
| `finally` | Se ejecuta SIEMPRE                    | NO           |
| `raise`   | Lanza un error manualmente            | Independiente|
| `as`      | Guarda el error en una variable       | NO           |

---

## 7. Type Hints (anotaciones de tipo)

### Que es

Indicaciones que le dices a Python (y a tu editor) sobre que tipo
de dato espera cada variable, parametro o retorno.

**Python NO las obliga.** Pero tu editor (Pylance) si las verifica
y te avisa cuando algo no cuadra.

### Sintaxis basica

```python
# Variables
nombre: str = "Ana"
edad: int = 25
activo: bool = True
precio: float = 19.99

# Parametros de funcion
def saludar(nombre: str) -> str:
    return f"Hola {nombre}"

# Retorno None (no devuelve nada)
def eliminar(libro_id: int) -> None:
    ...

# Parametro con valor por defecto
def buscar(limite: int = 10) -> list[str]:
    ...
```

### Tipos compuestos

```python
# Lista de strings
nombres: list[str] = ["Ana", "Luis"]

# Lista de objetos
libros: list[Libro] = [libro1, libro2]

# Diccionario
opciones: dict[str, int] = {"a": 1, "b": 2}

# Tupla
coordenada: tuple[float, float] = (10.5, 20.3)

# Puede ser de dos tipos
dato: str | None = None           # Python 3.10+
dato: int | str = 5               # Python 3.10+
```

### En clases

```python
class LibroService:
    def __init__(self, repository: LibroRepository) -> None:
        self._repository: LibroRepository = repository

    def get_libro(self, libro_id: int) -> Libro:
        ...

    def list_libros(self) -> list[Libro]:
        ...
```

### Tipos mas usados

| Tipo              | Ejemplo                    | Significa                     |
|-------------------|----------------------------|-------------------------------|
| `str`             | `"hola"`                   | Texto                         |
| `int`             | `42`                       | Numero entero                 |
| `float`           | `3.14`                     | Numero decimal                |
| `bool`            | `True`                     | Verdadero o falso             |
| `None`            | `None`                     | Nada, vacio                   |
| `list[X]`         | `[1, 2, 3]`               | Lista de elementos tipo X     |
| `dict[K, V]`      | `{"a": 1}`                | Diccionario clave:valor       |
| `tuple[X, Y]`     | `(1, "a")`                | Tupla con tipos fijos         |
| `X \| None`       | `libro \| None`            | Puede ser X o puede ser None  |

---

## 8. Optional

### Que es

`Optional[X]` significa "puede ser X o puede ser None".
Es equivalente a `X | None`.

### Sintaxis

```python
from typing import Optional

def get_by_id(self, libro_id: int) -> Optional[Libro]:
    """Devuelve un Libro o None si no existe."""
    row = self._conn.execute(sql, (libro_id,)).fetchone()
    if row is None:
        return None
    return self._row_to_entity(row)
```

### Equivalencias

```python
# Estas dos lineas significan EXACTAMENTE lo mismo:
id: Optional[int] = None
id: int | None = None

# La segunda forma (con |) es mas moderna (Python 3.10+)
```

### Cuando usarlo

| Situacion                               | Tipo de retorno       |
|-----------------------------------------|-----------------------|
| Siempre devuelve algo                    | `-> Libro`           |
| A veces no encuentra nada                | `-> Optional[Libro]` |
| Parametro que puede faltar               | `id: Optional[int] = None` |

---

## 9. from \_\_future\_\_ import annotations

### Que es

Una linea que va AL INICIO del archivo (antes de cualquier import).
Le dice a Python: "no evalues las anotaciones de tipo ahora,
tratalas como texto".

### Sintaxis

```python
from __future__ import annotations     # Siempre en la linea 1 o 2

from dataclasses import dataclass

@dataclass
class Libro:
    titulo: str
```

### Para que sirve

1. **Permite usar tipos que aun no se definieron:**

```python
from __future__ import annotations

class Nodo:
    def siguiente(self) -> Nodo:     # Sin __future__, esto da error
        ...                           # porque Nodo aun no termino de definirse
```

2. **Permite usar sintaxis moderna en Python 3.9:**

```python
from __future__ import annotations

# Sin __future__ en Python 3.9, tendrias que escribir:
from typing import Optional, List
def get_all(self) -> List[Libro]:     # List con L mayuscula

# Con __future__, puedes escribir la forma moderna:
def get_all(self) -> list[Libro]:     # list con l minuscula
```

### Regla simple

Ponlo en TODOS tus archivos .py como primera linea (despues del docstring).
No tiene efectos negativos y evita problemas de compatibilidad.

---

## 10. ClassVar

### Que es

Marca un campo como "pertenece a la CLASE, no a cada objeto individual".
Es una variable compartida por todas las instancias.

### Sintaxis

```python
from dataclasses import dataclass
from typing import ClassVar

@dataclass(frozen=True, slots=True)
class GasReading:
    hydrogen: float
    methane: float

    GAS_LABELS: ClassVar[dict[str, str]] = {
        "hydrogen": "Hidrogeno (H2)",
        "methane": "Metano (CH4)",
    }
```

### Diferencia entre campo normal y ClassVar

```python
# Campo normal: cada objeto tiene su propia copia
libro1.titulo = "Don Quijote"
libro2.titulo = "Hamlet"           # Cada libro tiene su titulo

# ClassVar: todos comparten el mismo valor
GasReading.GAS_LABELS              # Uno solo para TODA la clase
# No se pasa en el constructor, no se incluye en __init__
```

### Cuando usarlo

| Caso                                        | Ejemplo                          |
|---------------------------------------------|----------------------------------|
| Constantes de la clase                       | Etiquetas, formatos              |
| Valores que no cambian entre instancias      | Configuracion fija               |
| Datos de referencia                          | Tablas de conversion             |

---

## 11. staticmethod

### Que es

Un metodo que pertenece a la clase pero NO necesita acceso al objeto
(`self`) ni a la clase (`cls`). Es como una funcion suelta que vive
dentro de la clase por organizacion.

### Sintaxis

```python
class SQLiteLibroRepository(LibroRepository):

    @staticmethod
    def _row_to_entity(row: sqlite3.Row) -> Libro:
        return Libro(
            id=row["id"],
            titulo=row["titulo"],
            autor=row["autor"],
            isbn=row["isbn"],
            disponible=bool(row["disponible"]),
        )
```

### No recibe self

```python
# Metodo normal: recibe self (accede al objeto)
def create(self, libro: Libro) -> Libro:
    self._conn.execute(...)         # Usa self._conn

# Metodo estatico: NO recibe self (no necesita acceder al objeto)
@staticmethod
def _row_to_entity(row: sqlite3.Row) -> Libro:
    return Libro(id=row["id"], ...)  # Solo trabaja con lo que le pasan
```

### Cuando usarlo

Cuando el metodo no necesita `self` ni ningun dato del objeto.
Solo trabaja con los parametros que recibe.

Ejemplo tipico: convertir una fila de la base de datos a un objeto Python.

---

## 12. Property

### Que es

Convierte un metodo en algo que se usa como si fuera un campo.
Se accede SIN parentesis.

### Sintaxis

```python
@dataclass
class Rectangulo:
    ancho: float
    alto: float

    @property
    def area(self) -> float:
        return self.ancho * self.alto
```

### Como se usa

```python
r = Rectangulo(ancho=5, alto=3)
print(r.area)                      # 15.0  (sin parentesis, como un campo)
# print(r.area())                  # NO, esto daria error
```

### Cuando usarlo

| Situacion                                  | Usar property? |
|--------------------------------------------|----------------|
| Valor que se calcula a partir de otros     | SI             |
| Quieres que se vea como un campo           | SI             |
| Necesitas recibir parametros               | NO (usa metodo normal) |

---

## 13. List Comprehensions

### Que es

Una forma compacta de crear una lista nueva a partir de otra.

### Sintaxis basica

```python
# Forma larga:
resultado = []
for row in rows:
    resultado.append(self._row_to_entity(row))

# Forma compacta (list comprehension):
resultado = [self._row_to_entity(row) for row in rows]
```

Ambas hacen EXACTAMENTE lo mismo. La segunda es mas profesional.

### Con filtro

```python
# Solo los libros disponibles
disponibles = [libro for libro in libros if libro.disponible]

# Solo los numeros positivos
positivos = [n for n in numeros if n > 0]
```

### Con transformacion

```python
# Convertir a mayusculas
mayusculas = [nombre.upper() for nombre in nombres]

# Extraer solo los IDs
ids = [libro.id for libro in libros]
```

### Patron comun en repositorios

```python
def get_all(self) -> list[Libro]:
    rows = self._conn.execute("SELECT * FROM libros").fetchall()
    return [self._row_to_entity(row) for row in rows]
```

---

## 14. Dictionary .get()

### Que es

Busca una clave en un diccionario. Si no la encuentra,
devuelve `None` (o un valor que tu elijas) en vez de dar error.

### Sintaxis

```python
datos = {"a": 1, "b": 2, "c": 3}

datos["a"]            # 1         (si existe, OK)
datos["z"]            # KeyError  (si NO existe, ERROR)

datos.get("a")        # 1         (si existe, OK)
datos.get("z")        # None      (si NO existe, devuelve None)
datos.get("z", 0)     # 0         (si NO existe, devuelve 0)
```

### Uso tipico en CLIs (despacho de acciones)

```python
actions = {
    "1": self._create,
    "2": self._list_all,
    "3": self._get_by_id,
}

action = actions.get(choice)       # Si choice="5", action = None
if action is None:
    print("Opcion no valida.")
    continue
action()                           # Ejecuta la funcion encontrada
```

### Por que usar .get() en vez de []

```python
# CON []: si la clave no existe, el programa se cae
action = actions[choice]           # KeyError si choice no esta

# CON .get(): si la clave no existe, devuelve None tranquilamente
action = actions.get(choice)       # None si choice no esta
```

---

## 15. f-strings

### Que es

Cadenas de texto que permiten meter variables adentro usando `{}`.

### Sintaxis

```python
nombre = "Ana"
edad = 25

# f-string basico
mensaje = f"Hola {nombre}, tienes {edad} anos."
# Resultado: "Hola Ana, tienes 25 anos."

# Puedes poner expresiones
mensaje = f"El doble es {edad * 2}."
# Resultado: "El doble es 50."

# Puedes llamar metodos
mensaje = f"Nombre: {nombre.upper()}"
# Resultado: "Nombre: ANA"
```

### Alineacion y formato (para tablas)

```python
# Alinear a la izquierda con ancho fijo
print(f"{'ID':<6} {'Titulo':<30} {'Autor':<20}")
print(f"{libro.id:<6} {libro.titulo:<30} {libro.autor:<20}")

# < = izquierda
# > = derecha
# ^ = centro
# El numero es el ancho minimo en caracteres
```

### Multilinea

```python
BANNER = (
    f"\n{'='*40}\n"
    f"   Sistema de Biblioteca\n"
    f"{'='*40}\n"
)
```

### Error comun

```python
# MAL: olvidar la f al inicio
mensaje = "Hola {nombre}"          # Imprime: Hola {nombre}  (literal)

# BIEN:
mensaje = f"Hola {nombre}"         # Imprime: Hola Ana
```

---

## 16. Metodos de string

### Los mas usados

| Metodo         | Que hace                            | Ejemplo                                |
|----------------|-------------------------------------|----------------------------------------|
| `.strip()`     | Quita espacios al inicio y final    | `"  hola  ".strip()` --> `"hola"`      |
| `.isdigit()`   | Verifica si es solo numeros         | `"123".isdigit()` --> `True`           |
| `.lower()`     | Convierte a minusculas              | `"Hola".lower()` --> `"hola"`          |
| `.upper()`     | Convierte a mayusculas              | `"hola".upper()` --> `"HOLA"`          |
| `.startswith()`| Verifica si empieza con algo        | `"abc".startswith("a")` --> `True`     |
| `.endswith()`  | Verifica si termina con algo        | `"foto.png".endswith(".png")` --> `True`|
| `.replace()`   | Reemplaza texto                     | `"a-b".replace("-", "_")` --> `"a_b"`  |
| `.split()`     | Divide en una lista                 | `"a,b,c".split(",")` --> `["a","b","c"]`|
| `.join()`      | Une una lista en un string          | `", ".join(["a","b"])` --> `"a, b"`    |

### Uso tipico en validacion de input

```python
raw_id = input("ID: ").strip()          # Quita espacios

if not raw_id:                          # Esta vacio?
    print("Debe ingresar un valor.")
    return

if not raw_id.isdigit():                # Es un numero?
    print("El ID debe ser un numero.")
    return

libro_id = int(raw_id)                  # Ahora si, convertir a entero
```

### Encadenar metodos

```python
respuesta = input("Confirmar (s/n): ").strip().lower()
# .strip() quita espacios --> .lower() convierte a minusculas
# Si el usuario escribe "  S  ", queda "s"
```

---

## 17. Path (pathlib)

### Que es

Una forma moderna de trabajar con rutas de archivos y carpetas.

### Importar

```python
from pathlib import Path
```

### Usos comunes

```python
# Ruta del archivo actual
ruta_actual = Path(__file__)

# Directorio donde esta el archivo
directorio = Path(__file__).resolve().parent

# Construir ruta a la base de datos (junto al archivo actual)
_DB_PATH = Path(__file__).resolve().parent / "app.db"

# Verificar si existe
if _DB_PATH.exists():
    print("La BD existe")

# Leer un archivo
contenido = Path("datos.txt").read_text(encoding="utf-8")
```

### Operaciones utiles

| Operacion               | Codigo                              | Resultado              |
|--------------------------|-------------------------------------|------------------------|
| Unir rutas               | `Path("src") / "app" / "main.py"`  | `src/app/main.py`     |
| Nombre del archivo       | `Path("docs/guia.md").name`         | `"guia.md"`           |
| Extension                | `Path("guia.md").suffix`            | `".md"`               |
| Sin extension            | `Path("guia.md").stem`              | `"guia"`              |
| Directorio padre         | `Path("src/app/main.py").parent`    | `src/app`             |
| Ruta absoluta            | `Path("app.db").resolve()`          | `C:\Users\...\app.db` |
| Existe?                  | `Path("app.db").exists()`           | `True` o `False`      |

### Por que Path y no strings

```python
# MAL (concatenar strings, problemas con / y \)
ruta = "src" + "\\" + "app" + "\\" + "main.py"

# BIEN (Path maneja las barras automaticamente)
ruta = Path("src") / "app" / "main.py"
```

---

## 18. with (context managers)

### Que es

Abre un recurso (archivo, conexion, etc.) y GARANTIZA que se cierre
automaticamente cuando terminas, aunque haya un error.

### Sintaxis

```python
# Abrir un archivo
with open("datos.txt", "r", encoding="utf-8") as archivo:
    contenido = archivo.read()
# Aqui el archivo ya se cerro automaticamente

# Sin with (peligroso, puedes olvidar cerrar):
archivo = open("datos.txt", "r")
contenido = archivo.read()
archivo.close()                     # Si hay error antes, nunca se cierra
```

### Uso con bases de datos

```python
# Patron del main.py en nuestro proyecto:
connection = get_connection(_DB_PATH)
try:
    menu.run()
finally:
    connection.close()

# Equivalente con with (si la conexion lo soporta):
with get_connection(_DB_PATH) as connection:
    menu.run()
# Se cierra automaticamente
```

### Regla

Siempre que abras algo que necesita cerrarse (archivos, conexiones,
sockets), usa `with` o `try/finally`. Nunca dejes recursos abiertos.

---

## 19. yield y fixtures de pytest

### Que es yield

`yield` es como `return`, pero la funcion NO termina. Se pausa.
Cuando la necesitas de nuevo, continua desde donde se quedo.

### Uso en pytest: fixtures

Una fixture es una funcion que PREPARA algo antes del test
y LIMPIA despues.

```python
import pytest

@pytest.fixture
def repo():
    # PREPARACION (antes del test)
    conn = get_connection(":memory:")
    initialize_database(conn)
    repository = SQLiteLibroRepository(conn)

    yield repository         # <-- Pausa aqui. El test usa 'repository'.

    # LIMPIEZA (despues del test, aunque haya fallado)
    conn.close()
```

### Que pasa paso a paso

```
1. El test pide 'repo' como parametro:
       def test_crear(self, repo):

2. pytest ejecuta la fixture hasta el yield:
       conn = get_connection(":memory:")
       initialize_database(conn)
       repository = SQLiteLibroRepository(conn)
       yield repository   <-- PAUSA: le pasa 'repository' al test

3. El test se ejecuta:
       created = repo.create(libro)
       assert created.id is not None

4. El test termina. pytest vuelve a la fixture
   y ejecuta lo que esta DESPUES del yield:
       conn.close()
```

### Beneficio

No tienes que repetir la preparacion y limpieza en cada test.
Lo escribes UNA vez en la fixture y todos los tests la comparten.

---

## 20. pytest.raises

### Que es

Verifica que un bloque de codigo LANCE un error especifico.
Si el error no se lanza, el test FALLA.

### Sintaxis

```python
import pytest

# Verificar que se lanza ValueError
def test_titulo_vacio(self):
    with pytest.raises(ValueError, match="titulo"):
        Libro(titulo="", autor="Test", isbn="1234567890123")

# Verificar que se lanza un error de dominio
def test_libro_no_encontrado(self):
    with pytest.raises(LibroNotFoundError):
        servicio.get_libro(999)
```

### Que hace match

`match="titulo"` verifica que el MENSAJE del error contenga la palabra "titulo".
Es opcional pero recomendable para asegurar que es el error correcto.

```python
# Este test pasa porque el mensaje contiene "titulo":
# ValueError("El titulo no puede estar vacio.")
with pytest.raises(ValueError, match="titulo"):
    Libro(titulo="", autor="Test", isbn="1234567890123")

# Este test FALLA porque el mensaje no contiene "autor":
with pytest.raises(ValueError, match="autor"):
    Libro(titulo="", autor="Test", isbn="1234567890123")
```

### Patron del test

```python
with pytest.raises(TipoDeError):
    codigo_que_deberia_fallar()

# Si el codigo NO lanza el error: el test FALLA (rojo)
# Si el codigo SI lanza el error: el test PASA (verde)
```

---

## 21. \_\_name\_\_ == "\_\_main\_\_"

### Que es

Una condicion que verifica si el archivo se esta ejecutando directamente
(no importado desde otro archivo).

### Sintaxis

```python
def main() -> None:
    # Todo el codigo de arranque

if __name__ == "__main__":
    main()
```

### Que pasa en cada caso

```
Caso 1: Ejecutas directamente
    > python main.py
    __name__ vale "__main__"  -->  Se ejecuta main()

Caso 2: Otro archivo lo importa
    from main import main
    __name__ vale "main"  -->  NO se ejecuta main() automaticamente
```

### Por que usarlo

Sin esta condicion, si alguien importa tu archivo para usar una funcion,
todo el programa se ejecutaria automaticamente. Con esta condicion,
solo se ejecuta cuando TU quieres.

---

## 22. Docstrings

### Que es

Un texto entre triple comillas que documenta que hace una clase,
metodo o modulo. Lo pones justo debajo de la definicion.

### Sintaxis

```python
# Docstring de modulo (al inicio del archivo)
"""Servicio de aplicacion para la gestion de libros."""


# Docstring de clase
class LibroService:
    """Orquesta las operaciones CRUD de libros."""


# Docstring de metodo
def get_libro(self, libro_id: int) -> Libro:
    """Busca un libro por ID. Lanza error si no existe."""


# Docstring detallado (para modelos)
@dataclass
class Libro:
    """Entidad que representa un libro.

    Attributes:
        titulo: Titulo del libro.
        autor: Nombre del autor.
        isbn: Codigo ISBN unico.
    """
```

### Reglas

| Regla                                     | Ejemplo                              |
|-------------------------------------------|--------------------------------------|
| Primera linea: resumen corto (una oracion) | `"""Busca un libro por ID."""`       |
| Si necesitas mas detalle, linea en blanco  | Ver ejemplo de Libro arriba         |
| Usa comillas triples `"""`                 | No uses `'''` para docstrings       |
| Va DENTRO de la clase/funcion              | Justo debajo de `def` o `class`     |

### Para que sirve

1. Tu editor lo muestra cuando pasas el mouse sobre la funcion
2. `help(mi_funcion)` lo imprime en consola
3. Herramientas como Sphinx generan documentacion automatica

---

## 23. Tuplas de un solo elemento

### El problema

Cuando pasas parametros a `execute()` de SQLite, necesitas una tupla.
Pero una tupla de un solo elemento necesita una coma al final.

### Sintaxis

```python
# Tupla de varios elementos (sin problema)
datos = (libro.titulo, libro.autor, libro.isbn)

# Tupla de UN solo elemento (necesita la coma)
datos = (libro_id,)           # CORRECTO: es una tupla

# Sin la coma NO es una tupla
datos = (libro_id)            # INCORRECTO: es solo un parentesis, no tupla
```

### Donde aparece en el proyecto

```python
# Buscar por ID: un solo parametro
row = self._conn.execute(sql, (libro_id,)).fetchone()
#                                      ^ Esta coma es OBLIGATORIA

# Insertar: varios parametros (la coma final es opcional)
cursor = self._conn.execute(sql, (libro.titulo, libro.autor, libro.isbn))
```

### Error comun

```python
# MAL: falta la coma, Python cree que es un entero entre parentesis
self._conn.execute("SELECT * FROM libros WHERE id = ?", (5))
# TypeError: no se puede iterar un entero

# BIEN: con la coma, Python sabe que es una tupla
self._conn.execute("SELECT * FROM libros WHERE id = ?", (5,))
```

---

## 24. Operador walrus :=

### Que es

Asigna un valor a una variable Y lo usa en la misma linea.
Se llama "walrus" (morsa) porque `:=` parece los ojos y colmillos
de una morsa.

### Sintaxis

```python
# Sin walrus (dos lineas):
valor = input("Dato: ").strip()
if valor:
    print(f"Escribiste: {valor}")

# Con walrus (una linea):
if valor := input("Dato: ").strip():
    print(f"Escribiste: {valor}")
```

### Uso tipico en lectura

```python
# Sin walrus:
fila = cursor.fetchone()
if fila is not None:
    return self._row_to_entity(fila)

# Con walrus:
if (fila := cursor.fetchone()) is not None:
    return self._row_to_entity(fila)
```

### Cuando usarlo

Solo cuando hace el codigo MAS LEGIBLE, no menos.
Si la linea queda compleja, mejor usar dos lineas.
Es una herramienta opcional, no obligatoria.

---

## 25. Enum

### Que es

Una clase que define un conjunto FIJO de opciones.
Cada opcion tiene un nombre y un valor.

### Sintaxis

```python
from enum import Enum

class EstadoLibro(Enum):
    DISPONIBLE = "disponible"
    PRESTADO = "prestado"
    EN_REPARACION = "en_reparacion"
```

### Uso

```python
libro.estado = EstadoLibro.DISPONIBLE

if libro.estado == EstadoLibro.PRESTADO:
    print("Este libro esta prestado.")

# Obtener el valor texto
print(libro.estado.value)        # "disponible"

# Obtener el nombre
print(libro.estado.name)         # "DISPONIBLE"
```

### Para que sirve

Evita errores de tipeo. Sin Enum:

```python
# MAL: puedes escribir cualquier cosa
libro.estado = "Disponibl"       # Typo, nadie lo detecta
libro.estado = "xyz"             # Valor inventado, sin error

# BIEN con Enum: solo valores permitidos
libro.estado = EstadoLibro.DISPONIBLE    # Solo estas opciones existen
libro.estado = EstadoLibro.XYZ           # ERROR inmediato
```

---

## 26. slots

### Que es

Una optimizacion que le dice a Python: "esta clase solo tiene
ESTOS campos, nada mas". Usa menos memoria y es mas rapido.

### Sintaxis

```python
@dataclass(slots=True)
class Libro:
    titulo: str
    autor: str
```

### Que efecto tiene

```python
# CON slots=True:
libro = Libro(titulo="Test", autor="Ana")
libro.nuevo_campo = "sorpresa"     # ERROR: no puedes agregar campos nuevos

# SIN slots:
libro.nuevo_campo = "sorpresa"     # Funciona pero no deberia existir
```

### Cuando usarlo

Siempre que puedas. La regla simple: ponlo en todas tus dataclasses.

```python
@dataclass(slots=True)                  # Entidad mutable
@dataclass(frozen=True, slots=True)     # Value Object inmutable
```

---

## 27. Tabla resumen rapida

### Elementos de clase

| Elemento              | Para que sirve                            | Se usa en...            |
|-----------------------|-------------------------------------------|-------------------------|
| `@dataclass`          | Generar __init__ automatico               | Modelos, DTOs           |
| `frozen=True`         | Hacer la clase inmutable                  | Value Objects, DTOs     |
| `slots=True`          | Optimizar memoria                         | Todas las dataclasses   |
| `__post_init__`       | Validar al crear el objeto                | Modelos                 |
| `__init__`            | Constructor manual                        | Servicios, CLIs, Repos  |
| `super()`             | Llamar al constructor del padre           | Excepciones             |
| `ABC`                 | Crear interfaz abstracta                  | Puertos                 |
| `@abstractmethod`     | Obligar a implementar un metodo           | Puertos                 |
| `@staticmethod`       | Metodo sin acceso a self                  | Repos (_row_to_entity)  |
| `@property`           | Campo calculado                           | Modelos (si necesitas)  |
| `ClassVar`            | Variable compartida de clase              | Constantes en modelos   |
| `Enum`                | Opciones fijas                            | Estados, tipos          |

### Manejo de errores

| Elemento              | Para que sirve                            | Se usa en...            |
|-----------------------|-------------------------------------------|-------------------------|
| `raise`               | Lanzar un error                           | Servicios, Repos        |
| `try/except`          | Atrapar un error                          | CLI, Repos              |
| `finally`             | Ejecutar siempre (limpieza)               | main.py                 |
| `as exc`              | Guardar el error en variable              | CLIs                    |

### Tipos y anotaciones

| Elemento              | Para que sirve                            | Se usa en...            |
|-----------------------|-------------------------------------------|-------------------------|
| Type Hints            | Indicar tipos de datos                    | Todo el proyecto        |
| `Optional[X]`         | Puede ser X o None                        | Retornos, parametros    |
| `X \| None`           | Igual que Optional (moderno)              | Retornos, parametros    |
| `-> None`             | La funcion no devuelve nada               | delete, __init__        |
| `from __future__`     | Compatibilidad de tipos                   | Inicio de cada archivo  |

### Datos y colecciones

| Elemento              | Para que sirve                            | Se usa en...            |
|-----------------------|-------------------------------------------|-------------------------|
| List comprehension    | Crear lista transformada                  | Repos (get_all)         |
| `.get()`              | Buscar en diccionario sin error           | CLIs (despacho)         |
| f-string              | Texto con variables                       | Todo el proyecto        |
| `.strip()`            | Limpiar espacios                          | CLIs, __post_init__     |
| `.isdigit()`          | Verificar si es numero                    | CLIs                    |
| `(valor,)`            | Tupla de un elemento                      | SQL con execute()       |

### Testing

| Elemento              | Para que sirve                            | Se usa en...            |
|-----------------------|-------------------------------------------|-------------------------|
| `@pytest.fixture`     | Preparar datos para tests                 | Tests de integracion    |
| `yield`               | Pausar fixture, limpiar despues           | Fixtures                |
| `pytest.raises`       | Verificar que un error se lance           | Tests negativos         |
| `match="texto"`       | Verificar mensaje del error               | Tests negativos         |

### Estructura

| Elemento              | Para que sirve                            | Se usa en...            |
|-----------------------|-------------------------------------------|-------------------------|
| `__name__ == "__main__"`| Solo ejecutar si es el archivo principal| main.py                 |
| `Path`                | Rutas de archivos                         | main.py, conexion BD    |
| `with`                | Abrir y cerrar recursos                   | Archivos, conexiones    |
| docstrings            | Documentar clases y funciones             | Todo el proyecto        |
