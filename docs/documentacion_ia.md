# Documentación del Motor de Inteligencia Artificial

## Sistema Automatizado de Diagnóstico de Transformadores mediante AGD e IA

> Proyecto de Grado — ENDE Transmisión

---

## 1. Visión General

El motor de IA del sistema implementa un módulo de clasificación supervisada
de fallas en transformadores de potencia, basado en los 9 gases disueltos
obtenidos mediante cromatografía de gases (AGD/DGA).

El módulo entrena, evalúa y compara **4 algoritmos de Machine Learning**,
seleccionando automáticamente el de mejor desempeño para uso en producción.

### 1.1 Objetivo

Complementar los 6 métodos normativos tradicionales (IEEE C57.104, IEC 60599,
Rogers, Dornenburg, Triángulo de Duval, Pentágono de Duval) con un clasificador
inteligente que aprende patrones de los datos históricos y permite:

- Diagnóstico automático de nuevas lecturas de gases.
- Comparación objetiva entre el enfoque normativo y el enfoque de IA.
- Validación cruzada rigurosa para estimar el rendimiento real.

---

## 2. Arquitectura del Motor de IA

El motor sigue la **Arquitectura Hexagonal** del sistema, organizado en
4 componentes internos coordinados por un servicio fachada:

```
ai_service.py (Fachada / Orquestador)
├── data_preparation.py    ← Preparación de datos
├── model_trainer.py       ← Entrenamiento y comparación
├── model_evaluator.py     ← Evaluación con métricas detalladas
└── fault_classifier.py    ← Clasificación de nuevas lecturas
```

### 2.1 Flujo de Trabajo Completo

```
Muestras (Sample)
       │
       ▼
┌──────────────────────┐
│  data_preparation.py │  Extrae 9 features (gases) + genera etiquetas
│  - extract_features  │  por consenso normativo (voto mayoritario)
│  - auto_label        │
│  - prepare_dataset   │
└──────────┬───────────┘
           │ X (n×9), y (n,)
           ▼
┌──────────────────────┐
│  model_trainer.py    │  Entrena 4 modelos con validación cruzada
│  - _build_pipelines  │  estratificada (k-fold)
│  - train_all         │
│  - save_model        │  Persiste el mejor modelo con joblib
└──────────┬───────────┘
           │ TrainingResult
           ▼
┌──────────────────────┐
│  model_evaluator.py  │  Evalúa con cross_val_predict (out-of-fold)
│  - evaluate          │  Genera accuracy, precision, recall, F1,
│  - format_report     │  matriz de confusión por clase
└──────────┬───────────┘
           │ EvaluationResult
           ▼
┌──────────────────────┐
│  fault_classifier.py │  Clasifica nuevas lecturas de gases
│  - classify          │  Retorna FaultType del dominio
│  - classify_with_    │  Opcionalmente con probabilidades
│    probabilities     │
│  - classify_batch    │
└──────────────────────┘
```

---

## 3. Preparación de Datos (`data_preparation.py`)

### 3.1 Features (Variables de Entrada)

Se utilizan los **9 gases disueltos** medidos por cromatografía como features
de entrada, en orden canónico:

| # | Feature | Gas                     | Unidad | Rol diagnóstico             |
|---|---------|-------------------------|--------|-----------------------------|
| 1 | `h2`    | Hidrógeno               | ppm    | Indicador general de falla  |
| 2 | `ch4`   | Metano                  | ppm    | Fallas térmicas bajas       |
| 3 | `c2h6`  | Etano                   | ppm    | Fallas térmicas moderadas   |
| 4 | `c2h4`  | Etileno                 | ppm    | Fallas térmicas severas     |
| 5 | `c2h2`  | Acetileno               | ppm    | Descargas eléctricas        |
| 6 | `co`    | Monóxido de carbono     | ppm    | Degradación de celulosa     |
| 7 | `co2`   | Dióxido de carbono      | ppm    | Degradación de celulosa     |
| 8 | `o2`    | Oxígeno                 | ppm    | Gas atmosférico de control  |
| 9 | `n2`    | Nitrógeno               | ppm    | Gas atmosférico de control  |

### 3.2 Etiquetado Automático por Consenso Normativo

