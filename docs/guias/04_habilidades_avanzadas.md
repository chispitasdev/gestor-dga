# Guia Avanzada: Las 3 Habilidades que Faltan

Complemento de la guia de pensamiento. Estas 3 habilidades son las
que mas separan al que "sabe Python" del que sabe programar de verdad.

---

## Indice

1. [Saber leer codigo que no escribiste](#1-saber-leer-codigo-que-no-escribiste)
2. [Saber depurar (encontrar errores)](#2-saber-depurar-encontrar-errores)
3. [Mapa de ruta: que aprender despues](#3-mapa-de-ruta-que-aprender-despues)

---

## 1. Saber leer codigo que no escribiste

### El problema

Abris un proyecto de alguien mas. Ves 20 archivos. No sabes por donde empezar.
Te da ansiedad. Cerras todo.

Eso le pasa a todo el mundo. La solucion es tener un METODO, no leer todo de arriba a abajo.

### El metodo de los 5 pasos para leer cualquier proyecto

#### Paso 1: Buscar el punto de entrada

Todo programa tiene UN archivo que lo arranca. Buscalo primero.

Pistas para encontrarlo:
- Se llama `main.py`, `app.py`, `run.py`, `index.py`, o `manage.py`
- Tiene `if __name__ == "__main__":` adentro
- Es el archivo que ejecutas para correr el programa

En nuestro proyecto es `main.py`. Abrilo y leelo. No necesitas entender todo,
solo busca: que cosas crea? a quien llama?

```python
# Lo que ves en main.py (simplificado):
connection = get_connection("dga.db")
transformer_repo = SQLiteTransformerRepository(connection)
transformer_service = TransformerService(transformer_repo)
transformer_cli = TransformerCLI(transformer_service)
# ... lo mismo para samples ...
menu = MainMenu(transformer_cli, sample_cli)
menu.run()
```

Con solo eso ya sabes:
- Hay una base de datos SQLite
- Hay repositorios, servicios y CLIs
- El menu principal arranca todo

#### Paso 2: Seguir el flujo de UNA funcion

No intentes entender todo el proyecto. Elige UNA accion concreta
(ej: "registrar un transformador") y segui su camino archivo por archivo.

```
main.py --> Donde se crea el CLI?
  --> TransformerCLI --> Donde se llama a crear?
    --> _create() --> Que llama?
      --> self._service.register_transformer(dto) --> Que hace eso?
        --> transformer_service.py --> register_transformer()
```

Cuando entendiste UNA accion, las demas siguen el mismo patron.

#### Paso 3: Leer las firmas, no los cuerpos

Una "firma" es la primera linea de una funcion. Dice que recibe y que devuelve.

```python
def register_transformer(self, dto: CreateTransformerDTO) -> Transformer:
```

Sin leer adentro ya sabes:
- Recibe un DTO de creacion
- Devuelve un Transformer
- Se llama "registrar transformador"

Lee las firmas de todas las funciones del archivo. Eso te da un mapa mental
de que puede hacer esa clase, sin leer los detalles.

#### Paso 4: Leer los imports

Los imports de un archivo te dicen DE QUIEN depende:

```python
from src.dga.application.dto.transformer_dto import CreateTransformerDTO
from src.dga.application.services.transformer_service import TransformerService
from src.dga.domain.exceptions import DGADomainError
```

Con eso sabes: "Este archivo usa DTOs, un servicio, y puede lanzar errores de dominio."
No necesitas leer 100 lineas para saber eso.

#### Paso 5: Leer los tests

Los tests son la MEJOR documentacion. Te dicen que se supone que hace el codigo
y con que datos.

```python
def test_register_transformer_returns_entity_with_id():
    dto = CreateTransformerDTO(name="Trafo Norte")
    result = service.register_transformer(dto)
    assert result.id is not None
    assert result.name == "Trafo Norte"
```

Sin leer el servicio, ya sabes:
- Se le pasa un DTO con un nombre
- Devuelve algo con id y name
- El id no debe ser None despues de registrar

### Resumen del metodo

```
1. Buscar main.py (punto de entrada)
2. Seguir UNA accion de punta a punta
3. Leer firmas de funciones (que recibe, que devuelve)
4. Leer imports (de quien depende)
5. Leer tests (que se espera que haga)
```

Con esos 5 pasos podes entender cualquier proyecto en menos de 30 minutos.

---

## 2. Saber depurar (encontrar errores)

### El problema

Ejecutas el programa. Sale un error. Ves un muro de texto rojo. No sabes que hacer.
Empezas a cambiar cosas al azar hasta que "funciona" pero no sabes por que.

### Regla numero 1: LEER el error

Python te dice exactamente que paso y donde. Solo hay que saber leer el mensaje.

Un error tipico se ve asi:

```
Traceback (most recent call last):
  File "main.py", line 15, in <module>
    menu.run()
  File "src/dga/infrastructure/cli/transformer_cli.py", line 58, in run
    action()
  File "src/dga/infrastructure/cli/transformer_cli.py", line 72, in _create
    transformer = self._service.register_transformer(dto)
  File "src/dga/application/services/transformer_service.py", line 48, in register_transformer
    return self._repository.create(transformer)
  File "src/dga/infrastructure/persistence/sqlite_transformer_repository.py", line 68, in create
    cursor = self._conn.execute(sql, (transformer.name,))
sqlite3.OperationalError: no such table: transformers
```

Como leerlo:

1. **Lee de ABAJO hacia ARRIBA.** La ultima linea es el error real.
2. **La ultima linea dice:** `sqlite3.OperationalError: no such table: transformers`
   Traduccion: "La tabla 'transformers' no existe en la base de datos."
3. **La penultima linea dice donde fallo:** archivo, linea, codigo exacto.
4. **Las lineas de arriba son el camino:** como llego hasta ahi (la cadena de llamadas).

### El metodo sistematico para encontrar errores

#### Tecnica 1: Leer el error (80% de los casos)

La mayoria de las veces, el error te dice TODO lo que necesitas saber.
Solo hay que leerlo completo, de abajo hacia arriba.

Errores comunes y que significan:

| Error de Python                     | Que significa en espanol                   |
|-------------------------------------|--------------------------------------------|
| `NameError: name 'x' is not defined`| Usaste una variable que no existe           |
| `TypeError: expected str, got int`  | Pasaste un numero donde iba texto           |
| `AttributeError: has no attribute`  | Llamaste a un metodo que no existe          |
| `ValueError: invalid literal`       | Quisiste convertir algo imposible (ej: int("hola")) |
| `KeyError: 'nombre'`               | Buscaste una clave que no existe en un diccionario |
| `IndexError: list index out of range`| Pediste la posicion 5 de una lista de 3    |
| `IntegrityError: UNIQUE constraint` | Intentaste guardar un dato duplicado        |
| `OperationalError: no such table`   | La tabla no existe en la base de datos      |
| `FileNotFoundError`                 | El archivo no existe en esa ruta            |
| `ImportError: cannot import`        | El modulo o clase no se encuentra           |

#### Tecnica 2: Imprimir para ver que hay adentro (print-debugging)

Cuando no entendes por que algo falla, pone prints temporales
para ver que valores tiene cada variable:

```python
def _create(self) -> None:
    name = input("Nombre: ").strip()
    print(f"DEBUG: name = '{name}'")          # <-- temporal
    print(f"DEBUG: tipo = {type(name)}")       # <-- temporal
    dto = CreateTransformerDTO(name=name)
    print(f"DEBUG: dto = {dto}")               # <-- temporal
    transformer = self._service.register_transformer(dto)
    print(f"DEBUG: resultado = {transformer}") # <-- temporal
```

Ejecutas el programa y ves:

```
DEBUG: name = 'Trafo Norte'
DEBUG: tipo = <class 'str'>
DEBUG: dto = CreateTransformerDTO(name='Trafo Norte')
```

Si alguna linea muestra algo inesperado, ahi esta el problema.
Una vez que lo resolviste, BORRA los prints.

#### Tecnica 3: Aislar el problema (dividir a la mitad)

Si tenes una funcion de 10 lineas y no sabes cual falla:

1. Pone un print a la mitad (linea 5).
2. Si el print se ejecuta, el error esta DESPUES de la linea 5.
3. Si NO se ejecuta, el error esta ANTES de la linea 5.
4. Ahora pone un print en el cuarto que queda. Repetir.

En 3-4 intentos encontras la linea exacta, sin importar lo largo del codigo.

#### Tecnica 4: Reproducir el error con el caso mas simple posible

Si el error pasa cuando registras un transformador con nombre largo,
probalo primero con "A" (un solo caracter). Si tambien falla,
el problema no es el largo. Asi vas descartando.

#### Tecnica 5: Buscar el error exacto en Google/StackOverflow

Copia la ULTIMA linea del error (ej: `sqlite3.OperationalError: no such table`)
y pegala en Google tal cual. El 99% de las veces ya alguien tuvo ese problema.

### El flujo mental de depuracion

```
1. Leer el error de abajo hacia arriba
2. Identificar la linea y el archivo que falla
3. Preguntarse: "que valor esperaba aca y que valor hay realmente?"
4. Si no es obvio, poner prints para ver los valores
5. Si sigue sin ser obvio, aislar el problema (dividir a la mitad)
6. Si no lo encuentras, buscar el error exacto en Google
```

### Los 3 errores mas comunes del principiante al depurar

| Lo que hace (mal)                    | Lo que deberia hacer                     |
|--------------------------------------|------------------------------------------|
| Cambiar cosas al azar                | Leer el error primero                    |
| Borrar y reescribir todo             | Encontrar la linea exacta que falla      |
| Frustarse y dejar de intentar         | Usar print para ver que hay adentro      |

---

## 3. Mapa de ruta: que aprender despues

### Donde estas ahora

Ya sabes:
- Python basico (variables, funciones, clases, if, while, for)
- Hacer un CRUD completo
- Separar codigo en capas (hexagonal)
- Escribir tests
- Usar SQLite

Eso es mas de lo que la mayoria de cursos ensenan.

### La ruta de aprendizaje (en orden)

Cada nivel se construye sobre el anterior. No te saltes niveles.

#### Nivel 1: Solidificar lo que ya sabes (1-2 semanas)

Lo que hacer: construir OTRO CRUD totalmente diferente, desde cero, sin ayuda.

Ideas:
- Sistema de biblioteca (libros + prestamos)
- Inventario de productos (categorias + productos + stock)
- Registro de pacientes (pacientes + consultas)

Objetivo: que puedas hacerlo sin consultar el proyecto DGA.
Si podes, ya dominaste el nivel.

#### Nivel 2: Manejo de archivos y datos (1-2 semanas)

Lo que aprender:
- Leer y escribir archivos CSV (modulo `csv`)
- Leer y escribir archivos JSON (modulo `json`)
- Exportar datos a Excel (libreria `openpyxl`)
- Generar reportes en PDF (libreria `reportlab` o `fpdf`)

Por que importa: en la vida real, siempre te piden "exportar a Excel"
o "importar desde un CSV". Es lo primero que te van a pedir en un trabajo.

Proyecto sugerido: agregar al DGA la opcion de exportar muestras a CSV y Excel.

#### Nivel 3: Interfaz grafica basica (2-3 semanas)

Lo que aprender:
- `tkinter` (viene con Python, no requiere instalar nada)
- Ventanas, botones, campos de texto, tablas
- Conectar la interfaz con los servicios que ya tenes

Por que importa: el CLI es para programadores. Los usuarios reales quieren
botones y ventanas. Pero la logica de atras (servicios, repositorios)
sigue siendo EXACTAMENTE la misma.

Proyecto sugerido: reemplazar el CLI del DGA con una ventana de tkinter.
Solo cambias la capa de infraestructura. El dominio y la aplicacion no se tocan.
Esa es la magia de la arquitectura hexagonal.

#### Nivel 4: APIs y Web (3-4 semanas)

Lo que aprender:
- HTTP basico (GET, POST, PUT, DELETE -- son las mismas 4 del CRUD)
- `FastAPI` o `Flask` (frameworks web de Python)
- Crear endpoints que hagan lo mismo que tu CLI
- Probar con Postman o curl

Por que importa: hoy todo es web. Tu CRUD de transformadores podria ser
accesible desde un navegador en cualquier computadora de la empresa.

Proyecto sugerido: crear una API REST para el DGA. Otra vez, solo cambias
la capa de infraestructura. El dominio y la aplicacion no se tocan.

#### Nivel 5: Frontend basico (3-4 semanas)

Lo que aprender:
- HTML y CSS basico
- JavaScript basico
- Hacer que una pagina web hable con tu API

Por que importa: con una API (backend) y una pagina web (frontend),
tenes una aplicacion completa accesible desde el navegador.

#### Nivel 6: Bases de datos reales y despliegue (2-3 semanas)

Lo que aprender:
- PostgreSQL o MySQL (bases de datos de produccion)
- Docker (empaquetar tu app para que funcione en cualquier servidor)
- Desplegar en un servidor (Railway, Render, o un VPS)

Por que importa: SQLite sirve para desarrollo, pero en produccion
se usa PostgreSQL o MySQL.

### Diagrama visual de la ruta

```
AHORA --> Nivel 1: Otro CRUD solo
             |
          Nivel 2: Archivos (CSV, Excel, PDF)
             |
          Nivel 3: Interfaz grafica (tkinter)
             |
          Nivel 4: API web (FastAPI)
             |
          Nivel 5: Frontend (HTML/CSS/JS)
             |
          Nivel 6: BD real + Despliegue
             |
          PROGRAMADOR COMPLETO
```

### Que NO aprender todavia

Cosas que suenan atractivas pero no necesitas ahora:

| Tentacion                   | Por que NO ahora                                  |
|-----------------------------|----------------------------------------------------|
| Machine Learning            | Necesitas estadistica y mucho Python antes          |
| Blockchain                  | Es un nicho muy especifico                         |
| 5 lenguajes a la vez        | Domina UNO primero. Los demas se aprenden rapido   |
| Frameworks pesados (Django) | Primero FastAPI/Flask. Django tiene demasiada magia |
| Patrones de disenio (todos) | Ya usaste 3 sin darte cuenta. Los demas veniran     |
| Microservicios              | Primero domina un monolito bien hecho               |

### Cuanto tiempo toma todo

| Nivel | Tiempo estimado | Resultado concreto                        |
|-------|-----------------|-------------------------------------------|
| 1     | 1-2 semanas     | Podes hacer cualquier CRUD solo            |
| 2     | 1-2 semanas     | Exportas datos a Excel, CSV, PDF           |
| 3     | 2-3 semanas     | Tu programa tiene ventanas y botones       |
| 4     | 3-4 semanas     | Tu programa es accesible por HTTP          |
| 5     | 3-4 semanas     | Tenes una aplicacion web completa          |
| 6     | 2-3 semanas     | Tu app esta en un servidor real            |

Total: 3-5 meses dedicando 1-2 horas diarias.
Al final de esos meses podes construir una aplicacion web completa
desde cero. Eso es mas de lo que piden en la mayoria de trabajos junior.

### La unica regla que importa

**Construir cosas.** No mirar tutoriales, no leer libros sin practicar,
no acumular cursos. CONSTRUIR.

Cada proyecto terminado vale mas que 10 tutoriales vistos.

Si pasas 5 meses construyendo 6 proyectos (uno por nivel),
vas a tener un portafolio real y vas a saber mas que el 80%
de las personas que dicen "saber programar".

---

## Nota final

La guia anterior te enseno a PENSAR como programador.
Esta guia te enseno a LEER codigo, ENCONTRAR errores,
y saber PARA DONDE IR despues.

Con las dos juntas tenes todo lo necesario para crecer.
Lo unico que falta es sentarte y construir.
