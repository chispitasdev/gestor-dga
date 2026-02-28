# Diagrama de Clases -- Capa Domain

Diagrama UML de clases de la capa domain del sistema DGA.
Contiene las entidades, value objects, puertos abstractos y
excepciones que conforman el nucleo de negocio.

Ninguna clase de este diagrama depende de capas externas.

```mermaid
classDiagram
    direction TB

    %% ================================================================
    %% MODELOS (Entidades y Value Objects)
    %% ================================================================

    class GasReading {
        <<frozen dataclass>>
        +float h2
        +float ch4
        +float c2h6
        +float c2h4
        +float c2h2
        +float co
        +float co2
        +float o2
        +float n2
        +ClassVar~dict~ GAS_LABELS
        +field_names() tuple~str~
        +descriptive_labels() dict~str, str~
        +as_dict() dict~str, float~
    }

    class Transformer {
        <<dataclass>>
        +str name
        +Optional~int~ id
    }

    class Sample {
        <<dataclass>>
        +str sample_code
        +int transformer_id
        +date extraction_date
        +GasReading gas_reading
        +date diagnosis_date
        +Optional~int~ id
    }

    %% ================================================================
    %% PUERTOS (Interfaces abstractas)
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
    %% EXCEPCIONES
    %% ================================================================

    class DGADomainError {
        <<exception>>
    }

    class TransformerNotFoundError {
        <<exception>>
        +int transformer_id
    }

    class SampleNotFoundError {
        <<exception>>
        +int sample_id
    }

    class DuplicateTransformerError {
        <<exception>>
        +str name
    }

    class DuplicateSampleCodeError {
        <<exception>>
        +str sample_code
    }

    class InvalidGasValueError {
        <<exception>>
    }

    %% ================================================================
    %% RELACIONES
    %% ================================================================

    %% Composicion: Sample contiene un GasReading
    Sample *-- GasReading : gas_reading

    %% Puertos operan sobre entidades
    TransformerRepository ..> Transformer : opera sobre
    SampleRepository ..> Sample : opera sobre

    %% Jerarquia de excepciones
    DGADomainError <|-- TransformerNotFoundError
    DGADomainError <|-- SampleNotFoundError
    DGADomainError <|-- DuplicateTransformerError
    DGADomainError <|-- DuplicateSampleCodeError
    DGADomainError <|-- InvalidGasValueError

    %% ================================================================
    %% ESTILOS
    %% ================================================================

    style GasReading fill:#d0e0ff,stroke:#336699,color:#000
    style Transformer fill:#d0e0ff,stroke:#336699,color:#000
    style Sample fill:#d0e0ff,stroke:#336699,color:#000
    style TransformerRepository fill:#e8eeff,stroke:#336699,color:#000
    style SampleRepository fill:#e8eeff,stroke:#336699,color:#000
    style DGADomainError fill:#ffeaea,stroke:#cc4444,color:#000
    style TransformerNotFoundError fill:#ffeaea,stroke:#cc4444,color:#000
    style SampleNotFoundError fill:#ffeaea,stroke:#cc4444,color:#000
    style DuplicateTransformerError fill:#ffeaea,stroke:#cc4444,color:#000
    style DuplicateSampleCodeError fill:#ffeaea,stroke:#cc4444,color:#000
    style InvalidGasValueError fill:#ffeaea,stroke:#cc4444,color:#000
```

## Leyenda

| Color       | Elemento                       | Descripcion                                    |
|-------------|--------------------------------|------------------------------------------------|
| Azul fuerte | Modelos (entidades / VO)       | Clases con datos e invariantes de negocio.     |
| Azul claro  | Puertos (interfaces)           | Contratos abstractos (ABC) sin implementacion. |
| Rojo claro  | Excepciones                    | Errores especificos del dominio.               |

## Relaciones UML utilizadas

| Simbolo                     | Tipo           | Significado                                         |
|-----------------------------|----------------|-----------------------------------------------------|
| Linea con rombo negro       | Composicion    | Sample posee y controla el ciclo de vida de GasReading. |
| Flecha punteada abierta     | Dependencia    | El puerto opera sobre la entidad indicada.          |
| Flecha con triangulo vacio  | Generalizacion | La subclase hereda de DGADomainError.               |

## Notas de diseno

- **GasReading** es un Value Object (frozen=True): inmutable, sin identidad,
  comparable por valor.
- **Transformer** y **Sample** son Entidades (frozen=False): mutables, con
  identidad (id) y validacion en `__post_init__`.
- Los puertos definen contratos CRUD puros. No contienen logica de negocio.
- Todas las excepciones heredan de **DGADomainError** para permitir captura
  centralizada en las capas superiores.
