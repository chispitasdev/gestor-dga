# Guia: Procesamiento de Datos y Graficos Profesionales

Complemento de la guia CRUD hexagonal.
Toma los datos que ya guardaste en la base de datos, los procesa
con funciones, genera graficos y los presenta de forma profesional.
Usa el mismo ejemplo de Biblioteca (libros y prestamos).

---

## Indice

1. [Que necesitas instalar](#1-que-necesitas-instalar)
2. [Donde encaja esto en la arquitectura hexagonal](#2-donde-encaja-esto-en-la-arquitectura-hexagonal)
3. [Paso 1: Funciones de procesamiento (logica pura)](#3-paso-1-funciones-de-procesamiento)
4. [Paso 2: Servicio de reportes](#4-paso-2-servicio-de-reportes)
5. [Paso 3: Graficos con matplotlib](#5-paso-3-graficos-con-matplotlib)
6. [Paso 4: Graficos de barras](#6-paso-4-graficos-de-barras)
7. [Paso 5: Graficos de pastel (pie)](#7-paso-5-graficos-de-pastel)
8. [Paso 6: Graficos de linea (evolucion en el tiempo)](#8-paso-6-graficos-de-linea)
9. [Paso 7: Graficos combinados (subplots)](#9-paso-7-graficos-combinados)
10. [Paso 8: Exportar graficos a imagen](#10-paso-8-exportar-graficos-a-imagen)
11. [Paso 9: Tablas formateadas en consola](#11-paso-9-tablas-formateadas-en-consola)
12. [Paso 10: Integrar todo en el CLI](#12-paso-10-integrar-todo-en-el-cli)
13. [Paso 11: Consultas SQL avanzadas para reportes](#13-paso-11-consultas-sql-avanzadas-para-reportes)
14. [Paso 12: El archivo completo de reportes](#14-paso-12-el-archivo-completo-de-reportes)
15. [Receta: como pensar un reporte nuevo](#15-receta-como-pensar-un-reporte-nuevo)
16. [Errores comunes al graficar](#16-errores-comunes-al-graficar)
17. [Referencia rapida de matplotlib](#17-referencia-rapida-de-matplotlib)
18. [Siguiente paso despues de esto](#18-siguiente-paso-despues-de-esto)

---

## 1. Que necesitas instalar

```
pip install matplotlib
```

Agrega al `requirements.txt`:

```
pytest>=7.0
matplotlib>=3.7
```

### Que es matplotlib

La libreria mas usada en Python para hacer graficos.
Puede hacer barras, lineas, pastel, dispersiones, histogramas
y muchos mas. Es la base sobre la que se construyen otras
librerias mas avanzadas (como seaborn o plotly).

---

## 2. Donde encaja esto en la arquitectura hexagonal

Los graficos y reportes son PRESENTACION. Van en infrastructure.
El procesamiento de datos (calculos, estadisticas) es LOGICA DE NEGOCIO.
Va en application.

```
domain/
    models/
        libro.py                    <-- Ya existe
        prestamo.py                 <-- Ya existe
    ports/
        libro_repository.py         <-- Ya existe
        prestamo_repository.py      <-- Ya existe

application/
    services/
        libro_service.py            <-- Ya existe
        prestamo_service.py         <-- Ya existe
        reporte_service.py          <-- NUEVO: logica de reportes

infrastructure/
    persistence/
        sqlite_libro_repository.py  <-- Ya existe (agregar consultas nuevas)
    cli/
        libro_cli.py                <-- Ya existe
        reporte_cli.py              <-- NUEVO: menu de reportes
    graphics/
        chart_generator.py          <-- NUEVO: genera los graficos
```

### Regla de separacion

```
reporte_service.py    --> Calcula los numeros (logica pura, sin graficos)
chart_generator.py    --> Dibuja los graficos (solo presentacion)
reporte_cli.py        --> Menu de consola para elegir reportes
```

El servicio NO sabe de matplotlib.
El generador de graficos NO sabe de SQL.
Cada uno hace UNA sola cosa.

---

## 3. Paso 1: Funciones de procesamiento

Antes de graficar, necesitas PROCESAR los datos.
Esto significa: tomar la lista cruda de la BD y convertirla
en numeros utiles.

### Que tipo de preguntas responden las funciones de procesamiento

```
Con los libros:
  - Cuantos libros hay en total?
  - Cuantos estan disponibles vs prestados?
  - Cuantos libros tiene cada autor?
  - Cual es el autor con mas libros?

Con los prestamos:
  - Cuantos prestamos hay activos?
  - Cuantos prestamos se hicieron por mes?
  - Cual es la persona que mas libros pidio?
  - Cual es el tiempo promedio de prestamo?
```

### Funciones puras de procesamiento

Una funcion "pura" recibe datos y devuelve un resultado.
No accede a la BD, no imprime, no grafica. Solo calcula.

```python
"""Funciones de procesamiento de datos para reportes."""

from __future__ import annotations

from collections import Counter
from datetime import date

from src.mi_app.domain.models.libro import Libro
from src.mi_app.domain.models.prestamo import Prestamo


def contar_por_disponibilidad(libros: list[Libro]) -> dict[str, int]:
    """Cuenta cuantos libros estan disponibles y cuantos prestados.

    Returns:
        {"Disponibles": 15, "Prestados": 8}
    """
    disponibles = sum(1 for libro in libros if libro.disponible)
    prestados = len(libros) - disponibles
    return {"Disponibles": disponibles, "Prestados": prestados}


def contar_libros_por_autor(libros: list[Libro]) -> dict[str, int]:
    """Cuenta cuantos libros tiene cada autor.

    Returns:
        {"Cervantes": 3, "Borges": 5, "Garcia Marquez": 2}
    """
    autores = [libro.autor for libro in libros]
    return dict(Counter(autores))


def ranking_autores(libros: list[Libro], top: int = 5) -> list[tuple[str, int]]:
    """Devuelve los autores con mas libros, ordenados de mayor a menor.

    Returns:
        [("Borges", 5), ("Cervantes", 3), ("Garcia Marquez", 2)]
    """
    conteo = Counter(libro.autor for libro in libros)
    return conteo.most_common(top)


def prestamos_por_mes(prestamos: list[Prestamo]) -> dict[str, int]:
    """Cuenta cuantos prestamos se hicieron en cada mes.

    Returns:
        {"2026-01": 12, "2026-02": 8, "2026-03": 15}
    """
    meses: dict[str, int] = {}
    for prestamo in prestamos:
        clave = prestamo.fecha_prestamo.strftime("%Y-%m")
        meses[clave] = meses.get(clave, 0) + 1
    return dict(sorted(meses.items()))


def personas_mas_activas(
    prestamos: list[Prestamo], top: int = 5
) -> list[tuple[str, int]]:
    """Devuelve las personas que mas libros pidieron prestados.

    Returns:
        [("Juan Perez", 8), ("Ana Lopez", 5)]
    """
    conteo = Counter(p.nombre_persona for p in prestamos)
    return conteo.most_common(top)


def promedio_dias_prestamo(prestamos: list[Prestamo]) -> float:
    """Calcula el promedio de dias que duran los prestamos devueltos.

    Solo cuenta prestamos que ya fueron devueltos (tienen fecha_devolucion).
    """
    devueltos = [
        p for p in prestamos
        if p.fecha_devolucion is not None
    ]
    if not devueltos:
        return 0.0

    total_dias = sum(
        (p.fecha_devolucion - p.fecha_prestamo).days
        for p in devueltos
    )
    return total_dias / len(devueltos)
```

### Herramientas clave que usamos

| Herramienta               | Que hace                          | Ejemplo                           |
|----------------------------|-----------------------------------|-----------------------------------|
| `Counter`                  | Cuenta repeticiones               | `Counter(["a","b","a"])` -> `{"a":2,"b":1}` |
| `Counter.most_common(n)`   | Los n mas frecuentes              | `[("a", 2), ("b", 1)]`           |
| `sum(1 for x in lista if condicion)` | Contar con filtro      | Cuantos disponibles               |
| `dict.get(clave, default)` | Buscar o usar default             | Acumular conteos                  |
| `sorted(dict.items())`     | Ordenar diccionario               | Meses en orden cronologico        |
| `.strftime("%Y-%m")`       | Fecha a texto formateado          | `date(2026,3,15)` -> `"2026-03"` |
| `(fecha2 - fecha1).days`   | Dias entre dos fechas             | Duracion de prestamo              |

---

## 4. Paso 2: Servicio de reportes

El servicio orquesta: pide datos al repositorio, los pasa a las
funciones de procesamiento, y devuelve los resultados listos.

```python
"""Servicio de reportes de la biblioteca."""

from __future__ import annotations

from src.mi_app.application.services import data_processing as dp
from src.mi_app.domain.ports.libro_repository import LibroRepository
from src.mi_app.domain.ports.prestamo_repository import PrestamoRepository


class ReporteService:
    """Genera los datos procesados para cada reporte."""

    def __init__(
        self,
        libro_repo: LibroRepository,
        prestamo_repo: PrestamoRepository,
    ) -> None:
        self._libro_repo = libro_repo
        self._prestamo_repo = prestamo_repo

    def reporte_disponibilidad(self) -> dict[str, int]:
        """Cuantos libros disponibles vs prestados."""
        libros = self._libro_repo.get_all()
        return dp.contar_por_disponibilidad(libros)

    def reporte_libros_por_autor(self) -> dict[str, int]:
        """Cuantos libros tiene cada autor."""
        libros = self._libro_repo.get_all()
        return dp.contar_libros_por_autor(libros)

    def reporte_top_autores(self, top: int = 5) -> list[tuple[str, int]]:
        """Los autores con mas libros."""
        libros = self._libro_repo.get_all()
        return dp.ranking_autores(libros, top)

    def reporte_prestamos_por_mes(self) -> dict[str, int]:
        """Cuantos prestamos por mes."""
        prestamos = self._prestamo_repo.get_all()
        return dp.prestamos_por_mes(prestamos)

    def reporte_personas_activas(self, top: int = 5) -> list[tuple[str, int]]:
        """Las personas que mas libros pidieron."""
        prestamos = self._prestamo_repo.get_all()
        return dp.personas_mas_activas(prestamos, top)

    def reporte_promedio_dias(self) -> float:
        """Promedio de dias de duracion de prestamos."""
        prestamos = self._prestamo_repo.get_all()
        return dp.promedio_dias_prestamo(prestamos)
```

### El patron del servicio de reportes

```
1. Pedir datos crudos al repositorio   -->  libro_repo.get_all()
2. Pasar los datos a la funcion pura   -->  dp.contar_por_disponibilidad(libros)
3. Devolver el resultado               -->  return resultado
```

Es siempre el mismo patron. Nunca grafica. Nunca imprime.
Solo conecta el repositorio con las funciones de procesamiento.

---

## 5. Paso 3: Graficos con matplotlib

### La estructura basica de cualquier grafico

```python
import matplotlib.pyplot as plt

# 1. Crear la figura y el area de dibujo
fig, ax = plt.subplots(figsize=(10, 6))

# 2. Dibujar los datos
ax.bar(categorias, valores)

# 3. Decorar (titulos, etiquetas, colores)
ax.set_title("Mi Grafico")
ax.set_xlabel("Eje X")
ax.set_ylabel("Eje Y")

# 4. Mostrar
plt.tight_layout()
plt.show()
```

### Que es fig y que es ax

```
fig = La ventana completa (el lienzo en blanco)
ax  = El area donde se dibuja el grafico (los ejes X e Y)

Una fig puede tener varios ax (varios graficos en una ventana).
```

### Que es plt.subplots()

Crea la ventana y el area de dibujo en una sola linea:

```python
fig, ax = plt.subplots()                  # Un solo grafico
fig, ax = plt.subplots(figsize=(10, 6))   # Un grafico de 10x6 pulgadas
fig, axes = plt.subplots(1, 2)            # Dos graficos lado a lado
fig, axes = plt.subplots(2, 1)            # Dos graficos uno arriba del otro
```

### El ciclo de vida de un grafico

```
1. plt.subplots()    --> Crear la ventana y el area
2. ax.bar/plot/pie   --> Dibujar los datos
3. ax.set_title      --> Ponerle titulo
4. ax.set_xlabel     --> Etiqueta del eje X
5. ax.set_ylabel     --> Etiqueta del eje Y
6. plt.tight_layout  --> Ajustar para que no se corten los textos
7. plt.savefig       --> (Opcional) Guardar como imagen
8. plt.show          --> Mostrar en pantalla
9. plt.close         --> Liberar memoria
```

---

## 6. Paso 4: Graficos de barras

El grafico mas comun para comparar cantidades entre categorias.

### Ejemplo: libros por autor

```python
"""Generador de graficos para la biblioteca."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt


# Colores profesionales (paleta consistente)
COLORS = {
    "primary": "#2563EB",       # Azul
    "secondary": "#10B981",     # Verde
    "accent": "#F59E0B",        # Amarillo
    "danger": "#EF4444",        # Rojo
    "neutral": "#6B7280",       # Gris
}

# Paleta para multiples barras
PALETTE = ["#2563EB", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6", "#EC4899"]


def grafico_libros_por_autor(
    datos: dict[str, int],
    output_path: Path | None = None,
) -> None:
    """Grafico de barras horizontales: libros por autor.

    Args:
        datos: {"Cervantes": 3, "Borges": 5, ...}
        output_path: Si se proporciona, guarda la imagen en esa ruta.
    """
    if not datos:
        print("No hay datos para graficar.")
        return

    # Ordenar de mayor a menor para que se vea mejor
    datos_ordenados = dict(sorted(datos.items(), key=lambda x: x[1]))

    autores = list(datos_ordenados.keys())
    cantidades = list(datos_ordenados.values())

    fig, ax = plt.subplots(figsize=(10, max(4, len(autores) * 0.5)))

    # Barras horizontales (barh) porque los nombres de autores son largos
    bars = ax.barh(autores, cantidades, color=COLORS["primary"], edgecolor="white")

    # Poner el numero al final de cada barra
    for bar in bars:
        width = bar.get_width()
        ax.text(
            width + 0.1,                        # Posicion X (un poco a la derecha)
            bar.get_y() + bar.get_height() / 2, # Posicion Y (centrado en la barra)
            str(int(width)),                     # El numero
            va="center",                         # Alineacion vertical: centrado
            fontsize=10,
            fontweight="bold",
        )

    ax.set_title("Libros por Autor", fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("Cantidad de Libros", fontsize=11)
    ax.spines["top"].set_visible(False)          # Quitar borde superior
    ax.spines["right"].set_visible(False)        # Quitar borde derecho

    plt.tight_layout()

    if output_path:
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
        print(f"Grafico guardado en: {output_path}")

    plt.show()
    plt.close(fig)
```

### Barras verticales (para pocas categorias)

```python
def grafico_disponibilidad(datos: dict[str, int]) -> None:
    """Grafico de barras verticales: disponibles vs prestados.

    Args:
        datos: {"Disponibles": 15, "Prestados": 8}
    """
    categorias = list(datos.keys())
    valores = list(datos.values())
    colores = [COLORS["secondary"], COLORS["danger"]]

    fig, ax = plt.subplots(figsize=(6, 5))

    bars = ax.bar(categorias, valores, color=colores, width=0.5, edgecolor="white")

    # Poner numeros arriba de cada barra
    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,   # Centrado horizontal
            height + 0.3,                          # Un poco arriba de la barra
            str(int(height)),
            ha="center",                           # Alineacion horizontal: centrado
            fontsize=12,
            fontweight="bold",
        )

    ax.set_title("Estado de los Libros", fontsize=14, fontweight="bold", pad=15)
    ax.set_ylabel("Cantidad", fontsize=11)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    plt.show()
    plt.close(fig)
```

### Anatomia de una barra

```
ax.bar(categorias, valores, color, width, edgecolor)
  |       |           |       |      |       |
  |       |           |       |      |       Borde de la barra
  |       |           |       |      Ancho (0.0 a 1.0)
  |       |           |       Color de relleno
  |       |           Altura de cada barra (los numeros)
  |       Etiquetas del eje X
  El area de dibujo

ax.barh(...)    = barras HORIZONTALES (la h es de "horizontal")
ax.bar(...)     = barras VERTICALES
```

---

## 7. Paso 5: Graficos de pastel (pie)

Ideal para mostrar proporciones (que porcentaje del total es cada parte).

### Ejemplo: proporcion disponibles vs prestados

```python
def grafico_pastel_disponibilidad(datos: dict[str, int]) -> None:
    """Grafico de pastel: proporcion de libros disponibles vs prestados.

    Args:
        datos: {"Disponibles": 15, "Prestados": 8}
    """
    if not datos or all(v == 0 for v in datos.values()):
        print("No hay datos para graficar.")
        return

    etiquetas = list(datos.keys())
    valores = list(datos.values())
    colores = [COLORS["secondary"], COLORS["danger"]]

    fig, ax = plt.subplots(figsize=(7, 7))

    wedges, texts, autotexts = ax.pie(
        valores,
        labels=etiquetas,
        colors=colores,
        autopct="%1.1f%%",          # Muestra el porcentaje con 1 decimal
        startangle=90,               # Empieza desde arriba (las 12 del reloj)
        textprops={"fontsize": 12},
        wedgeprops={"edgecolor": "white", "linewidth": 2},
    )

    # Hacer los porcentajes en negrita
    for autotext in autotexts:
        autotext.set_fontweight("bold")
        autotext.set_color("white")

    ax.set_title(
        "Proporcion de Disponibilidad",
        fontsize=14,
        fontweight="bold",
        pad=20,
    )

    plt.tight_layout()
    plt.show()
    plt.close(fig)
```

### Parametros del grafico de pastel

| Parametro       | Que hace                                   | Ejemplo               |
|-----------------|--------------------------------------------|-----------------------|
| `labels`        | Nombres de cada porcion                    | `["A", "B", "C"]`    |
| `autopct`       | Formato del porcentaje                     | `"%1.1f%%"` = 65.2%  |
| `startangle`    | Desde donde empieza a dibujar (grados)     | `90` = arriba         |
| `explode`       | Separar una porcion del centro             | `(0.05, 0, 0)`       |
| `shadow`        | Sombra detras del pastel                   | `True`                |
| `wedgeprops`    | Estilo de cada porcion                     | Borde blanco          |

### Cuando usar pastel y cuando NO

```
USAR pastel cuando:
  - Tienes 2 a 5 categorias
  - Quieres mostrar proporciones del total
  - Los valores son significativamente diferentes

NO usar pastel cuando:
  - Tienes mas de 6 categorias (queda ilegible)
  - Los valores son muy parecidos (dificil de comparar)
  - Quieres comparar entre grupos distintos (usar barras)
```

---

## 8. Paso 6: Graficos de linea (evolucion en el tiempo)

Ideal para mostrar como algo cambia a lo largo del tiempo.

### Ejemplo: prestamos por mes

```python
def grafico_prestamos_por_mes(datos: dict[str, int]) -> None:
    """Grafico de linea: evolucion de prestamos por mes.

    Args:
        datos: {"2026-01": 12, "2026-02": 8, "2026-03": 15}
    """
    if not datos:
        print("No hay datos para graficar.")
        return

    meses = list(datos.keys())
    cantidades = list(datos.values())

    fig, ax = plt.subplots(figsize=(10, 5))

    ax.plot(
        meses,
        cantidades,
        color=COLORS["primary"],
        marker="o",                  # Circulo en cada punto
        linewidth=2,
        markersize=8,
        markerfacecolor="white",     # Circulo blanco por dentro
        markeredgewidth=2,           # Borde grueso del circulo
    )

    # Area sombreada debajo de la linea (da efecto profesional)
    ax.fill_between(meses, cantidades, alpha=0.1, color=COLORS["primary"])

    # Numeros arriba de cada punto
    for i, cantidad in enumerate(cantidades):
        ax.text(
            i, cantidad + 0.5,
            str(cantidad),
            ha="center",
            fontsize=10,
            fontweight="bold",
        )

    ax.set_title(
        "Prestamos por Mes",
        fontsize=14,
        fontweight="bold",
        pad=15,
    )
    ax.set_xlabel("Mes", fontsize=11)
    ax.set_ylabel("Cantidad de Prestamos", fontsize=11)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Rotar las etiquetas del eje X si son largas
    plt.xticks(rotation=45, ha="right")

    plt.tight_layout()
    plt.show()
    plt.close(fig)
```

### Parametros de la linea

| Parametro           | Que hace                           | Ejemplo               |
|---------------------|------------------------------------|-----------------------|
| `color`             | Color de la linea                  | `"#2563EB"`           |
| `linewidth`         | Grosor de la linea                 | `2`                   |
| `linestyle`         | Estilo de la linea                 | `"-"`, `"--"`, `":"` |
| `marker`            | Forma del punto                    | `"o"`, `"s"`, `"^"`  |
| `markersize`        | Tamano del punto                   | `8`                   |
| `markerfacecolor`   | Color interior del punto           | `"white"`             |
| `alpha`             | Transparencia (0 a 1)              | `0.1`                 |

### Estilos de linea

```
"-"     linea solida         ___________
"--"    linea punteada       _ _ _ _ _ _
":"     linea de puntos      ...........
"-."    linea punto-raya     _._._._._._
```

### Marcadores (formas de los puntos)

```
"o"     circulo
"s"     cuadrado
"^"     triangulo
"D"     diamante
"*"     estrella
"+"     cruz
"x"     equis
```

---

## 9. Paso 7: Graficos combinados (subplots)

Multiples graficos en una sola ventana. Ideal para dashboards.

### Ejemplo: resumen completo de la biblioteca

```python
def dashboard_biblioteca(
    disponibilidad: dict[str, int],
    por_autor: dict[str, int],
    por_mes: dict[str, int],
    top_personas: list[tuple[str, int]],
) -> None:
    """Dashboard con 4 graficos en una sola ventana.

    Args:
        disponibilidad: {"Disponibles": 15, "Prestados": 8}
        por_autor: {"Cervantes": 3, "Borges": 5}
        por_mes: {"2026-01": 12, "2026-02": 8}
        top_personas: [("Juan", 8), ("Ana", 5)]
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    # axes es una matriz 2x2:
    #   axes[0][0] = arriba izquierda
    #   axes[0][1] = arriba derecha
    #   axes[1][0] = abajo izquierda
    #   axes[1][1] = abajo derecha

    # --- Grafico 1: Pastel de disponibilidad (arriba izquierda) ---
    ax1 = axes[0][0]
    if disponibilidad and any(v > 0 for v in disponibilidad.values()):
        colores_disp = [COLORS["secondary"], COLORS["danger"]]
        ax1.pie(
            disponibilidad.values(),
            labels=disponibilidad.keys(),
            colors=colores_disp,
            autopct="%1.1f%%",
            startangle=90,
            wedgeprops={"edgecolor": "white"},
        )
    ax1.set_title("Disponibilidad", fontweight="bold")

    # --- Grafico 2: Barras por autor (arriba derecha) ---
    ax2 = axes[0][1]
    if por_autor:
        ordenado = dict(sorted(por_autor.items(), key=lambda x: x[1]))
        ax2.barh(
            list(ordenado.keys()),
            list(ordenado.values()),
            color=COLORS["primary"],
        )
    ax2.set_title("Libros por Autor", fontweight="bold")
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)

    # --- Grafico 3: Linea por mes (abajo izquierda) ---
    ax3 = axes[1][0]
    if por_mes:
        ax3.plot(
            list(por_mes.keys()),
            list(por_mes.values()),
            color=COLORS["accent"],
            marker="o",
            linewidth=2,
        )
        ax3.fill_between(
            list(por_mes.keys()),
            list(por_mes.values()),
            alpha=0.1,
            color=COLORS["accent"],
        )
        ax3.tick_params(axis="x", rotation=45)
    ax3.set_title("Prestamos por Mes", fontweight="bold")
    ax3.spines["top"].set_visible(False)
    ax3.spines["right"].set_visible(False)

    # --- Grafico 4: Barras de personas activas (abajo derecha) ---
    ax4 = axes[1][1]
    if top_personas:
        nombres = [p[0] for p in top_personas]
        conteos = [p[1] for p in top_personas]
        ax4.barh(nombres, conteos, color=COLORS["accent"])
    ax4.set_title("Personas mas Activas", fontweight="bold")
    ax4.spines["top"].set_visible(False)
    ax4.spines["right"].set_visible(False)

    # Titulo general del dashboard
    fig.suptitle(
        "Dashboard - Biblioteca",
        fontsize=16,
        fontweight="bold",
        y=1.02,
    )

    plt.tight_layout()
    plt.show()
    plt.close(fig)
```

### Como funciona subplots

```python
# Un solo grafico
fig, ax = plt.subplots()

# Dos graficos lado a lado (1 fila, 2 columnas)
fig, axes = plt.subplots(1, 2)
# axes[0] = izquierda
# axes[1] = derecha

# Cuatro graficos en cuadricula (2 filas, 2 columnas)
fig, axes = plt.subplots(2, 2)
# axes[0][0] = arriba izquierda
# axes[0][1] = arriba derecha
# axes[1][0] = abajo izquierda
# axes[1][1] = abajo derecha

# Tres graficos en una fila
fig, axes = plt.subplots(1, 3, figsize=(15, 5))
```

---

## 10. Paso 8: Exportar graficos a imagen

### Guardar con savefig

```python
# Guardar en PNG (el mas comun)
fig.savefig("reporte.png", dpi=150, bbox_inches="tight")

# Guardar en PDF (para imprimir)
fig.savefig("reporte.pdf", bbox_inches="tight")

# Guardar en SVG (para web, escala sin perder calidad)
fig.savefig("reporte.svg", bbox_inches="tight")
```

### Parametros de savefig

| Parametro        | Que hace                               | Valor recomendado    |
|------------------|----------------------------------------|----------------------|
| `dpi`            | Resolucion (puntos por pulgada)        | 150 (pantalla), 300 (imprimir) |
| `bbox_inches`    | Recortar bordes blancos                | `"tight"` siempre    |
| `facecolor`      | Color de fondo                         | `"white"` por defecto|
| `transparent`    | Fondo transparente                     | `True` para web      |

### Patron para guardar en una carpeta de reportes

```python
from pathlib import Path

REPORTS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "reports"


def _ensure_reports_dir() -> Path:
    """Crea la carpeta de reportes si no existe."""
    REPORTS_DIR.mkdir(exist_ok=True)
    return REPORTS_DIR


def guardar_grafico(fig: plt.Figure, nombre: str) -> Path:
    """Guarda un grafico y devuelve la ruta del archivo."""
    carpeta = _ensure_reports_dir()
    ruta = carpeta / f"{nombre}.png"
    fig.savefig(ruta, dpi=150, bbox_inches="tight")
    return ruta
```

---

## 11. Paso 9: Tablas formateadas en consola

A veces no necesitas un grafico. Una tabla bien formateada
en la consola es suficiente y mas rapida.

### Tabla basica con f-strings

```python
def mostrar_tabla_autores(datos: list[tuple[str, int]]) -> None:
    """Muestra un ranking de autores en tabla formateada.

    Args:
        datos: [("Borges", 5), ("Cervantes", 3)]
    """
    if not datos:
        print("No hay datos.")
        return

    # Encabezado
    print(f"\n{'#':<4} {'Autor':<30} {'Libros':>8}")
    print("-" * 44)

    # Filas
    for posicion, (autor, cantidad) in enumerate(datos, start=1):
        print(f"{posicion:<4} {autor:<30} {cantidad:>8}")

    # Total
    total = sum(cantidad for _, cantidad in datos)
    print("-" * 44)
    print(f"{'':4} {'Total':<30} {total:>8}")
```

### Resultado en consola

```
#    Autor                          Libros
--------------------------------------------
1    Borges                              5
2    Cervantes                           3
3    Garcia Marquez                      2
--------------------------------------------
     Total                              10
```

### Tabla con barras ASCII (pseudo-grafico en consola)

```python
def mostrar_barras_consola(datos: dict[str, int], ancho_max: int = 30) -> None:
    """Muestra un grafico de barras en la consola usando caracteres.

    Args:
        datos: {"Borges": 5, "Cervantes": 3}
        ancho_max: Ancho maximo de la barra en caracteres.
    """
    if not datos:
        print("No hay datos.")
        return

    valor_max = max(datos.values())
    if valor_max == 0:
        print("Todos los valores son cero.")
        return

    print()
    for nombre, valor in sorted(datos.items(), key=lambda x: -x[1]):
        proporcion = valor / valor_max
        largo_barra = int(proporcion * ancho_max)
        barra = "#" * largo_barra
        print(f"  {nombre:<20} {barra} {valor}")
    print()
```

### Resultado en consola

```
  Borges               ############################## 5
  Cervantes            ################## 3
  Garcia Marquez       ############ 2
```

### Formato de alineacion en f-strings

```
{valor:<20}    Alinear a la IZQUIERDA, 20 caracteres de ancho
{valor:>10}    Alinear a la DERECHA, 10 caracteres de ancho
{valor:^15}    CENTRAR, 15 caracteres de ancho
{valor:>8.1f}  Derecha, 8 de ancho, 1 decimal (para float)
{valor:>6d}    Derecha, 6 de ancho (para enteros)
{valor:>8.1%}  Derecha, como porcentaje con 1 decimal
```

---

## 12. Paso 10: Integrar todo en el CLI

### Menu de reportes

```python
"""CLI para la generacion de reportes."""

from __future__ import annotations

from pathlib import Path

from src.mi_app.application.services.reporte_service import ReporteService
from src.mi_app.infrastructure.graphics.chart_generator import (
    dashboard_biblioteca,
    grafico_disponibilidad,
    grafico_libros_por_autor,
    grafico_pastel_disponibilidad,
    grafico_prestamos_por_mes,
)


class ReporteCLI:

    MENU = (
        "\n--- Reportes ---\n"
        "1. Disponibilidad de libros (barras)\n"
        "2. Disponibilidad de libros (pastel)\n"
        "3. Libros por autor\n"
        "4. Prestamos por mes\n"
        "5. Personas mas activas (tabla)\n"
        "6. Promedio de dias de prestamo\n"
        "7. Dashboard completo\n"
        "0. Volver\n"
    )

    def __init__(self, service: ReporteService) -> None:
        self._service = service

    def run(self) -> None:
        actions = {
            "1": self._disponibilidad_barras,
            "2": self._disponibilidad_pastel,
            "3": self._libros_por_autor,
            "4": self._prestamos_por_mes,
            "5": self._personas_activas,
            "6": self._promedio_dias,
            "7": self._dashboard,
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
            action()

    def _disponibilidad_barras(self) -> None:
        datos = self._service.reporte_disponibilidad()
        if not datos:
            print("\nNo hay libros registrados.")
            return
        grafico_disponibilidad(datos)

    def _disponibilidad_pastel(self) -> None:
        datos = self._service.reporte_disponibilidad()
        if not datos:
            print("\nNo hay libros registrados.")
            return
        grafico_pastel_disponibilidad(datos)

    def _libros_por_autor(self) -> None:
        datos = self._service.reporte_libros_por_autor()
        if not datos:
            print("\nNo hay libros registrados.")
            return
        grafico_libros_por_autor(datos)

    def _prestamos_por_mes(self) -> None:
        datos = self._service.reporte_prestamos_por_mes()
        if not datos:
            print("\nNo hay prestamos registrados.")
            return
        grafico_prestamos_por_mes(datos)

    def _personas_activas(self) -> None:
        datos = self._service.reporte_personas_activas(top=10)
        if not datos:
            print("\nNo hay prestamos registrados.")
            return

        # Tabla en consola (no necesita grafico)
        print(f"\n{'#':<4} {'Persona':<30} {'Prestamos':>10}")
        print("-" * 46)
        for i, (nombre, cantidad) in enumerate(datos, start=1):
            print(f"{i:<4} {nombre:<30} {cantidad:>10}")

    def _promedio_dias(self) -> None:
        promedio = self._service.reporte_promedio_dias()
        if promedio == 0:
            print("\nNo hay prestamos devueltos para calcular.")
            return
        print(f"\nPromedio de dias por prestamo: {promedio:.1f} dias")

    def _dashboard(self) -> None:
        disponibilidad = self._service.reporte_disponibilidad()
        por_autor = self._service.reporte_libros_por_autor()
        por_mes = self._service.reporte_prestamos_por_mes()
        personas = self._service.reporte_personas_activas(top=5)

        dashboard_biblioteca(disponibilidad, por_autor, por_mes, personas)
```

### Conectar en main.py

```python
# Agregar estas lineas al main.py existente:

from src.mi_app.application.services.reporte_service import ReporteService
from src.mi_app.infrastructure.cli.reporte_cli import ReporteCLI

def main() -> None:
    connection = get_connection(_DB_PATH)
    initialize_database(connection)

    libro_repo = SQLiteLibroRepository(connection)
    prestamo_repo = SQLitePrestamoRepository(connection)

    libro_service = LibroService(libro_repo)
    prestamo_service = PrestamoService(prestamo_repo)
    reporte_service = ReporteService(libro_repo, prestamo_repo)    # NUEVO

    libro_cli = LibroCLI(libro_service)
    prestamo_cli = PrestamoCLI(prestamo_service)
    reporte_cli = ReporteCLI(reporte_service)                      # NUEVO

    menu = MainMenu(libro_cli, prestamo_cli, reporte_cli)          # AGREGAR
    try:
        menu.run()
    finally:
        connection.close()
```

### Actualizar el menu principal

```python
MENU = (
    "1. Gestion de Libros\n"
    "2. Gestion de Prestamos\n"
    "3. Reportes y Graficos\n"       # NUEVO
    "0. Salir\n"
)

actions = {
    "1": self._libro_cli.run,
    "2": self._prestamo_cli.run,
    "3": self._reporte_cli.run,      # NUEVO
}
```

---

## 13. Paso 11: Consultas SQL avanzadas para reportes

A veces es mejor hacer el calculo DIRECTAMENTE en SQL
en vez de traer todos los datos a Python. Es mas rapido
cuando la tabla tiene miles de filas.

### Consultas utiles para reportes

```python
"""Metodos adicionales para el repositorio de libros."""


def count_by_disponibilidad(self) -> dict[str, int]:
    """Cuenta libros agrupados por disponibilidad directo en SQL."""
    sql = """
        SELECT disponible, COUNT(*) as cantidad
        FROM libros
        GROUP BY disponible
    """
    rows = self._conn.execute(sql).fetchall()
    resultado = {"Disponibles": 0, "Prestados": 0}
    for row in rows:
        clave = "Disponibles" if row["disponible"] else "Prestados"
        resultado[clave] = row["cantidad"]
    return resultado


def count_by_autor(self) -> list[tuple[str, int]]:
    """Cuenta libros por autor, ordenados de mayor a menor."""
    sql = """
        SELECT autor, COUNT(*) as cantidad
        FROM libros
        GROUP BY autor
        ORDER BY cantidad DESC
    """
    rows = self._conn.execute(sql).fetchall()
    return [(row["autor"], row["cantidad"]) for row in rows]
```

### SQL para reportes de prestamos

```python
"""Metodos adicionales para el repositorio de prestamos."""


def count_by_month(self) -> dict[str, int]:
    """Cuenta prestamos agrupados por mes."""
    sql = """
        SELECT strftime('%Y-%m', fecha_prestamo) as mes,
               COUNT(*) as cantidad
        FROM prestamos
        GROUP BY mes
        ORDER BY mes
    """
    rows = self._conn.execute(sql).fetchall()
    return {row["mes"]: row["cantidad"] for row in rows}


def top_borrowers(self, limit: int = 5) -> list[tuple[str, int]]:
    """Las personas que mas libros pidieron."""
    sql = """
        SELECT nombre_persona, COUNT(*) as cantidad
        FROM prestamos
        GROUP BY nombre_persona
        ORDER BY cantidad DESC
        LIMIT ?
    """
    rows = self._conn.execute(sql, (limit,)).fetchall()
    return [(row["nombre_persona"], row["cantidad"]) for row in rows]


def average_loan_days(self) -> float:
    """Promedio de dias de prestamos devueltos."""
    sql = """
        SELECT AVG(julianday(fecha_devolucion) - julianday(fecha_prestamo))
               as promedio
        FROM prestamos
        WHERE fecha_devolucion IS NOT NULL
    """
    row = self._conn.execute(sql).fetchone()
    return row["promedio"] or 0.0
```

### SQL clave para reportes

| Funcion SQL          | Que hace                          | Ejemplo                           |
|----------------------|-----------------------------------|-----------------------------------|
| `COUNT(*)`           | Contar filas                      | Cuantos libros hay                |
| `SUM(campo)`         | Sumar valores                     | Total de prestamos                |
| `AVG(campo)`         | Promedio                          | Promedio de dias                  |
| `MIN(campo)`         | Valor minimo                      | Fecha mas antigua                 |
| `MAX(campo)`         | Valor maximo                      | Fecha mas reciente                |
| `GROUP BY campo`     | Agrupar filas iguales             | Contar POR autor                  |
| `ORDER BY campo DESC`| Ordenar de mayor a menor          | Top autores                       |
| `LIMIT n`            | Solo las primeras n filas         | Top 5                             |
| `HAVING COUNT(*) > n`| Filtrar grupos                    | Autores con mas de 3 libros       |
| `strftime('%Y-%m', fecha)` | Extraer mes de una fecha    | Agrupar por mes                   |
| `julianday(fecha)`   | Fecha como numero (para restar)   | Dias entre dos fechas             |

### Python puro vs SQL: cuando usar cada uno

| Situacion                           | Usar Python puro | Usar SQL       |
|-------------------------------------|------------------|----------------|
| Menos de 1000 registros             | OK               | OK             |
| Miles de registros                  | Lento            | Rapido         |
| Calculo simple (contar, promediar)  | OK               | Mejor en SQL   |
| Logica compleja con ifs             | Mejor en Python  | Complicado     |
| Necesitas objetos Python despues    | Necesario        | Solo numeros   |

---

## 14. Paso 12: El archivo completo de chart_generator

Resumen de la estructura completa del generador de graficos:

```python
"""Generador de graficos para reportes de la biblioteca."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt

# --- Configuracion de estilo global ---

COLORS = {
    "primary": "#2563EB",
    "secondary": "#10B981",
    "accent": "#F59E0B",
    "danger": "#EF4444",
    "neutral": "#6B7280",
}

PALETTE = ["#2563EB", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6", "#EC4899"]

REPORTS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "reports"


def _setup_style() -> None:
    """Aplica un estilo global limpio a todos los graficos."""
    plt.rcParams.update({
        "font.size": 11,
        "axes.titlesize": 14,
        "axes.labelsize": 11,
        "figure.facecolor": "white",
        "axes.facecolor": "#FAFAFA",
        "axes.grid": True,
        "grid.alpha": 0.3,
        "grid.linestyle": "--",
    })


def _save_if_needed(fig: plt.Figure, output_path: Optional[Path]) -> None:
    """Guarda el grafico si se proporciona una ruta."""
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
        print(f"Grafico guardado en: {output_path}")


def _clean_axes(ax: plt.Axes) -> None:
    """Quita bordes innecesarios de un grafico."""
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


# --- Funciones de graficos individuales ---

def grafico_disponibilidad(datos, output_path=None):
    """Barras verticales: disponibles vs prestados."""
    ...

def grafico_pastel_disponibilidad(datos, output_path=None):
    """Pastel: proporcion disponibles vs prestados."""
    ...

def grafico_libros_por_autor(datos, output_path=None):
    """Barras horizontales: libros por cada autor."""
    ...

def grafico_prestamos_por_mes(datos, output_path=None):
    """Linea: evolucion de prestamos mes a mes."""
    ...

def dashboard_biblioteca(disponibilidad, por_autor, por_mes, top_personas):
    """Dashboard con 4 graficos combinados."""
    ...


# Aplicar estilo al importar el modulo
_setup_style()
```

### El patron de cada funcion de grafico

```
1. Verificar que hay datos (if not datos: return)
2. Preparar los datos (ordenar, extraer listas)
3. Crear figura: fig, ax = plt.subplots(figsize=(...))
4. Dibujar: ax.bar / ax.barh / ax.plot / ax.pie
5. Decorar: titulo, etiquetas, numeros sobre las barras
6. Limpiar: quitar bordes (spines), ajustar layout
7. Guardar si se pidio: _save_if_needed(fig, output_path)
8. Mostrar: plt.show()
9. Cerrar: plt.close(fig)
```

---

## 15. Receta: como pensar un reporte nuevo

Cuando quieras agregar un reporte nuevo, sigue estos pasos:

### Paso 1: La pregunta

Escribe en lenguaje natural que quieres saber:

```
"Quiero saber cuantos prestamos se hacen cada dia de la semana"
```

### Paso 2: Los datos que necesitas

```
Necesito: lista de prestamos con sus fechas
Fuente: prestamo_repository.get_all()
```

### Paso 3: La funcion de procesamiento

```python
def prestamos_por_dia_semana(prestamos: list[Prestamo]) -> dict[str, int]:
    dias = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"]
    conteo = {dia: 0 for dia in dias}
    for p in prestamos:
        dia = dias[p.fecha_prestamo.weekday()]
        conteo[dia] += 1
    return conteo
```

### Paso 4: El metodo en el servicio

```python
def reporte_por_dia_semana(self) -> dict[str, int]:
    prestamos = self._prestamo_repo.get_all()
    return dp.prestamos_por_dia_semana(prestamos)
```

### Paso 5: El grafico

```python
def grafico_por_dia_semana(datos: dict[str, int]) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(datos.keys(), datos.values(), color=PALETTE[:7])
    ax.set_title("Prestamos por Dia de la Semana")
    _clean_axes(ax)
    plt.tight_layout()
    plt.show()
    plt.close(fig)
```

### Paso 6: Agregar al CLI

```python
# En el diccionario de acciones:
"8": self._por_dia_semana,

# El metodo:
def _por_dia_semana(self) -> None:
    datos = self._service.reporte_por_dia_semana()
    grafico_por_dia_semana(datos)
```

### Resumen del patron

```
Pregunta  -->  Datos  -->  Funcion pura  -->  Servicio  -->  Grafico  -->  CLI
```

Siempre es el mismo flujo. Cada pieza hace una sola cosa.

---

## 16. Errores comunes al graficar

### Error 1: graficar datos vacios

```python
# MAL: no verificar, da error o grafico vacio
ax.bar([], [])

# BIEN: verificar primero
if not datos:
    print("No hay datos para graficar.")
    return
```

### Error 2: no cerrar la figura

```python
# MAL: la figura queda en memoria
plt.show()
# Si haces esto 100 veces, se acumula mucha memoria

# BIEN: cerrar despues de mostrar
plt.show()
plt.close(fig)
```

### Error 3: etiquetas del eje X que se superponen

```python
# MAL: textos largos se montan unos sobre otros
ax.bar(["Nombre Largo 1", "Nombre Largo 2", ...], valores)

# BIEN: rotar las etiquetas
plt.xticks(rotation=45, ha="right")

# O MEJOR: usar barras horizontales (barh) para textos largos
ax.barh(nombres, valores)
```

### Error 4: colores sin contraste

```python
# MAL: colores muy parecidos
colores = ["#AAAAAA", "#BBBBBB", "#CCCCCC"]

# BIEN: colores distintos y con proposito
colores = [COLORS["secondary"], COLORS["danger"]]   # Verde vs Rojo
```

### Error 5: olvidar tight_layout

```python
# MAL: los titulos se cortan en los bordes
plt.show()

# BIEN: ajustar antes de mostrar
plt.tight_layout()
plt.show()
```

### Error 6: grafico de pastel con demasiadas porciones

```python
# MAL: 15 porciones, ilegible
ax.pie(valores_15_categorias, labels=etiquetas_15)

# BIEN: agrupar las menores en "Otros"
def agrupar_menores(datos: dict[str, int], top: int = 5) -> dict[str, int]:
    ordenado = sorted(datos.items(), key=lambda x: -x[1])
    principales = dict(ordenado[:top])
    resto = sum(v for _, v in ordenado[top:])
    if resto > 0:
        principales["Otros"] = resto
    return principales
```

---

## 17. Referencia rapida de matplotlib

### Tipos de grafico

| Metodo               | Tipo de grafico         | Mejor para                        |
|----------------------|-------------------------|-----------------------------------|
| `ax.bar(x, y)`      | Barras verticales       | Comparar pocas categorias         |
| `ax.barh(y, x)`     | Barras horizontales     | Categorias con nombres largos     |
| `ax.plot(x, y)`     | Linea                   | Cambio en el tiempo               |
| `ax.pie(valores)`   | Pastel                  | Proporciones (2-5 partes)         |
| `ax.scatter(x, y)`  | Dispersion              | Relacion entre 2 variables        |
| `ax.hist(datos)`    | Histograma              | Distribucion de valores           |

### Decoracion

| Metodo / Propiedad               | Que hace                              |
|-----------------------------------|---------------------------------------|
| `ax.set_title("Titulo")`         | Titulo del grafico                    |
| `ax.set_xlabel("Eje X")`         | Etiqueta del eje X                    |
| `ax.set_ylabel("Eje Y")`         | Etiqueta del eje Y                    |
| `ax.legend()`                     | Mostrar leyenda                       |
| `ax.set_xlim(0, 100)`            | Rango del eje X                       |
| `ax.set_ylim(0, 50)`             | Rango del eje Y                       |
| `ax.grid(True)`                   | Mostrar cuadricula                    |
| `ax.spines["top"].set_visible(False)` | Quitar borde superior            |
| `plt.xticks(rotation=45)`        | Rotar etiquetas del eje X             |

### Propiedades de texto

| Propiedad           | Valores comunes                        |
|---------------------|----------------------------------------|
| `fontsize`          | `10`, `12`, `14`, `16`                 |
| `fontweight`        | `"normal"`, `"bold"`                   |
| `ha` (horizontal)   | `"left"`, `"center"`, `"right"`       |
| `va` (vertical)     | `"top"`, `"center"`, `"bottom"`       |
| `color`             | `"black"`, `"white"`, `"#2563EB"`     |

### Tamanos de figura recomendados

| Tipo de grafico        | figsize           | Cuando                         |
|------------------------|-------------------|--------------------------------|
| Grafico simple         | `(8, 5)`          | Un grafico solo                |
| Barras horizontales    | `(10, 6)`         | Muchas categorias              |
| Pastel                 | `(7, 7)`          | Siempre cuadrado               |
| Dashboard 2x2          | `(14, 10)`        | Cuatro graficos juntos         |
| Linea temporal         | `(10, 5)`         | Datos a lo largo del tiempo    |

### Colores en formato hexadecimal

```
Rojos:      #EF4444 (suave)    #DC2626 (intenso)    #FCA5A5 (claro)
Azules:     #2563EB (suave)    #1D4ED8 (intenso)    #93C5FD (claro)
Verdes:     #10B981 (suave)    #059669 (intenso)    #6EE7B7 (claro)
Amarillos:  #F59E0B (suave)    #D97706 (intenso)    #FCD34D (claro)
Morados:    #8B5CF6 (suave)    #7C3AED (intenso)    #C4B5FD (claro)
Grises:     #6B7280 (suave)    #374151 (intenso)    #D1D5DB (claro)
```

---

## 18. Siguiente paso despues de esto

### Tu ruta de aprendizaje ahora

```
Ya completaste:
  [x] CRUD con arquitectura hexagonal
  [x] Excepciones, modelos, puertos, DTOs, servicios
  [x] Repositorios SQLite, CLI, main.py, tests
  [x] Procesamiento de datos con funciones puras
  [x] Graficos con matplotlib (barras, linea, pastel, dashboard)
  [x] Tablas formateadas en consola
  [x] Consultas SQL avanzadas para reportes
  [x] Exportar graficos a imagen

Siguiente nivel:
  [ ] Interfaz web con Flask o FastAPI (en vez de consola)
  [ ] Graficos interactivos con Plotly (zoom, hover, filtros)
  [ ] Base de datos real con PostgreSQL o MySQL
  [ ] Docker para empaquetar tu aplicacion
  [ ] Frontend con HTML/CSS/JavaScript para mostrar graficos en navegador
```

### El flujo completo que ya dominas

```
USUARIO
  |
  v
CLI/Menu  (elige que hacer)
  |
  v
Servicio  (orquesta la logica)
  |
  v
Repositorio  (accede a la BD)
  |
  v
Base de Datos  (guarda los datos)
  |
  v
Procesamiento  (funciones puras que calculan)
  |
  v
Grafico / Tabla  (muestra los resultados)
  |
  v
USUARIO  (ve el resultado)
```

Ese flujo es el mismo en una aplicacion web, movil o de escritorio.
Lo que cambia es la capa de presentacion (CLI, web, app movil).
El dominio, los servicios y los repositorios se reutilizan tal cual.
Eso es lo poderoso de la arquitectura hexagonal.
