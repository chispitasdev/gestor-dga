# Diagrama de Paquetes -- Arquitectura Hexagonal

Diagrama UML de paquetes del sistema DGA (Dissolved Gas Analysis).
Muestra la organizacion en capas y la direccion de las dependencias
siguiendo la arquitectura hexagonal (Ports & Adapters).

Las dependencias fluyen siempre de afuera hacia adentro:
infrastructure -> application -> domain.

```mermaid
graph TD
    %% ================================================================
    %% COMPOSITION ROOT
    %% ================================================================
    main["main.py\nComposition Root"]

    %% ================================================================
    %% CAPA INFRASTRUCTURE -- Adaptadores externos
    %% ================================================================
    subgraph INFRA["infrastructure"]
        direction LR
        subgraph CLI["cli"]
            cli_1["MainMenu"]
            cli_2["TransformerCLI"]
            cli_3["SampleCLI"]
        end
        subgraph PERSISTENCE["persistence"]
            per_1["sqlite_connection"]
            per_2["SQLiteTransformerRepository"]
            per_3["SQLiteSampleRepository"]
        end
    end

    %% ================================================================
    %% CAPA APPLICATION -- Casos de uso
    %% ================================================================
    subgraph APP["application"]
        direction LR
        subgraph SERVICES["services"]
            svc_1["TransformerService"]
            svc_2["SampleService"]
        end
        subgraph DTO["dto"]
            dto_1["CreateTransformerDTO"]
            dto_2["UpdateTransformerDTO"]
            dto_3["CreateSampleDTO"]
            dto_4["UpdateSampleDTO"]
        end
    end

    %% ================================================================
    %% CAPA DOMAIN -- Nucleo de negocio
    %% ================================================================
    subgraph DOMAIN["domain"]
        direction LR
        subgraph MODELS["models"]
            mod_1["Transformer"]
            mod_2["Sample"]
            mod_3["GasReading"]
        end
        subgraph PORTS["ports"]
            port_1["TransformerRepository\n<<interface>>"]
            port_2["SampleRepository\n<<interface>>"]
        end
        subgraph EXCEPTIONS["exceptions"]
            exc_1["DGADomainError"]
        end
    end

    %% ================================================================
    %% DEPENDENCIAS ENTRE CAPAS
    %% ================================================================

    %% Composition Root inyecta en todas las capas
    main -.->|"inyecta"| INFRA
    main -.->|"inyecta"| APP
    main -.->|"inyecta"| DOMAIN

    %% CLI usa servicios de aplicacion
    CLI -.->|"<<use>>"| SERVICES

    %% Persistencia implementa puertos del dominio
    PERSISTENCE -.->|"<<realize>>"| PORTS

    %% Persistencia usa modelos del dominio
    PERSISTENCE -.->|"<<use>>"| MODELS

    %% Servicios dependen de puertos abstractos
    SERVICES -.->|"<<use>>"| PORTS

    %% Servicios usan modelos y excepciones del dominio
    SERVICES -.->|"<<use>>"| MODELS
    SERVICES -.->|"<<use>>"| EXCEPTIONS

    %% Servicios usan DTOs
    SERVICES -.->|"<<use>>"| DTO

    %% ================================================================
    %% ESTILOS
    %% ================================================================
    classDef domainNode fill:#d0e0ff,stroke:#336699,color:#000
    classDef appNode fill:#d5f0d5,stroke:#337733,color:#000
    classDef infraNode fill:#ffe8cc,stroke:#cc7700,color:#000
    classDef rootNode fill:#e8e8e8,stroke:#555555,color:#000

    class mod_1,mod_2,mod_3,port_1,port_2,exc_1 domainNode
    class svc_1,svc_2,dto_1,dto_2,dto_3,dto_4 appNode
    class cli_1,cli_2,cli_3,per_1,per_2,per_3 infraNode
    class main rootNode

    style DOMAIN fill:#f0f5ff,stroke:#336699,stroke-width:2px
    style MODELS fill:#e8eeff,stroke:#336699,stroke-width:1px
    style PORTS fill:#e8eeff,stroke:#336699,stroke-width:1px
    style EXCEPTIONS fill:#e8eeff,stroke:#336699,stroke-width:1px

    style APP fill:#f0fff0,stroke:#337733,stroke-width:2px
    style SERVICES fill:#e8ffe8,stroke:#337733,stroke-width:1px
    style DTO fill:#e8ffe8,stroke:#337733,stroke-width:1px

    style INFRA fill:#fff8f0,stroke:#cc7700,stroke-width:2px
    style CLI fill:#fff0e0,stroke:#cc7700,stroke-width:1px
    style PERSISTENCE fill:#fff0e0,stroke:#cc7700,stroke-width:1px
```

## Leyenda

| Color    | Capa            | Descripcion                                             |
|----------|-----------------|---------------------------------------------------------|
| Azul     | domain          | Nucleo de negocio. No depende de nada externo.          |
| Verde    | application     | Casos de uso. Depende solo de domain.                   |
| Naranja  | infrastructure  | Adaptadores concretos. Depende de application y domain. |
| Gris     | main.py         | Composition Root. Conecta todas las capas.              |

## Estereotipos UML utilizados

| Estereotipo    | Significado                                                  |
|----------------|--------------------------------------------------------------|
| <<interface>>  | Contrato abstracto (ABC) sin implementacion.                 |
| <<use>>        | El paquete origen importa y utiliza elementos del destino.   |
| <<realize>>    | El paquete origen implementa las interfaces del destino.     |

## Regla de dependencia

Las flechas punteadas representan dependencias en codigo (sentencias
import). Todas fluyen de la capa exterior hacia la interior. Ninguna
capa interna conoce a las externas.
