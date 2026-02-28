# Guia de Pensamiento para Programadores

Manual de entrenamiento mental para resolver problemas de software.
No es un manual de Python. Es un manual de como PENSAR.

---

## Indice

1. [La regla de oro](#1-la-regla-de-oro)
2. [Como convertir un problema en codigo](#2-como-convertir-un-problema-en-codigo)
3. [Las 12 herramientas que cubren el 90% de todo](#3-las-12-herramientas-que-cubren-el-90-de-todo)
4. [El metodo de las 3 preguntas (antes de escribir codigo)](#4-el-metodo-de-las-3-preguntas-antes-de-escribir-codigo)
5. [Patrones mentales para tareas comunes](#5-patrones-mentales-para-tareas-comunes)
6. [Los 6 habitos del programador profesional](#6-los-6-habitos-del-programador-profesional)
7. [Como funciona un CRUD (la receta universal)](#7-como-funciona-un-crud-la-receta-universal)
8. [El viaje completo de un dato (de input a base de datos)](#8-el-viaje-completo-de-un-dato-de-input-a-base-de-datos)
9. [Errores comunes del principiante y como evitarlos](#9-errores-comunes-del-principiante-y-como-evitarlos)
10. [Ejercicios para entrenar el cerebro](#10-ejercicios-para-entrenar-el-cerebro)

---

## 1. La regla de oro

**No pensas en codigo. Pensas en problemas pequenos.**

Nadie se sienta y escribe 100 lineas de una. Lo que haces es:

1. Decir en espanol que necesitas.
2. Cortar esa oracion en pasos.
3. Convertir cada paso en la herramienta de Python que corresponde.

Eso es todo. El resto es practica.

---

## 2. Como convertir un problema en codigo

### Paso 1: Describir en espanol que tiene que pasar

Ejemplo: "Necesito pedirle un nombre al usuario, verificar que no este vacio,
empaquetarlo, y mandarlo al servicio para que lo guarde."

### Paso 2: Cortar la oracion con comas (cada coma es un paso)

- Pedir un nombre al usuario
- Verificar que no este vacio
- Empaquetarlo
- Mandarlo al servicio

### Paso 3: Traducir cada paso a Python

| Paso en espanol              | Herramienta Python          | Codigo                                     |
|------------------------------|-----------------------------|---------------------------------------------|
| Pedir un nombre al usuario   | `input()`                   | `name = input("Nombre: ").strip()`          |
| Verificar que no este vacio  | `if not`                    | `if not name: return`                       |
| Empaquetarlo                 | Crear un objeto              | `dto = CreateTransformerDTO(name=name)`     |
| Mandarlo al servicio         | Llamar un metodo             | `result = self._service.register(dto)`      |

### Paso 4: Escribir el codigo en ese orden

```python
def _create(self) -> None:
    name = input("Nombre: ").strip()           # Paso 1
    if not name:                                # Paso 2
        print("El nombre no puede estar vacio.")
        return
    dto = CreateTransformerDTO(name=name)       # Paso 3
    result = self._service.register(dto)        # Paso 4
    print(f"Registrado con ID {result.id}")     # Resultado
```

**Cada linea viene de un paso en espanol. No se invento nada en el aire.**

---

## 3. Las 12 herramientas que cubren el 90% de todo

Memorizalas. Con estas 12 haces cualquier CRUD y la mayoria de programas:

| #  | Herramienta              | Cuando la usas                                    | Ejemplo                                  |
|----|--------------------------|---------------------------------------------------|------------------------------------------|
| 1  | `while True` + `break`   | Repetir algo hasta que el usuario quiera salir     | Menu interactivo                         |
| 2  | `if / elif / else`       | Elegir entre opciones o validar datos              | Verificar si un campo esta vacio         |
| 3  | `diccionario` + `.get()` | Muchas opciones, cada una hace algo distinto       | Despachar opcion del menu                |
| 4  | `try / except`           | Algo puede fallar y no quiero que explote          | Operaciones de base de datos             |
| 5  | `input()`                | Pedir datos al usuario                             | Nombre, ID, valores numericos            |
| 6  | `.strip()`               | Limpiar texto de espacios sobrantes                | Siempre despues de `input()`             |
| 7  | `if not variable`        | Verificar que algo no este vacio                   | Validacion rapida de campos              |
| 8  | `return` (sin nada)      | Abortar la funcion y volver al menu                | Cuando el dato es invalido               |
| 9  | `continue`               | Volver al inicio del bucle sin ejecutar lo de abajo| Opcion invalida en un menu               |
| 10 | `f"texto {variable}"`    | Armar texto con datos adentro                      | Mostrar resultados al usuario            |
| 11 | `Clase(campo=valor)`     | Crear un objeto (DTO, entidad, etc.)               | Empaquetar datos                         |
| 12 | `objeto.metodo()`        | Pedirle a otro objeto que haga algo                | Llamar al servicio o repositorio         |

No hay algoritmos complejos. No hay matematica. No hay recursion.
Solo estas 12 cosas combinadas de distintas formas.

---

## 4. El metodo de las 3 preguntas (antes de escribir codigo)

Antes de escribir una sola linea para cualquier proyecto,
respondete estas 3 preguntas en orden:

### Pregunta 1: "Que datos manejo?"

Pensalo como formularios vacios. Que campos tienen?

```
Ejemplo para un sistema de transformadores:

Transformador:
  - id (lo pone la computadora)
  - nombre (lo pone el usuario)

Muestra:
  - id
  - id del transformador (a cual pertenece)
  - fecha
  - 9 gases (hidrogeno, metano, etc.)
```

Esto se convierte en los **modelos** (las clases con los campos).

### Pregunta 2: "Que operaciones necesito?"

Para cada grupo de datos, que necesita hacer el usuario?

```
Con un Transformador puedo:
  - Crear uno nuevo
  - Ver todos
  - Ver uno por ID
  - Cambiarle el nombre
  - Borrarlo
```

Esto se convierte en los **metodos del servicio** (una funcion por operacion).

### Pregunta 3: "Donde guardo los datos?"

Opciones comunes: SQLite, PostgreSQL, archivos JSON, API externa.
Esto se convierte en el **repositorio** (la clase que ejecuta SQL o lo que sea).

**Siempre en ese orden.** Datos primero. Operaciones segundo. Almacenamiento tercero.

---

## 5. Patrones mentales para tareas comunes

### "Necesito un menu interactivo"

Patron: `while True` + `input` + `diccionario de acciones`

```python
while True:
    print(menu)
    choice = input("Opcion: ").strip()
    if choice == "0":
        break
    action = actions.get(choice)
    if action is None:
        print("Opcion no valida.")
        continue
    try:
        action()
    except Exception as e:
        print(f"Error: {e}")
```

### "Necesito pedir un dato y validarlo"

Patron: `input` + `strip` + `if not` + `return`

```python
name = input("Nombre: ").strip()
if not name:
    print("No puede estar vacio.")
    return
```

### "Necesito pedir un numero"

Patron: `input` + `isdigit` + `int()`

```python
raw_id = input("ID: ").strip()
if not raw_id.isdigit():
    print("Debe ser un numero.")
    return
real_id = int(raw_id)
```

### "Necesito pedir un numero decimal"

Patron: `input` + `try/except` con `float()`

```python
raw = input("Valor: ").strip()
try:
    value = float(raw)
except ValueError:
    print("Debe ser un numero.")
    return
if value < 0:
    print("Debe ser positivo.")
    return
```

### "Necesito pasar datos de un lugar a otro"

Patron: crear un DTO (un empaque con campos fijos)

```python
dto = CreateTransformerDTO(name=name)           # Empaqueta
result = self._service.register(dto)            # Envia
print(f"ID: {result.id}, Nombre: {result.name}")  # Usa la respuesta
```

### "Necesito guardar algo en la base de datos"

Patron: `execute` + `commit` + try/except para duplicados

```python
sql = "INSERT INTO tabla (campo) VALUES (?)"
try:
    cursor = self._conn.execute(sql, (valor,))
    self._conn.commit()
except sqlite3.IntegrityError:
    raise DuplicateError(valor)
nuevo_id = cursor.lastrowid
```

### "Necesito buscar algo en la base de datos"

Patron: `execute` + `fetchone` o `fetchall` + verificar None

```python
sql = "SELECT * FROM tabla WHERE id = ?"
row = self._conn.execute(sql, (id,)).fetchone()
if row is None:
    return None              # No existe
return Transformer(id=row["id"], name=row["name"])   # Convertir fila a objeto
```

### "Necesito mostrar una lista como tabla"

Patron: `f-string` con formato + `for` + contador

```python
print(f"\n{'ID':<6} {'Nombre'}")
print("-" * 40)
for item in lista:
    print(f"{item.id:<6} {item.name}")
print(f"\nTotal: {len(lista)} registros.")
```

### "Necesito pedir confirmacion antes de algo peligroso"

Patron: `input` + comparar con "s"

```python
confirm = input("Confirmar (s/n): ").strip().lower()
if confirm != "s":
    print("Operacion cancelada.")
    return
# Si llego aca, proceder con la operacion peligrosa
```

---

## 6. Los 6 habitos del programador profesional

### Habito 1: Pensar en todo lo que puede salir mal ANTES de que pase

Antes de escribir una funcion, hacete 3 preguntas:

1. Que pasa si el dato esta vacio?
2. Que pasa si el dato tiene basura (letras donde va un numero)?
3. Que pasa si el dato es valido pero no existe en la base de datos?

```python
# Principiante (no valida nada):
def delete(self, raw_id):
    self._service.remove(int(raw_id))

# Profesional (previene cada problema):
def delete(self, raw_id):
    raw_id = raw_id.strip()              # Dato vacio? Limpio primero
    if not raw_id.isdigit():             # Basura? Rechazo
        print("Debe ser un numero.")
        return
    confirm = input("Seguro? (s/n): ")   # Error humano? Confirmo
    if confirm != "s":
        return
    self._service.remove(int(raw_id))    # Ahora si, seguro
```

### Habito 2: Cada logica tiene UN solo lugar

Si copias y pegas logica, para.
Preguntate: "donde deberia vivir esto UNA sola vez?"

```
MAL:  Validar el nombre en el CLI, en el servicio, y en el repositorio.
BIEN: Validar el nombre SOLO en el modelo. Los demas confian en eso.
```

Si manana cambias la regla (ej: "minimo 3 caracteres"),
la cambias en UN archivo, no en tres.

### Habito 3: Los nombres son documentacion

Si necesitas un comentario para explicar que hace una variable,
cambia el nombre de la variable.

| Mal nombre   | Buen nombre              | Por que                          |
|--------------|--------------------------|----------------------------------|
| `d`          | `dto`                    | Sabes que es un paquete de datos |
| `x`          | `name`                   | Sabes que es un nombre           |
| `proc`       | `register_transformer`   | Sabes la accion y el sujeto      |
| `r`          | `transformer`            | Sabes que devuelve               |
| `do_stuff`   | `validate_gas_reading`   | Sabes QUE valida y DE QUE        |
| `data`       | `gas_reading`            | Sabes que tipo de datos son      |
| `handle`     | `save_sample`            | Sabes la accion concreta         |

**El mejor comentario es el que NO hace falta escribir.**

### Habito 4: No mezclar responsabilidades

Cada archivo responde a UNA sola pregunta:

| Archivo                              | Unica pregunta que responde            |
|--------------------------------------|----------------------------------------|
| `transformer.py`                     | Que ES un transformador?               |
| `transformer_service.py`             | Que PUEDO HACER con un transformador?  |
| `sqlite_transformer_repository.py`   | DONDE se guarda un transformador?      |
| `transformer_cli.py`                 | COMO le pido/muestro datos al usuario? |

Si un archivo responde a 2 preguntas, dividilo en 2.

Test rapido: si le explicas a alguien que hace un archivo
y usas la palabra "y" ("pide datos al usuario Y los guarda en la BD"),
probablemente son dos responsabilidades que deberian estar separadas.

### Habito 5: Hacer que lo nuevo sea facil de agregar

Preguntate: "si manana agrego una funcionalidad nueva,
cuanto codigo existente tengo que tocar?"

```python
# MAL: agregar una opcion requiere modificar la cadena de if/elif
if choice == "1":
    self._create()
elif choice == "2":
    self._list_all()
elif choice == "3":    # <-- nuevo: hay que meterlo en medio
    self._export()

# BIEN: agregar una opcion es agregar UNA linea
actions = {
    "1": self._create,
    "2": self._list_all,
    "3": self._export,    # <-- solo esto, nada mas se toca
}
```

Cuanto menos toques, menos cosas rompes.

### Habito 6: Escribir codigo que se puede testear solo

El servicio no crea su propia conexion a la base de datos.
La RECIBE de afuera:

```python
class TransformerService:
    def __init__(self, repository):     # <-- recibe el repositorio
        self._repository = repository
```

Esto permite:
- En la app real: pasarle el repositorio de SQLite.
- En los tests: pasarle un repositorio falso (Mock).

Si el servicio creara la conexion adentro, no podrias testearlo
sin una base de datos real.

**Regla:** Si una clase necesita algo externo (base de datos, API, archivos),
que lo reciba por parametro en el constructor. Nunca que lo cree adentro.

---

## 7. Como funciona un CRUD (la receta universal)

Un CRUD son 4 operaciones:

| Operacion | En espanol           | SQL equivalente | Metodo tipico |
|-----------|----------------------|-----------------|---------------|
| Create    | Crear un registro    | INSERT INTO     | `create()`    |
| Read      | Leer uno o varios    | SELECT          | `get_by_id()`, `get_all()` |
| Update    | Modificar un registro| UPDATE          | `update()`    |
| Delete    | Eliminar un registro | DELETE           | `delete()`    |

### Los 5 pasos para armar cualquier CRUD

Siempre los mismos, en este orden:

```
Paso 1 --> Definir los DATOS       --> Crear el modelo
           (que campos tiene)         transformer.py

Paso 2 --> Definir las OPERACIONES --> Crear el servicio
           (create, read,             transformer_service.py
            update, delete)

Paso 3 --> Definir DONDE se guarda --> Crear la interfaz + repositorio
           (SQLite, Postgres, etc.)   transformer_repository.py
                                      sqlite_transformer_repository.py

Paso 4 --> Definir COMO se ingresa --> Crear el CLI / pantalla / API
           (consola, web, app)        transformer_cli.py

Paso 5 --> CONECTAR todo           --> En main.py, armar las piezas
```

Si manana te piden un CRUD de clientes, de productos, de facturas,
o de lo que sea: son los mismos 5 pasos. Lo unico que cambia son
los datos y las reglas de cada negocio.

---

## 8. El viaje completo de un dato (de input a base de datos)

Cuando el usuario escribe "Trafo Norte 01" para registrar un transformador,
el dato viaja por esta cadena:

```
PASO 1 -- transformer_cli.py
  El usuario escribe "Trafo Norte 01"
  name = input("Nombre: ").strip()
  Ahora name = "Trafo Norte 01"

PASO 2 -- transformer_cli.py
  Verifica que no este vacio: if not name --> no esta vacio, sigue
  Lo mete en un DTO (sobre sellado):
  dto = CreateTransformerDTO(name="Trafo Norte 01")

PASO 3 -- transformer_service.py
  Recibe el DTO, lo abre, saca el nombre
  Crea un objeto Transformer: Transformer(name="Trafo Norte 01")
  El modelo se valida a si mismo al nacer (__post_init__)
  Si esta todo bien, se lo pasa al repositorio

PASO 4 -- sqlite_transformer_repository.py
  Recibe el Transformer
  Ejecuta: INSERT INTO transformers (name) VALUES ('Trafo Norte 01')
  Confirma: self._conn.commit()
  SQLite le asigna id=1 automaticamente
  Le pone el id al objeto: transformer.id = 1
  Lo devuelve

PASO 5 -- De vuelta en transformer_cli.py
  Recibe el Transformer con id=1
  Muestra: "Registrado. ID: 1, Nombre: Trafo Norte 01"
```

**Siempre es la misma cadena:**

```
CLI  -->  Servicio  -->  Repositorio  -->  Base de datos
                                               |
CLI  <--  Servicio  <--  Repositorio  <--------+
```

La pelota va y vuelve por el mismo camino.

---

## 9. Errores comunes del principiante y como evitarlos

### Error 1: Escribir todo en un solo archivo

**Problema:** Un archivo de 500 lineas donde todo esta mezclado.
Si algo falla, no sabes donde buscar.

**Solucion:** Un archivo por responsabilidad.
Si el error es al guardar, esta en el repositorio.
Si el error es al validar, esta en el modelo o servicio.
Cada error tiene su lugar.

### Error 2: No limpiar el input del usuario

**Problema:**
```python
name = input("Nombre: ")    # El usuario escribe "  Trafo  "
# Ahora name = "  Trafo  " (con espacios invisibles)
```

**Solucion:** SIEMPRE usar `.strip()` despues de `input()`.
```python
name = input("Nombre: ").strip()    # name = "Trafo"
```

### Error 3: No validar antes de convertir

**Problema:**
```python
id = int(input("ID: "))    # Si el usuario escribe "hola", EXPLOTA
```

**Solucion:** Validar primero, convertir despues.
```python
raw = input("ID: ").strip()
if not raw.isdigit():
    print("Debe ser un numero.")
    return
id = int(raw)    # Ahora es seguro
```

### Error 4: Repetir logica en varios lugares

**Problema:** Validar el nombre en 3 archivos distintos.
Si cambias la regla, te olvidas de uno.

**Solucion:** Validar en UN solo lugar (el modelo) y confiar en que esta ahi.

### Error 5: Nombres genericos

**Problema:**
```python
def process(data):          # Que procesa? Que data?
    result = do_thing(data)  # Que cosa hace?
    return result
```

**Solucion:**
```python
def register_transformer(dto: CreateTransformerDTO) -> Transformer:
    transformer = Transformer(name=dto.name)
    return self._repository.create(transformer)
```

### Error 6: No manejar errores

**Problema:** El programa explota si algo sale mal.
El usuario ve un traceback de Python que no entiende.

**Solucion:** `try/except` en el punto de entrada (el CLI),
con mensajes claros para el usuario.

```python
try:
    action()
except DGADomainError as exc:
    print(f"Error: {exc}")       # Mensaje que el usuario entiende
```

### Error 7: Crear conexiones a la BD en cualquier lado

**Problema:** Cada clase crea su propia conexion.
Hay 5 conexiones abiertas, no sabes cual fallo, no podes testear.

**Solucion:** Crear UNA conexion en main.py y pasarla a todos los que la necesiten.
```python
# En main.py (un solo lugar):
connection = get_connection("dga.db")
repo = SQLiteTransformerRepository(connection)    # Le paso la conexion
service = TransformerService(repo)                # Le paso el repo
cli = TransformerCLI(service)                     # Le paso el servicio
```

---

## 10. Ejercicios para entrenar el cerebro

### Ejercicio 1: Describir antes de codificar

Toma cualquier funcion del proyecto.
SIN mirar el codigo, describe en espanol que deberia hacer.
Despues abrila y compara.

Ejemplo con `_update`:
- "Pedir el ID del transformador. Validar que sea numero. Pedir el nuevo
  nombre. Validar que no este vacio. Armar un DTO con el ID y el nombre
  nuevo. Mandarlo al servicio. Mostrar el resultado."

Ahora abri `_update` y vas a ver que el codigo dice exactamente eso.

### Ejercicio 2: Encontrar los problemas

Lee este codigo y anota TODO lo que puede salir mal:

```python
def crear_producto():
    n = input("Nombre: ")
    p = float(input("Precio: "))
    cursor.execute(f"INSERT INTO products VALUES ('{n}', {p})")
    conn.commit()
    print("Listo")
```

Pistas: hay al menos 6 problemas.

(Respuestas al final del documento.)

### Ejercicio 3: Dividir un problema nuevo

Sin escribir codigo, solo en espanol, describe los pasos para:
"Un sistema donde un profesor registra alumnos y les pone notas."

Preguntas a responder:
1. Que datos hay? (modelos)
2. Que operaciones necesita el profesor? (servicio)
3. Que validaciones hacen falta?

### Ejercicio 4: Traducir espanol a Python

Convierte cada oracion a una linea de Python:

1. "Pedir un email al usuario y limpiar espacios"
2. "Si el email no contiene arroba, mostrar error y salir"
3. "Crear un paquete con el email adentro"
4. "Mandarlo al servicio de usuarios"
5. "Mostrar el ID del usuario creado"

### Ejercicio 5: Reconocer patrones

Abrí cualquier metodo del proyecto y marca con colores:
- AZUL: donde se piden datos (input)
- ROJO: donde se valida (if not, isdigit, etc.)
- VERDE: donde se empaqueta (crear DTOs u objetos)
- NARANJA: donde se delega (llamar al servicio)
- MORADO: donde se muestra el resultado (print)

Vas a notar que TODOS los metodos tienen los mismos colores en el mismo orden.

---

## Respuestas del Ejercicio 2

Los 6 problemas del codigo:

```python
def crear_producto():
    n = input("Nombre: ")                                      # 1. No usa .strip()
    p = float(input("Precio: "))                                # 2. Si escribe "hola", explota
    cursor.execute(f"INSERT INTO products VALUES ('{n}', {p})") # 3. SQL Injection (usar ? en lugar de f-string)
    conn.commit()                                               # 4. No maneja error si la BD falla
    print("Listo")                                              # 5. No muestra el ID generado
                                                                # 6. Nombres "n" y "p" no dicen nada
```

Version corregida:

```python
def crear_producto():
    name = input("Nombre: ").strip()                  # 1. Limpia espacios
    if not name:                                       #    Valida que no este vacio
        print("El nombre no puede estar vacio.")
        return

    raw_price = input("Precio: ").strip()
    try:
        price = float(raw_price)                       # 2. Convierte de forma segura
    except ValueError:
        print("El precio debe ser un numero.")
        return
    if price < 0:                                      #    Valida rango
        print("El precio no puede ser negativo.")
        return

    sql = "INSERT INTO products (name, price) VALUES (?, ?)"  # 3. Parametros seguros
    try:
        cursor = conn.execute(sql, (name, price))              # 4. Maneja errores
        conn.commit()
    except sqlite3.IntegrityError:
        print("Ya existe un producto con ese nombre.")
        return

    print(f"Producto creado con ID {cursor.lastrowid}")        # 5. Muestra el ID
                                                                # 6. Nombres claros
```

---

## Nota final

La programacion no es memorizar funciones.
Es saber dividir un problema grande en problemas pequenos,
y saber que herramienta usar para cada uno.

Las herramientas son pocas (12 para un CRUD).
Lo que cambia siempre es el problema.
Pero el METODO para resolverlo es siempre el mismo:

```
Espanol  -->  Pasos  -->  Herramientas  -->  Codigo
```

Entrena esto y vas a poder resolver cualquier cosa.
