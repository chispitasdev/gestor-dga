# Diagrama de Clases -- Capa Application

Diagrama UML de clases de la capa application del sistema DGA.
Contiene los DTOs (objetos de transferencia de datos) y los servicios
que orquestan los casos de uso CRUD.

Esta capa depende unicamente de domain (puertos, modelos, excepciones).
Nunca depende de infrastructure.

```mermaid
classDiagram
    direction TB

    %% ================================================================
    %% DTOs -- Transformador
    %% ================================================================

    class CreateTransformerDTO {
        <<frozen dataclass>>
        +str name
    }

    class UpdateTransformerDTO {
        <<frozen dataclass>>
        +int id
        +str name
    }

    %% ================================================================
    %% DTOs -- Muestra
    %% ================================================================

    class CreateSampleDTO {
        <<frozen dataclass>>
        +str sample_code
        +int transformer_id
        +date extraction_date
        +float h2
        +float ch4
        +float c2h6
        +float c2h4
        +float c2h2
        +float co
        +float co2
        +float o2
        +float n2
    }

    class UpdateSampleDTO {
        <<frozen dataclass>>
        +int id
        +str sample_code
        +int transformer_id
        +date extraction_date
        +date diagnosis_date
        +float h2
        +float ch4
        +float c2h6
        +float c2h4
        +float c2h2
        +float co
        +float co2
        +float o2
        +float n2
    }

    %% ================================================================
    %% SERVICIOS
    %% ================================================================

    class TransformerService {
        <<service>>
        -TransformerRepository _repository
        +register_transformer(CreateTransformerDTO) Transformer
        +list_transformers() list~Transformer~
        +get_transformer(int) Transformer
        +update_transformer(UpdateTransformerDTO) Transformer
        +remove_transformer(int) None
    }

    class SampleService {
        <<service>>
        -SampleRepository _sample_repo
        -TransformerRepository _transformer_repo
        +register_sample(CreateSampleDTO) Sample
        +list_samples() list~Sample~
        +get_sample(int) Sample
        +list_samples_by_transformer(int) list~Sample~
        +update_sample(UpdateSampleDTO) Sample
        +remove_sample(int) None
        -_validate_transformer_exists(int) None
        -_build_gas_reading(floats) GasReading
    }

    %% ================================================================
    %% PUERTOS DEL DOMINIO (referencias externas)
    %% ================================================================

    class TransformerRepository {
        <<interface>>
    }

    class SampleRepository {
        <<interface>>
    }

    %% ================================================================
    %% RELACIONES
    %% ================================================================

    %% Servicios dependen de puertos (DIP)
    TransformerService --> TransformerRepository : _repository
    SampleService --> SampleRepository : _sample_repo
    SampleService --> TransformerRepository : _transformer_repo

    %% Servicios consumen DTOs
    TransformerService ..> CreateTransformerDTO : recibe
    TransformerService ..> UpdateTransformerDTO : recibe
    SampleService ..> CreateSampleDTO : recibe
    SampleService ..> UpdateSampleDTO : recibe

    %% ================================================================
    %% ESTILOS
    %% ================================================================

    style CreateTransformerDTO fill:#d5f0d5,stroke:#337733,color:#000
    style UpdateTransformerDTO fill:#d5f0d5,stroke:#337733,color:#000
    style CreateSampleDTO fill:#d5f0d5,stroke:#337733,color:#000
    style UpdateSampleDTO fill:#d5f0d5,stroke:#337733,color:#000
    style TransformerService fill:#b8e6b8,stroke:#337733,color:#000
    style SampleService fill:#b8e6b8,stroke:#337733,color:#000
    style TransformerRepository fill:#e8eeff,stroke:#336699,color:#000
    style SampleRepository fill:#e8eeff,stroke:#336699,color:#000
```

## Leyenda

| Color       | Elemento            | Descripcion                                              |
|-------------|---------------------|----------------------------------------------------------|
| Verde claro | DTOs                | Objetos inmutables de transferencia de datos.            |
| Verde medio | Servicios           | Orquestadores de casos de uso CRUD.                      |
| Azul claro  | Puertos (domain)    | Interfaces abstractas importadas desde la capa domain.   |

## Relaciones UML utilizadas

| Simbolo                    | Tipo          | Significado                                            |
|----------------------------|---------------|--------------------------------------------------------|
| Linea continua con flecha  | Asociacion    | El servicio mantiene una referencia al puerto.         |
| Flecha punteada abierta    | Dependencia   | El servicio recibe el DTO como parametro de metodo.    |

## Notas de diseno

- Los servicios reciben puertos abstractos por constructor (DIP), no
  implementaciones concretas. Esto permite sustituir SQLite por cualquier
  otro adaptador sin modificar esta capa.
- Los DTOs son inmutables (frozen=True). Actuan como barrera entre la
  interfaz de usuario y el dominio, absorbiendo cambios de UI.
- **CreateSampleDTO** no incluye `diagnosis_date` porque se asigna
  automaticamente con la fecha actual al crear la entidad.
- **UpdateSampleDTO** si incluye `diagnosis_date` porque el usuario
  puede modificarla en una actualizacion.
