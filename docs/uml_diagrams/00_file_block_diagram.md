# Diagrama de Bloques -- Archivos .py del proyecto

## Nivel 1 -- Vista general (solo 3 capas)

Pensalo como un edificio de 3 pisos. Cada piso solo puede llamar al piso de abajo.

```mermaid
graph TD
    A["main.py -- Arranca todo"] --> B["INFRASTRUCTURE -- Lo que el usuario ve y toca"]
    B --> C["APPLICATION -- La logica de cada operacion"]
    C --> D["DOMAIN -- Las reglas del negocio"]

    style A fill:#e8e8e8,stroke:#555,color:#000
    style B fill:#ffe8cc,stroke:#cc7700,color:#000
    style C fill:#b8e6b8,stroke:#337733,color:#000
    style D fill:#d0e0ff,stroke:#336699,color:#000
```

---

## Nivel 2 -- Cada archivo y a quien llama

```mermaid
graph TD
    main["main.py"]

    main --> main_menu["main_menu.py -- Menu principal"]
    main --> transformer_cli["transformer_cli.py -- Menu transformadores"]
    main --> sample_cli["sample_cli.py -- Menu muestras"]

    transformer_cli --> trafo_svc["transformer_service.py"]
    sample_cli --> sample_svc["sample_service.py"]
    sample_cli --> trafo_svc

    trafo_svc --> trafo_port["transformer_repository.py -- interfaz"]
    sample_svc --> sample_port["sample_repository.py -- interfaz"]
    sample_svc --> trafo_port

    trafo_port -.->|"implementado por"| sqlite_trafo["sqlite_transformer_repository.py"]
    sample_port -.->|"implementado por"| sqlite_sample["sqlite_sample_repository.py"]

    sqlite_trafo --> transformer["transformer.py"]
    sqlite_sample --> sample["sample.py"]
    sample --> gas_reading["gas_reading.py"]

    style main fill:#e8e8e8,stroke:#555,color:#000
    style main_menu fill:#ffe8cc,stroke:#cc7700,color:#000
    style transformer_cli fill:#ffe8cc,stroke:#cc7700,color:#000
    style sample_cli fill:#ffe8cc,stroke:#cc7700,color:#000
    style trafo_svc fill:#b8e6b8,stroke:#337733,color:#000
    style sample_svc fill:#b8e6b8,stroke:#337733,color:#000
    style trafo_port fill:#aac8ee,stroke:#336699,color:#000
    style sample_port fill:#aac8ee,stroke:#336699,color:#000
    style sqlite_trafo fill:#ffe0b0,stroke:#cc7700,color:#000
    style sqlite_sample fill:#ffe0b0,stroke:#cc7700,color:#000
    style transformer fill:#d0e0ff,stroke:#336699,color:#000
    style sample fill:#d0e0ff,stroke:#336699,color:#000
    style gas_reading fill:#d0e0ff,stroke:#336699,color:#000
```

---

## Como leerlo (paso a paso)

1. **main.py** abre los 3 menus (naranja).
2. Cada menu llama a su **servicio** (verde).
3. Cada servicio habla con una **interfaz** (azul con borde).
4. Esa interfaz la **implementa** un repositorio SQLite (naranja claro, flecha punteada).
5. Los repositorios crean los **modelos** (azul): transformer, sample, gas_reading.

---

## Ejemplo real: el usuario registra una muestra

```
El usuario escribe los datos de gases
         |
    sample_cli.py        (recibe lo que escribio)
         |
    sample_service.py    (valida y coordina)
         |
    sqlite_sample_repository.py   (guarda en la base de datos)
         |
    sample.py + gas_reading.py    (la estructura de los datos guardados)
```