Dado que los datos históricos de ENDE Transmisión **no incluyen diagnósticos
manuales** confirmados por expertos, las etiquetas de entrenamiento se generan
automáticamente mediante **voto mayoritario** de los 6 métodos normativos:

1. Se ejecutan los 6 métodos normativos sobre cada lectura de gases.
2. Cada método produce un `FaultType` (N, PD, D1, D2, T1, T2, T3, DT, S).
3. Se cuenta la frecuencia de cada tipo de falla entre los 6 resultados.
4. El `FaultType` con más votos se asigna como **etiqueta de consenso**.
5. En caso de empate, se selecciona el tipo de falla de mayor severidad.

**Justificación:** El consenso de múltiples estándares internacionales proporciona
una etiqueta robusta, pues diferentes métodos cubren diferentes regiones del
espacio de fallas. Si 4 de 6 métodos coinciden en "D2 – Descargas de alta
energía", la etiqueta es confiable para entrenamiento.

### 3.3 Clases de Salida

El clasificador distingue **9 tipos de falla** definidos en `FaultType`:

| Código | Descripción                       | Estándar de referencia      |
|--------|-----------------------------------|-----------------------------|
| `N`    | Funcionamiento normal             | IEEE C57.104 / IEC 60599    |
| `PD`   | Descargas parciales               | IEC 60599 / Duval           |
| `D1`   | Descargas de baja energía         | IEC 60599 / Duval           |
| `D2`   | Descargas de alta energía (arco)  | IEC 60599 / Duval / Rogers  |
| `T1`   | Falla térmica < 300 °C            | IEC 60599 / Duval           |
| `T2`   | Falla térmica 300–700 °C          | IEC 60599 / Duval           |
| `T3`   | Falla térmica > 700 °C            | IEC 60599 / Duval           |
| `DT`   | Mezcla térmica y eléctrica        | Duval                       |
| `S`    | Sobrecalentamiento                | IEEE C57.104                |

---

## 4. Modelos de Machine Learning (`model_trainer.py`)

Se entrenan y comparan **4 algoritmos** de clasificación, cada uno encapsulado
en un `Pipeline` de scikit-learn que incluye preprocesamiento + clasificador.

### 4.1 Preprocesamiento Común

Todos los modelos utilizan **`StandardScaler`** como primer paso del pipeline:

$$
z_i = \frac{x_i - \mu_i}{\sigma_i}
$$

Donde $x_i$ es el valor original del gas $i$, $\mu_i$ es la media y $\sigma_i$
la desviación estándar calculadas sobre el conjunto de entrenamiento.

**Justificación:** Los 9 gases tienen escalas muy diferentes (H₂ puede ser
~100 ppm mientras que N₂ supera 50,000 ppm). La estandarización es esencial
para SVM y MLP, y no perjudica a RF ni KNN.

### 4.2 Random Forest (RF)

| Parámetro          | Valor   | Justificación                                    |
|--------------------|---------|--------------------------------------------------|
| `n_estimators`     | 200     | Suficientes árboles para estabilidad              |
| `max_depth`        | None    | Árboles crecen completos (datos no muy grandes)   |
| `min_samples_split`| 3       | Evita sobreajuste en hojas con pocas muestras     |
| `min_samples_leaf` | 1       | Permite capturar patrones minoritarios (PD, DT)   |
| `random_state`     | 42      | Reproducibilidad                                  |
| `n_jobs`           | -1      | Paralelismo completo                              |

**Principio de funcionamiento:** Ensemble de árboles de decisión entrenados
sobre subconjuntos aleatorios (bagging). La predicción final es el voto
mayoritario de los 200 árboles. Robusto ante ruido y no requiere ajuste fino.

### 4.3 Support Vector Machine (SVM)

| Parámetro     | Valor    | Justificación                                      |
|---------------|----------|----------------------------------------------------|
| `kernel`      | `rbf`    | Maneja fronteras no lineales entre tipos de falla   |
| `C`           | 10.0     | Penalización alta, fronteras más estrictas           |
| `gamma`       | `scale`  | $\gamma = \frac{1}{n_{features} \cdot \text{Var}(X)}$, adaptativo |
| `probability` | True     | Habilita `predict_proba` vía Platt scaling           |
| `random_state`| 42       | Reproducibilidad                                    |

