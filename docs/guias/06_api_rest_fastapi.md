# Guia: API REST con FastAPI - De la Consola al Mundo Real

Tu aplicacion de consola funciona, pero solo la puedes usar tu
en tu computadora. Una API permite que CUALQUIER programa
(una web, una app movil, otro servidor) use tu sistema
a traves de internet. Esta guia te lleva paso a paso
usando el mismo ejemplo de Biblioteca.

---

## Indice

1. [Que es una API y por que la necesitas](#1-que-es-una-api-y-por-que-la-necesitas)
2. [HTTP: el idioma de internet](#2-http-el-idioma-de-internet)
3. [Que es un endpoint](#3-que-es-un-endpoint)
4. [Que es REST](#4-que-es-rest)
5. [Que es JSON](#5-que-es-json)
6. [FastAPI: que es y por que usarlo](#6-fastapi-que-es-y-por-que-usarlo)
7. [Instalacion y primer servidor](#7-instalacion-y-primer-servidor)
8. [Donde encaja la API en la arquitectura hexagonal](#8-donde-encaja-la-api-en-la-arquitectura-hexagonal)
9. [Paso 1: Schemas (lo que recibe y devuelve la API)](#9-paso-1-schemas)
10. [Paso 2: El primer endpoint (GET)](#10-paso-2-el-primer-endpoint-get)
11. [Paso 3: Endpoint para crear (POST)](#11-paso-3-endpoint-para-crear-post)
12. [Paso 4: Endpoint para buscar uno (GET con parametro)](#12-paso-4-endpoint-para-buscar-uno)
13. [Paso 5: Endpoint para actualizar (PUT)](#13-paso-5-endpoint-para-actualizar-put)
14. [Paso 6: Endpoint para eliminar (DELETE)](#14-paso-6-endpoint-para-eliminar-delete)
15. [Paso 7: Manejo de errores en la API](#15-paso-7-manejo-de-errores-en-la-api)
16. [Paso 8: El router completo de libros](#16-paso-8-el-router-completo-de-libros)
17. [Paso 9: main.py para la API](#17-paso-9-mainpy-para-la-api)
18. [Paso 10: Probar la API](#18-paso-10-probar-la-api)
19. [Codigos de estado HTTP](#19-codigos-de-estado-http)
20. [Paso 11: Endpoint de reportes](#20-paso-11-endpoint-de-reportes)
21. [Que es CORS y por que importa](#21-que-es-cors-y-por-que-importa)
22. [Estructura completa del proyecto con API](#22-estructura-completa-del-proyecto-con-api)
23. [Paso 12: Dependency Injection en FastAPI](#23-paso-12-dependency-injection-en-fastapi)
24. [Paso 13: Tests de la API](#24-paso-13-tests-de-la-api)
25. [Comparacion: CLI vs API](#25-comparacion-cli-vs-api)
26. [Errores comunes al hacer APIs](#26-errores-comunes-al-hacer-apis)
27. [Referencia rapida de FastAPI](#27-referencia-rapida-de-fastapi)
28. [Tu arsenal completo](#28-tu-arsenal-completo)

---

## 1. Que es una API y por que la necesitas

### Analogia

Tu aplicacion de consola es como un restaurante que solo atiende
en mostrador. Tu llegas, pides y te dan la comida. Nadie mas puede pedir.

Una API es como poner un servicio de delivery. Ahora cualquiera puede
llamar por telefono (hacer una solicitud), pedir algo del menu
(un endpoint), y recibir la comida en su casa (la respuesta).

### Definicion simple

API = Application Programming Interface
(Interfaz de Programacion de Aplicaciones)

Es un CONTRATO que dice:
- "Si me mandas ESTO a ESTA direccion..."
- "...yo te devuelvo ESTO."

### Ejemplo concreto

```
SIN API (tu aplicacion de consola):
  Tu --> Consola --> Servicio --> BD

CON API (tu aplicacion disponible para todos):
  Pagina web    --\
  App movil     ---+--> API --> Servicio --> BD
  Otro servidor --/
  Tu consola    --/
```

La API es la PUERTA DE ENTRADA. Cualquier programa que sepa
hablar HTTP puede usarla.

### Por que la necesitas

| Sin API                              | Con API                                |
|--------------------------------------|----------------------------------------|
| Solo funciona en tu computadora      | Funciona desde cualquier lugar         |
| Solo la consola puede usar los datos | Una web, app o script puede usarlos    |
| Un solo usuario a la vez             | Multiples usuarios simultaneos         |
| No se puede compartir                | Cualquiera con acceso puede usarla     |

---

## 2. HTTP: el idioma de internet

### Que es

HTTP (HyperText Transfer Protocol) es el idioma que usan
los navegadores, apps y servidores para comunicarse.

Cuando escribes `google.com` en tu navegador, tu navegador
le manda un MENSAJE HTTP a Google, y Google le responde
con otro MENSAJE HTTP que contiene la pagina.

### Un mensaje HTTP tiene 3 partes

```
1. METODO + URL      --> Que quieres hacer y donde
   GET /libros

2. HEADERS           --> Informacion extra (formato, autenticacion, etc.)
   Content-Type: application/json

3. BODY              --> Los datos (solo en POST y PUT)
   {"titulo": "Don Quijote", "autor": "Cervantes", "isbn": "1234567890123"}
```

### Los 4 metodos HTTP que necesitas (los otros no importan por ahora)

| Metodo   | Que significa      | Equivalente CRUD | Ejemplo                    |
|----------|--------------------|-------------------|----------------------------|
| `GET`    | Dame informacion   | Read              | Dame todos los libros      |
| `POST`   | Crea algo nuevo    | Create            | Registra este libro nuevo  |
| `PUT`    | Actualiza algo     | Update            | Cambia los datos de este libro |
| `DELETE` | Elimina algo       | Delete            | Borra este libro           |

### Analogia con el restaurante

```
GET     = "Muestrame el menu"             (solo miras, no cambias nada)
POST    = "Quiero hacer un nuevo pedido"  (creas algo nuevo)
PUT     = "Cambia mi pedido por este otro" (modificas algo existente)
DELETE  = "Cancela mi pedido"             (eliminas algo)
```

---

## 3. Que es un endpoint

### Definicion

Un endpoint es una DIRECCION ESPECIFICA de tu API que hace UNA cosa.
Es la combinacion de un METODO HTTP + una URL.

### Ejemplo: API de la biblioteca

| Endpoint                    | Que hace                        |
|-----------------------------|---------------------------------|
| `GET    /libros`            | Listar todos los libros         |
| `GET    /libros/5`          | Buscar el libro con ID 5        |
| `POST   /libros`            | Crear un libro nuevo            |
| `PUT    /libros/5`          | Actualizar el libro con ID 5    |
| `DELETE /libros/5`          | Eliminar el libro con ID 5      |

### Partes de un endpoint

```
GET  /libros/5
 |      |    |
 |      |    Parametro de ruta (el ID del libro)
 |      Recurso (de que estamos hablando: libros)
 Metodo HTTP (que quieres hacer)
```

### La URL completa

```
http://localhost:8000/libros/5
  |        |      |     |    |
  |        |      |     |    ID del libro
  |        |      |     Recurso
  |        |      Puerto (la puerta del servidor)
  |        Direccion del servidor (tu computadora)
  Protocolo
```

`localhost` = tu propia computadora.
`8000` = el puerto donde tu API esta escuchando.
En produccion seria algo como `https://mi-api.com/libros/5`.

---

## 4. Que es REST

### Definicion simple

REST es un ESTILO de disenar APIs. No es una tecnologia,
es un conjunto de REGLAS sobre como nombrar y organizar
tus endpoints.

### Las reglas de REST (solo las que necesitas)

**Regla 1: Los endpoints son SUSTANTIVOS, no verbos**

```
BIEN (sustantivo):
  GET /libros          "Dame los libros"
  POST /libros         "Crea un libro"

MAL (verbo):
  GET /obtenerLibros
  POST /crearLibro
```

**Regla 2: Plural para colecciones, singular con ID**

```
/libros          --> La coleccion de TODOS los libros
/libros/5        --> UN libro especifico (el 5)
```

**Regla 3: El metodo HTTP indica la accion**

No necesitas poner la accion en la URL porque el metodo ya lo dice:

```
GET /libros       --> LEER (el metodo dice "dame")
POST /libros      --> CREAR (el metodo dice "crea")
PUT /libros/5     --> ACTUALIZAR (el metodo dice "cambia")
DELETE /libros/5  --> ELIMINAR (el metodo dice "borra")
```

**Regla 4: Responder con codigos de estado HTTP**

```
200 = OK, todo salio bien
201 = Creado exitosamente
404 = No se encontro
422 = Los datos que mandaste estan mal
500 = Error interno del servidor
```

**Regla 5: Los datos viajan en formato JSON**

---

## 5. Que es JSON

### Definicion

JSON (JavaScript Object Notation) es un formato de TEXTO
para representar datos. Es el idioma universal entre APIs.

### Sintaxis

```json
{
    "titulo": "Don Quijote",
    "autor": "Cervantes",
    "isbn": "1234567890123",
    "disponible": true,
    "id": 1
}
```

### Paralelo con Python

| JSON              | Python              | Tipo              |
|-------------------|---------------------|-------------------|
| `"texto"`         | `"texto"`           | String            |
| `42`              | `42`                | Entero            |
| `3.14`            | `3.14`              | Float             |
| `true` / `false`  | `True` / `False`    | Booleano          |
| `null`            | `None`              | Nulo              |
| `[1, 2, 3]`       | `[1, 2, 3]`        | Lista             |
| `{"a": 1}`        | `{"a": 1}`          | Diccionario       |

### JSON es lo que tu API recibe y devuelve

```
El cliente (web, app) manda JSON:
  {"titulo": "Don Quijote", "autor": "Cervantes", "isbn": "1234567890123"}

Tu API responde con JSON:
  {"id": 1, "titulo": "Don Quijote", "autor": "Cervantes", "isbn": "1234567890123", "disponible": true}
```

---

## 6. FastAPI: que es y por que usarlo

### Que es

FastAPI es un framework de Python para crear APIs.
Es el mas moderno, el mas rapido y el mas facil de usar.

### Por que FastAPI y no Flask u otro

| Caracteristica           | FastAPI           | Flask             |
|--------------------------|-------------------|-------------------|
| Velocidad                | Muy rapida        | Mas lenta         |
| Documentacion automatica | SI (Swagger UI)   | No (hay que agregar) |
| Validacion de datos      | Automatica        | Manual            |
| Type Hints               | Los usa para todo | No los usa        |
| Async/await              | Nativo            | Limitado          |
| Curva de aprendizaje     | Facil             | Facil             |

La ventaja asesina: FastAPI genera una PAGINA DE DOCUMENTACION
INTERACTIVA automaticamente. Puedes probar tu API desde el navegador
sin instalar nada.

---

## 7. Instalacion y primer servidor

### Instalar

```
pip install fastapi uvicorn
```

- `fastapi` = el framework que crea la API
- `uvicorn` = el servidor que la ejecuta (como el "motor" que la mantiene encendida)

### Agregar al requirements.txt

```
pytest>=7.0
matplotlib>=3.7
fastapi>=0.100
uvicorn>=0.23
```

### Tu primer servidor (3 lineas)

```python
"""Mi primera API."""

from fastapi import FastAPI

app = FastAPI(title="Biblioteca API")


@app.get("/")
def raiz():
    return {"mensaje": "La API esta funcionando"}
```

### Ejecutar

```
uvicorn main:app --reload
```

- `main` = nombre del archivo (main.py)
- `app` = nombre de la variable FastAPI
- `--reload` = reinicia automaticamente cuando cambias el codigo

### Que pasa

```
1. uvicorn arranca el servidor en http://localhost:8000
2. Tu navegador o cualquier programa puede hacer solicitudes
3. Si entras a http://localhost:8000/  ves: {"mensaje": "La API esta funcionando"}
4. Si entras a http://localhost:8000/docs  ves la DOCUMENTACION INTERACTIVA
```

La pagina `/docs` es GRATIS. FastAPI la genera sola a partir de tu codigo.
Ahi puedes probar cada endpoint sin escribir nada extra.

---

## 8. Donde encaja la API en la arquitectura hexagonal

La API es OTRA CAPA DE INFRAESTRUCTURA. Reemplaza (o complementa)
el CLI. Todo lo demas queda EXACTAMENTE igual.

```
ANTES (solo consola):
  CLI --> Servicio --> Repositorio --> BD

AHORA (consola + API):
  CLI --------\
               +--> Servicio --> Repositorio --> BD
  API (FastAPI)/

El servicio no sabe ni le importa quien lo llama.
Puede ser el CLI, la API, o un test. Es el mismo codigo.
```

### Estructura de directorios

```
src/mi_app/
    domain/                     <-- NO CAMBIA
        models/
        ports/
        exceptions.py

    application/                <-- NO CAMBIA
        dto/
        services/

    infrastructure/
        persistence/            <-- NO CAMBIA
            sqlite_connection.py
            sqlite_libro_repository.py
        cli/                    <-- YA EXISTIA
            main_menu.py
            libro_cli.py
        api/                    <-- NUEVO (toda la API va aqui)
            schemas/
                libro_schema.py
            routers/
                libro_router.py
            dependencies.py
            error_handlers.py
```

### La regla clave

**Los routers de la API hacen lo MISMO que el CLI:**

```
CLI:      input() --> DTO --> servicio --> print()
API:      JSON    --> DTO --> servicio --> JSON
```

La unica diferencia es DE DONDE vienen los datos
y HACIA DONDE van los resultados.

---

## 9. Paso 1: Schemas

### Que es un schema

Un schema define la FORMA que tienen los datos que entran y salen
de la API. Es como un formulario que dice: "para crear un libro,
necesito estos campos con estos tipos".

FastAPI usa Pydantic para los schemas. Pydantic valida los datos
AUTOMATICAMENTE. Si alguien manda un titulo que no es string,
Pydantic rechaza la solicitud sin que tu escribas una linea de validacion.

### Diferencia entre DTO y Schema

```
DTO:     Paquete de datos DENTRO de tu aplicacion (entre capas)
Schema:  Paquete de datos hacia AFUERA de tu aplicacion (hacia el cliente)

Son parecidos pero no iguales. El schema puede tener reglas de formato
(longitud minima, patron regex) que el DTO no necesita.
```

### Plantilla de schemas

```python
"""Schemas de la API para la entidad Libro."""

from __future__ import annotations

from pydantic import BaseModel, Field


class LibroCreate(BaseModel):
    """Lo que el cliente manda para CREAR un libro.

    Ejemplo de JSON que recibe:
    {
        "titulo": "Don Quijote",
        "autor": "Cervantes",
        "isbn": "1234567890123"
    }
    """

    titulo: str = Field(
        ...,                             # ... significa OBLIGATORIO
        min_length=1,                    # Minimo 1 caracter
        max_length=200,                  # Maximo 200 caracteres
        examples=["Don Quijote"],        # Ejemplo para la documentacion
    )
    autor: str = Field(
        ...,
        min_length=1,
        max_length=100,
        examples=["Cervantes"],
    )
    isbn: str = Field(
        ...,
        min_length=13,
        max_length=13,
        examples=["1234567890123"],
    )


class LibroUpdate(BaseModel):
    """Lo que el cliente manda para ACTUALIZAR un libro.

    Ejemplo de JSON que recibe:
    {
        "titulo": "Don Quijote de la Mancha",
        "autor": "Miguel de Cervantes",
        "isbn": "1234567890123"
    }
    """

    titulo: str = Field(..., min_length=1, max_length=200)
    autor: str = Field(..., min_length=1, max_length=100)
    isbn: str = Field(..., min_length=13, max_length=13)


class LibroResponse(BaseModel):
    """Lo que la API DEVUELVE al cliente.

    Ejemplo de JSON que devuelve:
    {
        "id": 1,
        "titulo": "Don Quijote",
        "autor": "Cervantes",
        "isbn": "1234567890123",
        "disponible": true
    }
    """

    id: int
    titulo: str
    autor: str
    isbn: str
    disponible: bool

    class Config:
        from_attributes = True           # Permite crear desde un objeto (dataclass)


class ErrorResponse(BaseModel):
    """Formato estandar para errores.

    Ejemplo:
    {
        "detail": "No se encontro el libro con ID 99."
    }
    """

    detail: str
```

### Que es Field

`Field` agrega validacion y documentacion a cada campo:

| Parametro       | Que hace                           | Ejemplo                |
|-----------------|------------------------------------|------------------------|
| `...`           | Campo obligatorio                  | No puede faltar        |
| `None`          | Campo opcional                     | Puede no venir         |
| `min_length`    | Longitud minima (strings)          | `min_length=1`         |
| `max_length`    | Longitud maxima (strings)          | `max_length=200`       |
| `gt`            | Mayor que (numeros)                | `gt=0`                 |
| `ge`            | Mayor o igual que                  | `ge=0`                 |
| `lt`            | Menor que                          | `lt=1000`              |
| `le`            | Menor o igual que                  | `le=999`               |
| `examples`      | Ejemplos para la documentacion     | `examples=["texto"]`   |
| `description`   | Descripcion del campo              | `description="El titulo"` |

### Que es BaseModel

`BaseModel` es la clase base de Pydantic. Funciona parecido a `@dataclass`
pero con superpoderes:

```
@dataclass:     Solo define campos
BaseModel:      Define campos + valida automaticamente + convierte a JSON
```

### Que es from_attributes = True

Permite crear un schema a partir de un objeto Python normal:

```python
# Tu modelo de dominio (dataclass):
libro = Libro(id=1, titulo="Test", autor="Ana", isbn="1234567890123", disponible=True)

# Convertir a schema de respuesta (para devolverlo como JSON):
respuesta = LibroResponse.model_validate(libro)
# Resultado: LibroResponse(id=1, titulo="Test", autor="Ana", ...)
```

Sin `from_attributes = True`, esa conversion no funciona.

---

## 10. Paso 2: El primer endpoint (GET)

### Listar todos los libros

```python
"""Router de la API para la entidad Libro."""

from __future__ import annotations

from fastapi import APIRouter

from src.mi_app.application.services.libro_service import LibroService
from src.mi_app.infrastructure.api.schemas.libro_schema import LibroResponse

router = APIRouter(prefix="/libros", tags=["Libros"])


@router.get("/", response_model=list[LibroResponse])
def listar_libros(service: LibroService) -> list[LibroResponse]:
    """Devuelve todos los libros registrados."""
    libros = service.list_libros()
    return [LibroResponse.model_validate(libro) for libro in libros]
```

### Que hace cada parte

```python
router = APIRouter(prefix="/libros", tags=["Libros"])
#                   |                  |
#                   |                  Grupo en la documentacion
#                   Todas las rutas empiezan con /libros

@router.get("/", response_model=list[LibroResponse])
#       |    |    |
#       |    |    Formato de la respuesta (para la documentacion)
#       |    Ruta relativa (/ = la raiz del prefijo = /libros)
#       Metodo HTTP

def listar_libros(service: LibroService) -> list[LibroResponse]:
#   |              |
#   |              Parametro inyectado (explicado en Paso 12)
#   Nombre de la funcion (se muestra en la documentacion)
```

### Que devuelve

Si tienes 2 libros en la BD, la API responde con:

```json
[
    {
        "id": 1,
        "titulo": "Don Quijote",
        "autor": "Cervantes",
        "isbn": "1234567890123",
        "disponible": true
    },
    {
        "id": 2,
        "titulo": "Cien Anos de Soledad",
        "autor": "Garcia Marquez",
        "isbn": "9876543210123",
        "disponible": false
    }
]
```

---

## 11. Paso 3: Endpoint para crear (POST)

```python
from fastapi import APIRouter, status

from src.mi_app.application.dto.libro_dto import CreateLibroDTO
from src.mi_app.infrastructure.api.schemas.libro_schema import (
    LibroCreate,
    LibroResponse,
)


@router.post("/", response_model=LibroResponse, status_code=status.HTTP_201_CREATED)
def crear_libro(body: LibroCreate, service: LibroService) -> LibroResponse:
    """Registra un libro nuevo."""
    dto = CreateLibroDTO(titulo=body.titulo, autor=body.autor, isbn=body.isbn)
    libro = service.register_libro(dto)
    return LibroResponse.model_validate(libro)
```

### Que pasa paso a paso

```
1. El cliente manda un POST a /libros con este JSON:
   {"titulo": "Hamlet", "autor": "Shakespeare", "isbn": "1111111111111"}

2. FastAPI recibe el JSON y lo convierte en un objeto LibroCreate
   body = LibroCreate(titulo="Hamlet", autor="Shakespeare", isbn="1111111111111")

3. Si el JSON tiene campos invalidos (isbn de 5 caracteres),
   FastAPI RECHAZA la solicitud automaticamente con error 422.
   Tu funcion NUNCA se ejecuta.

4. Si el JSON es valido, tu funcion se ejecuta:
   - Empaqueta en DTO:   dto = CreateLibroDTO(titulo=..., autor=..., isbn=...)
   - Llama al servicio:  libro = service.register_libro(dto)
   - Convierte a JSON:   return LibroResponse.model_validate(libro)

5. FastAPI envia la respuesta con codigo 201 (Creado):
   {"id": 3, "titulo": "Hamlet", "autor": "Shakespeare", "isbn": "1111111111111", "disponible": true}
```

### body: de donde sale

Cuando un parametro de la funcion tiene tipo `BaseModel` (como `LibroCreate`),
FastAPI automaticamente entiende que viene del BODY (el cuerpo) de la solicitud.
Es decir, del JSON que el cliente manda.

```python
def crear_libro(body: LibroCreate, ...):
#               |
#               FastAPI sabe que esto viene del JSON
#               porque LibroCreate hereda de BaseModel
```

---

## 12. Paso 4: Endpoint para buscar uno

```python
from fastapi import APIRouter, HTTPException, status


@router.get("/{libro_id}", response_model=LibroResponse)
def obtener_libro(libro_id: int, service: LibroService) -> LibroResponse:
    """Busca un libro por su ID."""
    libro = service.get_libro(libro_id)
    return LibroResponse.model_validate(libro)
```

### Que es {libro_id} en la ruta

Es un PARAMETRO DE RUTA. FastAPI lo extrae de la URL automaticamente.

```
Solicitud:  GET /libros/5
                        |
                        libro_id = 5 (FastAPI lo extrae y lo pasa a la funcion)
```

La funcion recibe `libro_id: int`. FastAPI convierte "5" (texto) a 5 (entero)
automaticamente. Si alguien pone `/libros/abc`, FastAPI rechaza con error 422.

### Y si el libro no existe?

El servicio lanza `LibroNotFoundError`. FastAPI no sabe que hacer con eso
por defecto (daria error 500). Por eso necesitamos el manejo de errores
que vemos en el Paso 7.

---

## 13. Paso 5: Endpoint para actualizar (PUT)

```python
from src.mi_app.application.dto.libro_dto import UpdateLibroDTO
from src.mi_app.infrastructure.api.schemas.libro_schema import (
    LibroUpdate,
    LibroResponse,
)


@router.put("/{libro_id}", response_model=LibroResponse)
def actualizar_libro(
    libro_id: int,
    body: LibroUpdate,
    service: LibroService,
) -> LibroResponse:
    """Actualiza los datos de un libro existente."""
    dto = UpdateLibroDTO(id=libro_id, titulo=body.titulo, autor=body.autor, isbn=body.isbn)
    libro = service.update_libro(dto)
    return LibroResponse.model_validate(libro)
```

### Que recibe esta funcion

```python
def actualizar_libro(
    libro_id: int,         # Viene de la URL:  PUT /libros/5
    body: LibroUpdate,     # Viene del JSON:   {"titulo": "...", "autor": "...", "isbn": "..."}
    service: LibroService, # Inyeccion de dependencia
)
```

FastAPI sabe que:
- `libro_id` viene de la URL porque esta en la ruta `/{libro_id}`
- `body` viene del JSON porque es BaseModel
- `service` es una dependencia inyectada

### Por que el ID va en la URL y NO en el JSON

```
PUT /libros/5
    Body: {"titulo": "Nuevo Titulo", "autor": "Nuevo Autor", "isbn": "1234567890123"}

El ID identifica CUAL recurso modificar (va en la URL).
El body dice CON QUE datos modificarlo (va en el JSON).
Son dos cosas diferentes.
```

---

## 14. Paso 6: Endpoint para eliminar (DELETE)

```python
@router.delete("/{libro_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_libro(libro_id: int, service: LibroService) -> None:
    """Elimina un libro por su ID."""
    service.remove_libro(libro_id)
```

### Por que 204 y no 200

```
200 = OK, aqui te devuelvo datos
204 = OK, hecho, pero no hay nada que devolver

Cuando eliminas, no tiene sentido devolver el libro que ya no existe.
Solo dices "listo, eliminado" con codigo 204 y respuesta vacia.
```

### Por que no devuelve nada

`-> None` y no hay `return`. El codigo 204 significa
"No Content" (sin contenido). La respuesta esta vacia a proposito.

---

## 15. Paso 7: Manejo de errores en la API

En el CLI usabamos `try/except` y `print`. En la API usamos
`exception_handler` que convierte excepciones en respuestas JSON.

### El problema

```python
# Si el servicio lanza LibroNotFoundError y no lo atrapamos,
# FastAPI devuelve un error 500 (Internal Server Error) generico.
# Eso es MALO porque:
# 1. No le dice al cliente que paso realmente
# 2. Parece que el servidor se rompio
```

### La solucion: exception handlers

```python
"""Manejadores de errores para la API."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.mi_app.domain.exceptions import AppDomainError, LibroNotFoundError, DuplicateISBNError


def register_error_handlers(app: FastAPI) -> None:
    """Registra los manejadores de errores en la aplicacion."""

    @app.exception_handler(LibroNotFoundError)
    async def libro_not_found_handler(
        request: Request, exc: LibroNotFoundError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={"detail": str(exc)},
        )

    @app.exception_handler(DuplicateISBNError)
    async def duplicate_isbn_handler(
        request: Request, exc: DuplicateISBNError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={"detail": str(exc)},
        )

    @app.exception_handler(AppDomainError)
    async def domain_error_handler(
        request: Request, exc: AppDomainError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={"detail": str(exc)},
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(
        request: Request, exc: ValueError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={"detail": str(exc)},
        )
```

### Que pasa ahora

```
ANTES (sin handler):
  GET /libros/99  -->  LibroNotFoundError  -->  500 Internal Server Error
                                                (el cliente no sabe que paso)

DESPUES (con handler):
  GET /libros/99  -->  LibroNotFoundError  -->  404 Not Found
                                                {"detail": "No se encontro el libro con ID 99."}
                                                (el cliente sabe exactamente que paso)
```

### Comparacion con el CLI

```
CLI:   except AppDomainError as exc:  print(f"Error: {exc}")
API:   exception_handler(AppDomainError):  return JSONResponse(status_code=400, ...)

Es lo mismo: atrapar el error y responder de forma clara.
Solo cambia el formato de la respuesta (texto vs JSON).
```

---

## 16. Paso 8: El router completo de libros

```python
"""Router de la API para la entidad Libro."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from src.mi_app.application.dto.libro_dto import CreateLibroDTO, UpdateLibroDTO
from src.mi_app.application.services.libro_service import LibroService
from src.mi_app.infrastructure.api.dependencies import get_libro_service
from src.mi_app.infrastructure.api.schemas.libro_schema import (
    LibroCreate,
    LibroResponse,
    LibroUpdate,
)

router = APIRouter(prefix="/libros", tags=["Libros"])


@router.get("/", response_model=list[LibroResponse])
def listar_libros(
    service: LibroService = Depends(get_libro_service),
) -> list[LibroResponse]:
    """Devuelve todos los libros registrados."""
    libros = service.list_libros()
    return [LibroResponse.model_validate(libro) for libro in libros]


@router.get("/{libro_id}", response_model=LibroResponse)
def obtener_libro(
    libro_id: int,
    service: LibroService = Depends(get_libro_service),
) -> LibroResponse:
    """Busca un libro por su ID."""
    libro = service.get_libro(libro_id)
    return LibroResponse.model_validate(libro)


@router.post("/", response_model=LibroResponse, status_code=status.HTTP_201_CREATED)
def crear_libro(
    body: LibroCreate,
    service: LibroService = Depends(get_libro_service),
) -> LibroResponse:
    """Registra un libro nuevo."""
    dto = CreateLibroDTO(titulo=body.titulo, autor=body.autor, isbn=body.isbn)
    libro = service.register_libro(dto)
    return LibroResponse.model_validate(libro)


@router.put("/{libro_id}", response_model=LibroResponse)
def actualizar_libro(
    libro_id: int,
    body: LibroUpdate,
    service: LibroService = Depends(get_libro_service),
) -> LibroResponse:
    """Actualiza los datos de un libro existente."""
    dto = UpdateLibroDTO(id=libro_id, titulo=body.titulo, autor=body.autor, isbn=body.isbn)
    libro = service.update_libro(dto)
    return LibroResponse.model_validate(libro)


@router.delete("/{libro_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_libro(
    libro_id: int,
    service: LibroService = Depends(get_libro_service),
) -> None:
    """Elimina un libro por su ID."""
    service.remove_libro(libro_id)
```

### El patron de cada endpoint (siempre igual)

```
GET (listar):     servicio.list()          --> convertir a schema --> devolver lista
GET (uno):        servicio.get(id)         --> convertir a schema --> devolver uno
POST (crear):     schema --> DTO --> servicio.create(dto) --> convertir --> devolver
PUT (actualizar): schema + id --> DTO --> servicio.update(dto) --> convertir --> devolver
DELETE (eliminar): servicio.delete(id)     --> devolver nada (204)
```

---

## 17. Paso 9: main.py para la API

```python
"""Punto de entrada de la API."""

from fastapi import FastAPI

from src.mi_app.infrastructure.api.error_handlers import register_error_handlers
from src.mi_app.infrastructure.api.routers.libro_router import router as libro_router


def create_app() -> FastAPI:
    """Crea y configura la aplicacion FastAPI."""

    app = FastAPI(
        title="Biblioteca API",
        description="API REST para el sistema de gestion de biblioteca.",
        version="1.0.0",
    )

    # Registrar manejadores de errores
    register_error_handlers(app)

    # Registrar routers
    app.include_router(libro_router)

    return app


app = create_app()
```

### Ejecutar

```
uvicorn src.mi_app.infrastructure.api.main_api:app --reload --port 8000
```

### Ver la documentacion automatica

Abre en tu navegador:
- `http://localhost:8000/docs` --> Swagger UI (interfaz interactiva)
- `http://localhost:8000/redoc` --> ReDoc (documentacion mas formal)

Ambas se generan SOLAS a partir de tu codigo. Cada endpoint,
cada schema, cada descripcion aparece automaticamente.

---

## 18. Paso 10: Probar la API

### Opcion 1: Swagger UI (la mas facil)

Abre `http://localhost:8000/docs` en tu navegador.
Veras todos tus endpoints listados. Para probar uno:

```
1. Haz clic en el endpoint (ej: POST /libros)
2. Haz clic en "Try it out"
3. Escribe el JSON en el campo de texto
4. Haz clic en "Execute"
5. Ves la respuesta abajo (codigo, cuerpo, headers)
```

### Opcion 2: curl (desde la terminal)

```bash
# Listar todos los libros
curl http://localhost:8000/libros

# Buscar un libro por ID
curl http://localhost:8000/libros/1

# Crear un libro
curl -X POST http://localhost:8000/libros \
  -H "Content-Type: application/json" \
  -d '{"titulo": "Don Quijote", "autor": "Cervantes", "isbn": "1234567890123"}'

# Actualizar un libro
curl -X PUT http://localhost:8000/libros/1 \
  -H "Content-Type: application/json" \
  -d '{"titulo": "Don Quijote Editado", "autor": "Cervantes", "isbn": "1234567890123"}'

# Eliminar un libro
curl -X DELETE http://localhost:8000/libros/1
```

### Opcion 3: Python (para scripts o tests)

```python
import requests

BASE_URL = "http://localhost:8000"

# Crear un libro
response = requests.post(
    f"{BASE_URL}/libros",
    json={"titulo": "Don Quijote", "autor": "Cervantes", "isbn": "1234567890123"},
)
print(response.status_code)    # 201
print(response.json())         # {"id": 1, "titulo": "Don Quijote", ...}

# Listar todos
response = requests.get(f"{BASE_URL}/libros")
print(response.json())         # [{"id": 1, ...}, {"id": 2, ...}]

# Buscar uno
response = requests.get(f"{BASE_URL}/libros/1")
print(response.json())         # {"id": 1, "titulo": "Don Quijote", ...}

# Buscar uno que no existe
response = requests.get(f"{BASE_URL}/libros/99")
print(response.status_code)    # 404
print(response.json())         # {"detail": "No se encontro el libro con ID 99."}
```

Para usar `requests` necesitas: `pip install requests`

---

## 19. Codigos de estado HTTP

### Los que necesitas saber

| Codigo | Nombre                 | Cuando usarlo                             |
|--------|------------------------|-------------------------------------------|
| `200`  | OK                     | Todo salio bien, aqui estan los datos     |
| `201`  | Created                | Se creo el recurso exitosamente           |
| `204`  | No Content             | Hecho, pero no hay nada que devolver      |
| `400`  | Bad Request            | La solicitud esta mal formada             |
| `404`  | Not Found              | El recurso no existe                      |
| `409`  | Conflict               | Conflicto (ej: ISBN duplicado)            |
| `422`  | Unprocessable Entity   | Los datos no pasan la validacion          |
| `500`  | Internal Server Error  | Algo se rompio en el servidor             |

### Grupos de codigos (la regla del primer digito)

```
2xx = Todo bien        (200, 201, 204)
3xx = Redireccion      (no los usamos por ahora)
4xx = Error del CLIENTE (el que hizo la solicitud la hizo mal)
5xx = Error del SERVIDOR (algo se rompio internamente)
```

### Que codigo usar en cada endpoint

| Endpoint                  | Exito  | No encontrado | Duplicado | Datos invalidos |
|---------------------------|--------|---------------|-----------|-----------------|
| `GET /libros`             | 200    | --            | --        | --              |
| `GET /libros/{id}`        | 200    | 404           | --        | --              |
| `POST /libros`            | 201    | --            | 409       | 422             |
| `PUT /libros/{id}`        | 200    | 404           | 409       | 422             |
| `DELETE /libros/{id}`     | 204    | 404           | --        | --              |

---

## 20. Paso 11: Endpoint de reportes

Los reportes no son CRUD (no crean, ni actualizan, ni eliminan).
Son endpoints de SOLO LECTURA que devuelven datos procesados.

```python
"""Router de la API para reportes."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from src.mi_app.application.services.reporte_service import ReporteService
from src.mi_app.infrastructure.api.dependencies import get_reporte_service

router = APIRouter(prefix="/reportes", tags=["Reportes"])


@router.get("/disponibilidad")
def reporte_disponibilidad(
    service: ReporteService = Depends(get_reporte_service),
) -> dict[str, int]:
    """Cantidad de libros disponibles vs prestados."""
    return service.reporte_disponibilidad()
    # Respuesta: {"Disponibles": 15, "Prestados": 8}


@router.get("/libros-por-autor")
def reporte_libros_por_autor(
    service: ReporteService = Depends(get_reporte_service),
) -> dict[str, int]:
    """Cantidad de libros agrupados por autor."""
    return service.reporte_libros_por_autor()
    # Respuesta: {"Cervantes": 3, "Borges": 5, "Garcia Marquez": 2}


@router.get("/top-autores")
def reporte_top_autores(
    top: int = 5,
    service: ReporteService = Depends(get_reporte_service),
) -> list[dict[str, str | int]]:
    """Los autores con mas libros."""
    datos = service.reporte_top_autores(top)
    return [{"autor": autor, "cantidad": cantidad} for autor, cantidad in datos]
    # Respuesta: [{"autor": "Borges", "cantidad": 5}, ...]


@router.get("/prestamos-por-mes")
def reporte_prestamos_por_mes(
    service: ReporteService = Depends(get_reporte_service),
) -> dict[str, int]:
    """Prestamos agrupados por mes."""
    return service.reporte_prestamos_por_mes()
    # Respuesta: {"2026-01": 12, "2026-02": 8}


@router.get("/promedio-dias")
def reporte_promedio_dias(
    service: ReporteService = Depends(get_reporte_service),
) -> dict[str, float]:
    """Promedio de dias de duracion de prestamos."""
    promedio = service.reporte_promedio_dias()
    return {"promedio_dias": round(promedio, 1)}
    # Respuesta: {"promedio_dias": 12.5}
```

### Parametros de query (el parametro top)

```python
@router.get("/top-autores")
def reporte_top_autores(top: int = 5):
```

El cliente puede pedir:
- `GET /reportes/top-autores` --> usa el default (top=5)
- `GET /reportes/top-autores?top=10` --> muestra los 10 mejores

Los parametros de query van DESPUES del `?` en la URL.
FastAPI los detecta automaticamente cuando no son parte de la ruta.

```
Parametro de RUTA:   /{libro_id}     --> Va en la URL
Parametro de QUERY:  ?top=10         --> Va despues del ?
Parametro de BODY:   JSON            --> Va en el cuerpo de la solicitud
```

---

## 21. Que es CORS y por que importa

### El problema

Si tu API corre en `localhost:8000` y tu pagina web corre
en `localhost:3000`, el navegador BLOQUEA las solicitudes
de la web a la API por seguridad. Se llama politica de
"mismo origen" (same-origin policy).

### La solucion

CORS (Cross-Origin Resource Sharing) le dice al navegador:
"Esta bien, deja que esa web me haga solicitudes."

```python
from fastapi.middleware.cors import CORSMiddleware


def create_app() -> FastAPI:
    app = FastAPI(title="Biblioteca API")

    # Permitir que un frontend se conecte
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",       # Tu frontend en desarrollo
            "http://localhost:5173",       # Vite (React, Vue, etc.)
        ],
        allow_credentials=True,
        allow_methods=["*"],               # Permitir todos los metodos
        allow_headers=["*"],               # Permitir todos los headers
    )

    register_error_handlers(app)
    app.include_router(libro_router)

    return app
```

### Cuando necesitas CORS

| Situacion                                         | Necesitas CORS? |
|---------------------------------------------------|-----------------|
| Solo pruebas con Swagger UI (/docs)               | NO              |
| Solo pruebas con curl o Python                    | NO              |
| Un frontend web se conecta a tu API               | SI              |
| Una app movil se conecta a tu API                 | NO (solo navegadores) |

### Regla simple

Si tu frontend y tu API estan en DIRECCIONES DIFERENTES,
necesitas CORS. Si estan en la misma, no.

---

## 22. Estructura completa del proyecto con API

```
mi_proyecto/
|-- main.py                              <-- Arranca CLI
|-- requirements.txt
|
|-- src/
|   |-- mi_app/
|       |-- domain/                      <-- NO CAMBIA
|       |   |-- exceptions.py
|       |   |-- models/
|       |   |   |-- libro.py
|       |   |   |-- prestamo.py
|       |   |-- ports/
|       |       |-- libro_repository.py
|       |       |-- prestamo_repository.py
|       |
|       |-- application/                 <-- NO CAMBIA (se agrega reporte_service)
|       |   |-- dto/
|       |   |   |-- libro_dto.py
|       |   |-- services/
|       |       |-- libro_service.py
|       |       |-- reporte_service.py
|       |       |-- data_processing.py
|       |
|       |-- infrastructure/
|           |-- persistence/             <-- NO CAMBIA
|           |   |-- sqlite_connection.py
|           |   |-- sqlite_libro_repository.py
|           |
|           |-- cli/                     <-- YA EXISTIA
|           |   |-- main_menu.py
|           |   |-- libro_cli.py
|           |   |-- reporte_cli.py
|           |
|           |-- graphics/               <-- De la guia anterior
|           |   |-- chart_generator.py
|           |
|           |-- api/                     <-- TODO ESTO ES NUEVO
|               |-- __init__.py
|               |-- main_api.py          <-- Crea la app FastAPI
|               |-- dependencies.py      <-- Inyeccion de dependencias
|               |-- error_handlers.py    <-- Convierte excepciones a JSON
|               |-- schemas/
|               |   |-- __init__.py
|               |   |-- libro_schema.py  <-- Schemas de entrada/salida
|               |-- routers/
|                   |-- __init__.py
|                   |-- libro_router.py  <-- Endpoints de libros
|                   |-- reporte_router.py <-- Endpoints de reportes
|
|-- tests/
|   |-- unit/
|   |-- integration/
|   |-- api/                             <-- NUEVO
|       |-- test_libro_endpoints.py
|
|-- reports/                             <-- Graficos exportados
```

### Que es NUEVO y que NO CAMBIA

```
NO CAMBIA:  domain/ (modelos, puertos, excepciones)
NO CAMBIA:  application/ (DTOs, servicios)
NO CAMBIA:  persistence/ (repositorios SQLite)
NO CAMBIA:  cli/ (menu de consola)

NUEVO:      api/ (schemas, routers, error_handlers, dependencies)
```

Eso demuestra la potencia de la arquitectura hexagonal:
agregar una API completa sin tocar una sola linea del dominio
ni de los servicios.

---

## 23. Paso 12: Dependency Injection en FastAPI

### El problema

Cada endpoint necesita un servicio. El servicio necesita un repositorio.
El repositorio necesita la conexion a la BD. La conexion se crea una vez.

Como hacer que todos los endpoints compartan la misma conexion?

### La solucion: Depends

```python
"""Inyeccion de dependencias para la API."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Generator

from fastapi import Depends

from src.mi_app.application.services.libro_service import LibroService
from src.mi_app.application.services.reporte_service import ReporteService
from src.mi_app.domain.ports.libro_repository import LibroRepository
from src.mi_app.infrastructure.persistence.sqlite_connection import (
    get_connection,
    initialize_database,
)
from src.mi_app.infrastructure.persistence.sqlite_libro_repository import (
    SQLiteLibroRepository,
)

_DB_PATH = Path(__file__).resolve().parent.parent.parent.parent / "app.db"


def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    """Crea una conexion a la BD para cada solicitud."""
    conn = get_connection(_DB_PATH)
    initialize_database(conn)
    try:
        yield conn
    finally:
        conn.close()


def get_libro_repository(
    conn: sqlite3.Connection = Depends(get_db_connection),
) -> SQLiteLibroRepository:
    """Crea el repositorio de libros."""
    return SQLiteLibroRepository(conn)


def get_libro_service(
    repo: LibroRepository = Depends(get_libro_repository),
) -> LibroService:
    """Crea el servicio de libros."""
    return LibroService(repo)


def get_reporte_service(
    libro_repo: LibroRepository = Depends(get_libro_repository),
) -> ReporteService:
    """Crea el servicio de reportes."""
    return ReporteService(libro_repo)
```

### Que hace Depends

`Depends` es la forma de FastAPI de decir "antes de ejecutar esta funcion,
ejecuta ESTA OTRA primero y pasame el resultado".

```
Cuando llega una solicitud a GET /libros:

1. FastAPI ve que listar_libros necesita un LibroService
2. Para crear LibroService, necesita un LibroRepository (Depends)
3. Para crear LibroRepository, necesita una Connection (Depends)
4. Crea la Connection
5. Con la Connection, crea el Repository
6. Con el Repository, crea el Service
7. Llama a listar_libros(service=el_service_que_creo)
8. Cuando termina, cierra la Connection (finally)
```

Es la misma cadena que en main.py del CLI, pero automatica:

```
CLI (main.py manual):
  conn = get_connection()
  repo = SQLiteLibroRepository(conn)
  service = LibroService(repo)
  cli = LibroCLI(service)

API (Depends automatico):
  Depends(get_db_connection) --> Depends(get_libro_repository) --> Depends(get_libro_service)
```

### Comparacion con main.py

| Concepto              | En main.py (CLI)                  | En dependencies.py (API)          |
|-----------------------|-----------------------------------|-----------------------------------|
| Crear conexion        | `conn = get_connection()`          | `Depends(get_db_connection)`      |
| Crear repositorio     | `repo = SQLiteLibroRepo(conn)`     | `Depends(get_libro_repository)`   |
| Crear servicio        | `service = LibroService(repo)`     | `Depends(get_libro_service)`      |
| Cerrar conexion       | `finally: conn.close()`           | `yield` + `finally: conn.close()` |

---

## 24. Paso 13: Tests de la API

FastAPI incluye un TestClient que simula solicitudes sin necesidad
de levantar el servidor real.

```python
"""Tests para los endpoints de libros."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.mi_app.infrastructure.api.main_api import create_app
from src.mi_app.infrastructure.api.dependencies import get_db_connection
from src.mi_app.infrastructure.persistence.sqlite_connection import (
    get_connection,
    initialize_database,
)


@pytest.fixture
def client():
    """Crea un cliente de test con BD en memoria."""

    def override_db():
        conn = get_connection(":memory:")
        initialize_database(conn)
        try:
            yield conn
        finally:
            conn.close()

    app = create_app()
    app.dependency_overrides[get_db_connection] = override_db

    with TestClient(app) as c:
        yield c


class TestLibroEndpoints:

    def test_listar_vacio(self, client):
        response = client.get("/libros")
        assert response.status_code == 200
        assert response.json() == []

    def test_crear_libro(self, client):
        response = client.post("/libros", json={
            "titulo": "Don Quijote",
            "autor": "Cervantes",
            "isbn": "1234567890123",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == 1
        assert data["titulo"] == "Don Quijote"
        assert data["disponible"] is True

    def test_crear_libro_isbn_corto(self, client):
        response = client.post("/libros", json={
            "titulo": "Test",
            "autor": "Test",
            "isbn": "123",
        })
        assert response.status_code == 422    # Validacion de Pydantic

    def test_obtener_libro(self, client):
        # Primero crear
        client.post("/libros", json={
            "titulo": "Test",
            "autor": "Autor",
            "isbn": "1234567890123",
        })
        # Luego buscar
        response = client.get("/libros/1")
        assert response.status_code == 200
        assert response.json()["titulo"] == "Test"

    def test_obtener_libro_no_existe(self, client):
        response = client.get("/libros/99")
        assert response.status_code == 404
        assert "No se encontro" in response.json()["detail"]

    def test_actualizar_libro(self, client):
        # Crear
        client.post("/libros", json={
            "titulo": "Original",
            "autor": "Autor",
            "isbn": "1234567890123",
        })
        # Actualizar
        response = client.put("/libros/1", json={
            "titulo": "Modificado",
            "autor": "Autor",
            "isbn": "1234567890123",
        })
        assert response.status_code == 200
        assert response.json()["titulo"] == "Modificado"

    def test_eliminar_libro(self, client):
        # Crear
        client.post("/libros", json={
            "titulo": "Test",
            "autor": "Autor",
            "isbn": "1234567890123",
        })
        # Eliminar
        response = client.delete("/libros/1")
        assert response.status_code == 204

        # Verificar que ya no existe
        response = client.get("/libros/1")
        assert response.status_code == 404

    def test_crear_isbn_duplicado(self, client):
        libro = {
            "titulo": "Test",
            "autor": "Autor",
            "isbn": "1234567890123",
        }
        client.post("/libros", json=libro)
        response = client.post("/libros", json=libro)
        assert response.status_code == 409
        assert "ISBN" in response.json()["detail"]
```

### Que es dependency_overrides

```python
app.dependency_overrides[get_db_connection] = override_db
```

Le dice a FastAPI: "Cuando alguien pida `get_db_connection`,
en vez de usar la funcion real, usa `override_db`."

Esto permite que los tests usen una BD en memoria (`:memory:`)
en vez de la BD real. Asi los tests no afectan tus datos reales.

### Como ejecutar los tests

```
pytest tests/api/ -v
```

---

## 25. Comparacion: CLI vs API

### El mismo CRUD, dos presentaciones

| Aspecto           | CLI (consola)                    | API (FastAPI)                     |
|-------------------|----------------------------------|-----------------------------------|
| Entrada de datos  | `input("Titulo: ")`              | JSON en el body                   |
| Salida de datos   | `print(f"Titulo: {titulo}")`     | JSON en la respuesta              |
| Navegacion        | Menu con numeros                 | URLs con metodos HTTP             |
| Errores           | `print(f"Error: {exc}")`         | JSON con status code              |
| Validacion        | `if not titulo: print("...")`    | Pydantic valida automaticamente   |
| Documentacion     | No tiene                         | Swagger UI automatica             |
| Usuarios          | Uno (tu)                         | Multiples simultaneos             |
| Donde se usa      | Solo tu computadora              | Cualquier lugar con internet      |

### Lo que NO cambia

```
domain/         --> EXACTAMENTE IGUAL
application/    --> EXACTAMENTE IGUAL
persistence/    --> EXACTAMENTE IGUAL

Lo unico nuevo es la carpeta api/ en infrastructure.
Eso prueba que la arquitectura hexagonal funciona.
```

---

## 26. Errores comunes al hacer APIs

### Error 1: devolver el modelo de dominio directamente

```python
# MAL: expones la estructura interna al mundo
@router.get("/libros")
def listar(service):
    return service.list_libros()     # Devuelve objetos Libro tal cual

# BIEN: convertir a schema de respuesta
@router.get("/libros", response_model=list[LibroResponse])
def listar(service):
    libros = service.list_libros()
    return [LibroResponse.model_validate(libro) for libro in libros]
```

Por que importa: si manana cambias la estructura interna del modelo,
no quieres que eso rompa las apps que usan tu API.

### Error 2: no manejar errores de dominio

```python
# MAL: el servicio lanza LibroNotFoundError y la API devuelve 500
@router.get("/{libro_id}")
def obtener(libro_id: int, service):
    return service.get_libro(libro_id)    # Si no existe: 500? 404?

# BIEN: registrar exception_handler para que devuelva 404
```

### Error 3: usar GET para crear o eliminar

```python
# MAL:
@router.get("/crear-libro")     # GET es para LEER, no para crear
@router.get("/eliminar/5")      # GET es para LEER, no para eliminar

# BIEN:
@router.post("/libros")         # POST para crear
@router.delete("/libros/5")     # DELETE para eliminar
```

### Error 4: poner logica de negocio en el router

```python
# MAL: el router hace calculos y validaciones
@router.post("/libros")
def crear(body: LibroCreate, conn):
    if len(body.isbn) != 13:                    # Validacion aqui? NO
        raise HTTPException(422, "ISBN malo")
    conn.execute("INSERT INTO ...", ...)         # SQL aqui? NO
    conn.commit()

# BIEN: el router solo conecta, la logica esta en el servicio
@router.post("/libros")
def crear(body: LibroCreate, service):
    dto = CreateLibroDTO(titulo=body.titulo, autor=body.autor, isbn=body.isbn)
    libro = service.register_libro(dto)          # El servicio hace todo
    return LibroResponse.model_validate(libro)
```

### Error 5: no usar codigos de estado correctos

```python
# MAL: todo devuelve 200
@router.post("/libros")    # Crear deberia ser 201
def crear(body):
    ...                     # FastAPI pone 200 por defecto

# MAL: inventar codigos
return JSONResponse(status_code=999, ...)    # 999 no existe

# BIEN: usar el codigo que corresponde
@router.post("/libros", status_code=status.HTTP_201_CREATED)
@router.delete("/libros/{id}", status_code=status.HTTP_204_NO_CONTENT)
```

---

## 27. Referencia rapida de FastAPI

### Decoradores de ruta

| Decorador            | Metodo HTTP | Uso                          |
|----------------------|-------------|------------------------------|
| `@router.get()`     | GET         | Leer datos                   |
| `@router.post()`    | POST        | Crear datos nuevos           |
| `@router.put()`     | PUT         | Actualizar datos completos   |
| `@router.patch()`   | PATCH       | Actualizar datos parciales   |
| `@router.delete()`  | DELETE      | Eliminar datos               |

### Parametros de los decoradores

| Parametro           | Que hace                              | Ejemplo                        |
|---------------------|---------------------------------------|--------------------------------|
| ruta                | La URL del endpoint                   | `"/"`, `"/{id}"`              |
| `response_model`    | Formato de la respuesta               | `response_model=LibroResponse` |
| `status_code`       | Codigo HTTP de respuesta exitosa      | `status_code=201`             |
| `tags`              | Grupo en la documentacion             | `tags=["Libros"]`             |
| `summary`           | Titulo corto en la documentacion      | `summary="Listar libros"`     |

### Tipos de parametros en las funciones

| De donde viene        | Como lo detecta FastAPI             | Ejemplo                         |
|-----------------------|-------------------------------------|---------------------------------|
| URL (path)            | Nombre esta en la ruta `/{nombre}`  | `libro_id: int`                |
| Query string (?x=y)   | Tipo simple con default             | `top: int = 5`                 |
| Body (JSON)           | Tipo es BaseModel                   | `body: LibroCreate`            |
| Dependencia           | Tiene `= Depends(funcion)`          | `service = Depends(get_service)` |

### Pydantic Field

| Validacion          | Ejemplo                              | Para que tipo     |
|---------------------|--------------------------------------|-------------------|
| Obligatorio         | `Field(...)`                         | Todos             |
| Opcional            | `Field(None)`                        | Todos             |
| Largo minimo        | `Field(min_length=1)`                | str               |
| Largo maximo        | `Field(max_length=200)`              | str               |
| Mayor que           | `Field(gt=0)`                        | int, float        |
| Mayor o igual       | `Field(ge=0)`                        | int, float        |
| Menor que           | `Field(lt=100)`                      | int, float        |
| Patron regex        | `Field(pattern=r"^\d{13}$")`           | str               |
| Ejemplo             | `Field(examples=["texto"])`          | Todos             |

### Respuestas comunes

```python
# Respuesta normal (200 por defecto)
return {"clave": "valor"}

# Respuesta con modelo
return LibroResponse.model_validate(libro)

# Respuesta con codigo custom
from fastapi.responses import JSONResponse
return JSONResponse(status_code=404, content={"detail": "No encontrado"})

# Sin respuesta (204)
# Solo pon status_code=204 en el decorador y no devuelvas nada
```

### Comandos de uvicorn

```
# Desarrollo (con auto-recarga)
uvicorn main:app --reload --port 8000

# Produccion
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# Con ruta de modulo
uvicorn src.mi_app.infrastructure.api.main_api:app --reload
```

| Flag          | Que hace                                       |
|---------------|------------------------------------------------|
| `--reload`    | Reinicia cuando cambias codigo (solo desarrollo)|
| `--port`      | Puerto donde escucha (default: 8000)           |
| `--host`      | Direccion (0.0.0.0 para acceso remoto)         |
| `--workers`   | Cantidad de procesos (para produccion)         |

---

## 28. Tu arsenal completo

### Lo que ya tienes

```
[x] Python: dataclasses, excepciones, type hints, ABC
[x] Arquitectura hexagonal: domain, application, infrastructure
[x] CRUD completo: modelos, puertos, DTOs, servicios, repositorios
[x] Base de datos: SQLite, SQL, consultas avanzadas
[x] CLI: menus, input/output, validacion
[x] Procesamiento: funciones puras, Counter, estadisticas
[x] Graficos: matplotlib (barras, linea, pastel, dashboard)
[x] Testing: pytest, fixtures, tests unitarios e integracion
[x] API REST: FastAPI, endpoints, schemas, error handling
[x] Documentacion: automatica con Swagger UI
```

### Estas listo? Si.

Con todo esto ya puedes CONSTRUIR SOFTWARE UTIL Y PROFESIONAL.

Puedes hacer un sistema completo donde:
1. Los datos se guardan en una base de datos
2. Se procesan con funciones que calculan y analizan
3. Se muestran en graficos profesionales
4. Se exponen a traves de una API para que cualquier
   programa, web o app los consuma
5. Todo esta testeado y documentado

### Que sigue (cuando quieras ir al siguiente nivel)

| Nivel              | Que aprender                                    | Para que                      |
|--------------------|-------------------------------------------------|-------------------------------|
| Frontend           | HTML, CSS, JavaScript, React o Vue              | Pagina web que consume tu API |
| Base de datos real | PostgreSQL, SQLAlchemy                          | Escalar a cientos de usuarios |
| Autenticacion      | JWT, OAuth2                                     | Login, permisos, seguridad    |
| Contenedores       | Docker, Docker Compose                          | Empaquetar y desplegar        |
| Cloud              | AWS, Azure, Google Cloud                        | Publicar en internet real     |
| CI/CD              | GitHub Actions                                  | Tests automaticos al subir codigo |

Pero eso es el SIGUIENTE nivel. Con lo que tienes ahora,
ya puedes construir aplicaciones backend completas y funcionales.
