# Diagrama de Clases -- Capa Infrastructure

Diagrama UML de clases de la capa infrastructure del sistema DGA.
Contiene los adaptadores concretos: repositorios SQLite (salida) y
adaptadores CLI (entrada).

Cada adaptador implementa o consume contratos definidos en las capas
internas (domain y application), cumpliendo la regla de dependencia.

```mermaid
classDiagram
    direction TB

    %% ================================================================
    %% ADAPTADORES DE PERSISTENCIA (salida)
    %% ================================================================

    class SQLiteTransformerRepository {
        <<adapter>>
        -Connection _conn
        +create(Transformer) Transformer
        +get_by_id(int) Optional~Transformer~
        +get_all() list~Transformer~
        +update(Transformer) Transformer
        +delete(int) None
        -_row_to_entity(Row) Transformer
    }

    class SQLiteSampleRepository {
        <<adapter>>
        -Connection _conn
        +create(Sample) Sample
        +get_by_id(int) Optional~Sample~
        +get_by_transformer_id(int) list~Sample~
        +get_all() list~Sample~
        +update(Sample) Sample
        +delete(int) None
        -_row_to_entity(Row) Sample
        -_entity_to_params(Sample) tuple
    }

    %% ================================================================
    %% PUERTOS DEL DOMINIO (interfaces implementadas)
    %% ================================================================

    class TransformerRepository {
        <<interface>>
        +create(Transformer) Transformer
        +get_by_id(int) Optional~Transformer~
        +get_all() list~Transformer~
        +update(Transformer) Transformer
        +delete(int) None
    }

    class SampleRepository {
        <<interface>>
        +create(Sample) Sample
        +get_by_id(int) Optional~Sample~
        +get_by_transformer_id(int) list~Sample~
        +get_all() list~Sample~
        +update(Sample) Sample
        +delete(int) None
    }

    %% ================================================================
    %% ADAPTADORES CLI (entrada)
    %% ================================================================

    class MainMenu {
        <<adapter>>
        -TransformerCLI _transformer_cli
        -SampleCLI _sample_cli
        +run() None
    }

    class TransformerCLI {
        <<adapter>>
        -TransformerService _service
        +run() None
        -_create() None
        -_list_all() None
        -_get_by_id() None
        -_update() None
        -_delete() None
    }

    class SampleCLI {
        <<adapter>>
        -SampleService _sample_svc
        -TransformerService _transformer_svc
        +run() None
        -_create() None
        -_list_all() None
        -_get_by_id() None
        -_filter_by_transformer() None
        -_update() None
        -_delete() None
        -_read_date(str) date
        -_read_float(str) float
        -_read_gas_values() dict
        -_select_transformer_id() int
        -_display_sample(Sample) None
        -_display_samples_table(list) None
    }

    %% ================================================================
    %% SERVICIOS DE APLICACION (referencias consumidas)
    %% ================================================================

    class TransformerService {
        <<service>>
    }

    class SampleService {
        <<service>>
    }

    %% ================================================================
    %% RELACIONES
    %% ================================================================

    %% Realizacion: adaptadores implementan puertos
    SQLiteTransformerRepository ..|> TransformerRepository
    SQLiteSampleRepository ..|> SampleRepository

    %% Asociacion: CLI mantiene referencia a servicios
    MainMenu --> TransformerCLI : _transformer_cli
    MainMenu --> SampleCLI : _sample_cli
    TransformerCLI --> TransformerService : _service
    SampleCLI --> SampleService : _sample_svc
    SampleCLI --> TransformerService : _transformer_svc

    %% ================================================================
    %% ESTILOS
    %% ================================================================

    style SQLiteTransformerRepository fill:#ffe8cc,stroke:#cc7700,color:#000
    style SQLiteSampleRepository fill:#ffe8cc,stroke:#cc7700,color:#000
    style MainMenu fill:#ffe8cc,stroke:#cc7700,color:#000
    style TransformerCLI fill:#ffe8cc,stroke:#cc7700,color:#000
    style SampleCLI fill:#ffe8cc,stroke:#cc7700,color:#000
    style TransformerRepository fill:#e8eeff,stroke:#336699,color:#000
    style SampleRepository fill:#e8eeff,stroke:#336699,color:#000
    style TransformerService fill:#d5f0d5,stroke:#337733,color:#000
    style SampleService fill:#d5f0d5,stroke:#337733,color:#000
```

## Leyenda

| Color       | Elemento                 | Descripcion                                          |
|-------------|--------------------------|------------------------------------------------------|
| Naranja     | Adaptadores (infra)      | Clases concretas de persistencia y CLI.              |
| Azul claro  | Puertos (domain)         | Interfaces abstractas implementadas por los repos.   |
| Verde claro | Servicios (application)  | Clases consumidas por los adaptadores CLI.           |

## Relaciones UML utilizadas

| Simbolo                               | Tipo          | Significado                                           |
|----------------------------------------|---------------|-------------------------------------------------------|
| Linea punteada con triangulo vacio     | Realizacion   | El adaptador implementa la interfaz del puerto.       |
| Linea continua con flecha              | Asociacion    | El adaptador mantiene una referencia al componente.   |

## Notas de diseno

- Los repositorios SQLite implementan los puertos abstractos del dominio.
  Podrian sustituirse por PostgreSQL, MongoDB o un mock en memoria sin
  modificar ninguna otra capa.
- Los adaptadores CLI solo conocen servicios de aplicacion, nunca acceden
  directamente a repositorios ni a la base de datos.
- **MainMenu** coordina la navegacion entre **TransformerCLI** y **SampleCLI**
  sin conocer la logica de negocio.
- **SampleCLI** depende de dos servicios porque necesita listar transformadores
  disponibles al registrar o actualizar una muestra.