**Principio de funcionamiento:** Busca el hiperplano (en espacio RBF de alta
dimensión) que maximiza el margen entre clases. La función kernel RBF mapea
los 9 gases a un espacio donde las fallas son linealmente separables.

### 4.4 K-Nearest Neighbors (KNN)

| Parámetro   | Valor        | Justificación                                      |
|-------------|--------------|-----------------------------------------------------|
| `n_neighbors`| 5           | Balance entre sesgo y varianza                       |
| `weights`   | `distance`   | Vecinos más cercanos tienen mayor influencia         |
| `metric`    | `euclidean`  | Distancia natural para datos estandarizados          |
| `n_jobs`    | -1           | Paralelismo completo                                 |

**Principio de funcionamiento:** Clasifica cada nueva lectura según el voto
ponderado por distancia de sus 5 vecinos más cercanos en el espacio de 9 gases.
No construye modelo explícito; es un método basado en instancias.

### 4.5 Multi-Layer Perceptron (MLP / Red Neuronal)

| Parámetro             | Valor       | Justificación                                 |
|-----------------------|-------------|-----------------------------------------------|
| `hidden_layer_sizes`  | (64, 32)    | 2 capas ocultas: 64→32 neuronas               |
| `activation`          | `relu`      | Activación estándar, evita vanishing gradient  |
| `solver`              | `adam`       | Optimizador adaptativo, convergencia rápida    |
| `max_iter`            | 500         | Iteraciones máximas de entrenamiento           |
| `early_stopping`      | True        | Detiene si la validación no mejora             |
| `validation_fraction` | 0.15        | 15% de datos para monitorear early stopping    |
| `random_state`        | 42          | Reproducibilidad                               |

**Arquitectura de la red:**

```
Entrada (9 neuronas) → Capa Oculta 1 (64 neuronas, ReLU)
                      → Capa Oculta 2 (32 neuronas, ReLU)
                      → Salida (9 neuronas, Softmax)
```

**Principio de funcionamiento:** Red neuronal feedforward que aprende
representaciones no lineales de los patrones de gases. La capa de salida
produce probabilidades para cada tipo de falla vía softmax. El early stopping
con 15% de validación previene sobreajuste.

---

## 5. Validación Cruzada Estratificada

### 5.1 Metodología

Se utiliza **Stratified K-Fold Cross-Validation** con $k = 5$ folds por defecto.

```
Dataset completo (n muestras)
├── Fold 1: Train (80%) │ Test (20%) → Score₁
├── Fold 2: Train (80%) │ Test (20%) → Score₂
├── Fold 3: Train (80%) │ Test (20%) → Score₃
├── Fold 4: Train (80%) │ Test (20%) → Score₄
└── Fold 5: Train (80%) │ Test (20%) → Score₅

Accuracy final = media(Score₁, ..., Score₅) ± std
```

**Estratificada** significa que cada fold mantiene la misma proporción de clases
que el dataset completo, crucial cuando hay clases minoritarias (ej. PD, DT).

### 5.2 Ajuste Automático de Folds

Si alguna clase tiene menos muestras que el número de folds, el sistema
reduce automáticamente $k$ al mínimo viable (≥ 2):

```python
effective_folds = min(n_folds, min_class_count)
if effective_folds < 2:
    effective_folds = 2
```

### 5.3 Doble Uso de Validación Cruzada

| Componente         | Función de sklearn      | Propósito                         |
|--------------------|------------------------|-----------------------------------|
| `model_trainer.py` | `cross_val_score`      | Comparar accuracy de los 4 modelos |
| `model_evaluator.py`| `cross_val_predict`   | Generar predicciones out-of-fold para métricas detalladas |

- **`cross_val_score`**: Retorna los scores de accuracy por fold. Se usa para
  seleccionar el mejor modelo.
- **`cross_val_predict`**: Retorna las predicciones de cada muestra cuando fue
  parte del conjunto de test. Permite calcular la matriz de confusión completa
  sin sesgo optimista.

---

## 6. Métricas de Evaluación (`model_evaluator.py`)

### 6.1 Métricas Globales

