# Indice de Documentacion

Guias de aprendizaje y diagramas del proyecto DGA
(Dissolved Gas Analysis - Analisis de Gases Disueltos).

---

## Guias de Estudio (en orden)

Estudialas en este orden. Cada una se construye sobre la anterior.

| #  | Archivo                                                                  | Que aprendes                                    | Secciones | Lineas |
|----|--------------------------------------------------------------------------|-------------------------------------------------|-----------|--------|
| 01 | [01_pensamiento_programador.md](guias/01_pensamiento_programador.md)     | Como pensar antes de codificar, patrones mentales, habitos profesionales | 10 | 702  |
| 02 | [02_referencia_python_esencial.md](guias/02_referencia_python_esencial.md) | Todas las herramientas de Python que usa el proyecto (dataclass, ABC, excepciones, pytest, etc.) | 27 | 1578 |
| 03 | [03_crud_hexagonal_paso_a_paso.md](guias/03_crud_hexagonal_paso_a_paso.md) | Como construir un CRUD completo con arquitectura hexagonal, paso a paso con plantillas | 16 | 1173 |
| 04 | [04_habilidades_avanzadas.md](guias/04_habilidades_avanzadas.md)         | Leer codigo ajeno, depurar errores, ruta de aprendizaje a futuro | 3  | 417  |
| 05 | [05_procesamiento_y_graficos.md](guias/05_procesamiento_y_graficos.md)   | Procesar datos, generar graficos con matplotlib (barras, linea, pastel, dashboard) | 18 | 1577 |
| 06 | [06_api_rest_fastapi.md](guias/06_api_rest_fastapi.md)                   | Crear una API REST con FastAPI, schemas, endpoints, tests, CORS | 28 | 1859 |

**Total: 102 secciones, 7306 lineas de contenido.**

---

## Diagramas UML (Mermaid)

Diagramas de la arquitectura del proyecto DGA.

| #  | Archivo                                                                                    | Que muestra                                  |
|----|--------------------------------------------------------------------------------------------|----------------------------------------------|
| 00 | [00_file_block_diagram.md](uml_diagrams/00_file_block_diagram.md)                          | Estructura de archivos y carpetas            |
| 01 | [01_package_diagram.md](uml_diagrams/01_package_diagram.md)                                | Dependencias entre paquetes (capas)          |
| 02 | [02_class_diagram_domain.md](uml_diagrams/02_class_diagram_domain.md)                      | Clases de la capa de dominio                 |
| 03 | [03_class_diagram_application.md](uml_diagrams/03_class_diagram_application.md)            | Clases de la capa de aplicacion              |
| 04 | [04_class_diagram_infrastructure.md](uml_diagrams/04_class_diagram_infrastructure.md)      | Clases de la capa de infraestructura         |
| 05 | [05_sequence_diagram_register_sample.md](uml_diagrams/05_sequence_diagram_register_sample.md) | Flujo completo de registrar una muestra   |

---

## Estructura final de docs/

```
docs/
|-- INDICE.md                  <-- Este archivo (empieza aqui)
|
|-- guias/                     <-- Guias de estudio numeradas
|   |-- 01_pensamiento_programador.md
|   |-- 02_referencia_python_esencial.md
|   |-- 03_crud_hexagonal_paso_a_paso.md
|   |-- 04_habilidades_avanzadas.md
|   |-- 05_procesamiento_y_graficos.md
|   |-- 06_api_rest_fastapi.md
|
|-- uml_diagrams/              <-- Diagramas de arquitectura
    |-- 00_file_block_diagram.md
    |-- 01_package_diagram.md
    |-- 02_class_diagram_domain.md
    |-- 03_class_diagram_application.md
    |-- 04_class_diagram_infrastructure.md
    |-- 05_sequence_diagram_register_sample.md
```