| Métrica              | Fórmula                                        | Interpretación                     |
|----------------------|------------------------------------------------|------------------------------------|
| **Accuracy**         | $\frac{TP + TN}{\text{Total}}$                | % de predicciones correctas         |
| **Macro Precision**  | $\frac{1}{C}\sum_{c=1}^{C} P_c$               | Promedio no ponderado de precisión   |
| **Macro Recall**     | $\frac{1}{C}\sum_{c=1}^{C} R_c$               | Promedio no ponderado de recall     |
| **Macro F1-Score**   | $\frac{1}{C}\sum_{c=1}^{C} F1_c$              | Promedio no ponderado de F1         |
| **Weighted F1**      | $\sum_{c=1}^{C} w_c \cdot F1_c$               | F1 ponderado por soporte de clase   |

Donde $C$ = número de clases y $w_c$ = proporción de muestras de la clase $c$.

### 6.2 Métricas por Clase

Para cada tipo de falla se calcula:

| Métrica      | Fórmula                     | Significado                                         |
|--------------|-----------------------------|----------------------------------------------------|
| **Precision**| $P = \frac{TP}{TP + FP}$   | De las predichas como X, ¿cuántas realmente son X? |
| **Recall**   | $R = \frac{TP}{TP + FN}$   | De las que realmente son X, ¿cuántas detectamos?    |
| **F1-Score** | $F1 = \frac{2PR}{P + R}$   | Media armónica de Precision y Recall                 |
| **Support**  | $n_c$                       | Cantidad de muestras reales de la clase             |

### 6.3 Matriz de Confusión

Matriz $C \times C$ donde la celda $(i, j)$ indica cuántas muestras de la
clase real $i$ fueron predichas como clase $j$. La diagonal principal
representa las predicciones correctas.

```
              Predicho
              N    PD   D1   D2   T1   T2   T3   DT    S
Real   N    [ 45    0    0    0    0    0    0    0    0 ]
       PD   [  0   12    0    0    1    0    0    0    0 ]
       D1   [  0    0   18    1    0    0    0    0    0 ]
       ...
```

---

## 7. Clasificación de Nuevas Lecturas (`fault_classifier.py`)

### 7.1 Flujo de Predicción

```
GasReading (9 gases en ppm)
       │
       ▼
  extract_features() → [h2, ch4, c2h6, c2h4, c2h2, co, co2, o2, n2]
       │
       ▼
  numpy array (1, 9)
       │
       ▼
  Pipeline.predict()
  ├── StandardScaler.transform() → normaliza
  └── Clasificador.predict()     → índice numérico
       │
       ▼
  INDEX_TO_FAULT[idx] → FaultType (ej. FaultType.D2)
```

### 7.2 Modos de Clasificación

| Método                        | Retorno                            | Uso                    |
|-------------------------------|------------------------------------|------------------------|
| `classify(reading)`           | `FaultType`                        | Diagnóstico simple      |
| `classify_with_probabilities` | `(FaultType, dict[FaultType, %])` | Diagnóstico con confianza|
| `classify_batch(readings)`    | `list[FaultType]`                  | Lote de lecturas        |

### 7.3 Probabilidades por Clase

Cuando se usa `classify_with_probabilities`, el clasificador retorna además
un diccionario con la probabilidad estimada para cada tipo de falla:

```
Predicción: D2 – Descargas de alta energía
Probabilidades:
    N  :  0.02   (2%)
    PD :  0.01   (1%)
    D1 :  0.08   (8%)
    D2 :  0.78  (78%)  ← mayor confianza
    T1 :  0.03   (3%)
    T2 :  0.05   (5%)
    T3 :  0.02   (2%)
    DT :  0.01   (1%)
    S  :  0.00   (0%)
```

Esto permite al ingeniero evaluar la **confianza** del diagnóstico de IA.

---

## 8. Persistencia de Modelos

### 8.1 Serialización con joblib

El mejor modelo (pipeline completo: `StandardScaler` + clasificador) se
serializa con `joblib` en formato `.joblib`:

```
models/
└── best_model.joblib    ← Pipeline serializado (~1-5 MB)
```

### 8.2 Ciclo de Vida del Modelo

```
1. Entrenamiento  → train()          → Guarda best_model.joblib
2. Carga          → load_model()     → Lee desde disco a memoria
3. Predicción     → classify()       → Usa modelo en memoria
4. Re-entrenamiento → train()        → Sobrescribe modelo anterior
```

El sistema intenta cargar el modelo automáticamente si no está en memoria
pero existe en disco, proporcionando una experiencia transparente.

---

## 9. Servicio Orquestador (`ai_service.py`)

### 9.1 API Principal

`AIService` es la **fachada única** que expone toda la funcionalidad de IA
a la capa de presentación (CLI):

| Método              | Descripción                                      |
|---------------------|--------------------------------------------------|
| `prepare_data()`    | Prepara dataset desde muestras del repositorio    |
| `train()`           | Entrena 4 modelos, guarda el mejor               |
| `evaluate_all()`    | Evalúa los 4 modelos con CV, retorna métricas    |
| `classify(reading)` | Clasifica una lectura con el modelo cargado       |
| `classify_with_proba()` | Clasifica con probabilidades               |
| `classify_batch()`  | Clasifica múltiples lecturas                      |
| `has_model()`       | Verifica si hay modelo disponible                 |
| `load_model()`      | Carga modelo desde disco                          |

### 9.2 Inyección de Dependencias

```python
ai_service = AIService(
    sample_repository=sample_repo,    # Acceso a datos
    normative_service=norm_svc,       # Para auto-etiquetado
    model_dir="models",               # Directorio de persistencia
    n_folds=5,                        # Folds de validación cruzada
)
```

---

## 10. Decisiones de Diseño y Justificaciones

### 10.1 ¿Por qué 4 modelos y no 1?

Se comparan 4 algoritmos con fundamentaciones teóricas diferentes para:

1. **Evaluar cuál se adapta mejor** al espacio de gases DGA.
2. **Transparencia académica**: la tesis debe demostrar que la selección
   del modelo se basa en evidencia empírica, no en suposición.
3. **Variedad de paradigmas**: basado en árboles (RF), basado en distancias
   (KNN, SVM) y basado en gradientes (MLP).

### 10.2 ¿Por qué auto-etiquetado por consenso?

Los datos históricos de ENDE no tienen diagnósticos confirmados por
laboratorio. El consenso de 6 métodos normativos internacionales es la
mejor aproximación disponible a la "verdad de terreno" (ground truth).

### 10.3 ¿Por qué StandardScaler y no MinMaxScaler?

- `StandardScaler` produce distribución ~N(0,1), ideal para SVM con kernel RBF
  y para MLP con activación ReLU.
- `MinMaxScaler` es sensible a outliers, frecuentes en datos DGA (picos de C₂H₂
  en descargas).

### 10.4 ¿Por qué joblib y no pickle?

`joblib` está optimizado para objetos numpy de gran tamaño (como los pesos de
modelos sklearn), con compresión eficiente y serialización más rápida.

### 10.5 ¿Por qué Pipeline y no pasos separados?

El `Pipeline` de sklearn garantiza que:
- El scaler se ajusta **solo** con datos de entrenamiento (previene data leakage).
- La transformación se aplica automáticamente en predicción.
- El modelo serializado incluye scaler + clasificador como unidad atómica.

---

## 11. Tecnologías Utilizadas

| Componente       | Tecnología          | Versión   |
|------------------|---------------------|-----------|
| ML Framework     | scikit-learn        | ≥ 1.3     |
| Serialización    | joblib              | ≥ 1.3     |
| Cálculo numérico | NumPy               | ≥ 1.24    |
| Lenguaje         | Python              | 3.13      |
| Testing          | pytest              | ≥ 7.0     |

---

## 12. Estructura de Archivos

```
src/dga/application/services/ai_engine/
├── __init__.py             Paquete del motor de IA
├── data_preparation.py     Extracción de features y auto-etiquetado
├── model_trainer.py        Entrenamiento y comparación de 4 modelos
├── model_evaluator.py      Evaluación detallada con métricas por clase
├── fault_classifier.py     Clasificador para nuevas lecturas
└── ai_service.py           Fachada/orquestador del módulo completo
```

---

*Documento generado como parte del Proyecto de Grado — Sistema AGD+IA para ENDE Transmisión.*
