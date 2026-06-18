# Estudio técnico de Agent Essentials

*Análisis crítico, pruebas adversariales y mejoras — desde la lógica de cómo fallan realmente los sistemas de IA.*

Autor: revisión asistida por IA · Versión del toolkit: 0.1.0 · Fecha: 2026-06-18

---

## 1. Resumen ejecutivo

Sometí los cinco módulos del MVP a pruebas adversariales diseñadas no para confirmar que funcionan, sino para **romperlos** usando los modos de fallo típicos de los LLM: respuestas fluidas que invierten el sentido de su fuente, contradicciones parafraseadas, variantes morfológicas y texto no inglés.

El núcleo es sólido y honesto (heurísticas deterministas, sin dependencias), pero encontré **tres fallos reales**, uno de ellos crítico para seguridad. Los corregí, los cubrí con tests de regresión y verifiqué que no hay regresiones.

| # | Hallazgo | Severidad | Estado |
|---|----------|-----------|--------|
| 1 | El detector de alucinaciones daba `riesgo=0.0` a respuestas que **dicen lo contrario** de su fuente | **Crítica** | Corregido |
| 2 | La recuperación de memoria no relacionaba variantes morfológicas (`running`/`runner`) | Media | Corregido |
| 3 | El conteo de tokens subestimaba ~10x el texto CJK (chino/japonés/coreano) | Media | Corregido |

Resultado tras las mejoras: **78 tests** en verde, **cobertura 91.3%**, `ruff` + `ruff format` + `mypy --strict` sin errores.

---

## 2. Metodología

La pregunta que guió el análisis no fue *"¿el código corre?"* sino *"¿en qué se equivocaría un ingeniero que confíe en esto en producción?"*. Por eso las sondas imitan cómo fallan los modelos de verdad:

- **Las alucinaciones son fluidas y plausibles.** Rara vez son texto aleatorio; suelen reutilizar el vocabulario correcto y afirmar algo falso. El caso más peligroso es la **inversión de polaridad**: la fuente dice "no es seguro" y la respuesta dice "es completamente seguro".
- **El lenguaje no es ASCII.** Producción es multilingüe; una heurística sesgada al inglés engaña los presupuestos de coste.
- **La morfología importa.** "runner", "running" y "run" son la misma idea para un usuario que busca en su memoria.

Cada sonda es **determinista y reproducible** (sin red, sin claves), igual que el propio toolkit. Capturé el estado *antes*, apliqué la mejora y volví a medir el estado *después* con el mismo caso, añadiendo además **casos de control** para no introducir falsos positivos.

---

## 3. Hallazgos por módulo

### 3.1 Architecture Generator — sólido

Las reglas (umbrales de RAG, niveles de vector store, caché, colas, regiones) son razonables y, sobre todo, **explicables**: cada decisión llega con su justificación. Es coherente con el coste estimado (ruta económica vs. balanceada).

Observación menor (no corregida, documentada): la estimación de coste asume `requests/día = usuarios × 10` y un tamaño fijo de prompt/respuesta. Es un supuesto de planificación honesto y está etiquetado como aproximado, pero conviene exponerlo como parámetro en una versión futura. No es un fallo, es una simplificación declarada.

### 3.2 Memory Engine — un punto ciego morfológico (corregido)

El `HashingEmbedder` por defecto era *bag-of-words* con feature hashing: determinista y sin dependencias, pero puramente léxico a nivel de palabra completa. Eso significa que **`running` y `runner` tenían similitud 0.0**, y una búsqueda de "running training" no recuperaba una memoria sobre un "runner".

Punto importante de honestidad: incluso mejorado, **sigue siendo un embedder léxico, no semántico**. No relacionará sinónimos sin raíz común (`car`/`automobile`). Para semántica real hay que enchufar un modelo de embeddings por la interfaz `Embedder` (extra `llm`). El valor del default es ser reproducible y testeable offline; la mejora amplía su alcance a la morfología, no a la semántica.

### 3.3 Task Planner — sólido para su alcance

La descomposición por plantillas + features detectadas es determinista, el orden topológico es correcto y los grupos paralelos son útiles. Las dependencias son "por fase" (gruesas); proyectos reales tienen dependencias cruzadas más finas. Es una limitación aceptable y esperable en un planificador heurístico; no la considero un fallo.

### 3.4 Hallucination Detector — el fallo crítico (corregido)

Este módulo es el más interesante desde la lógica de una IA, porque conozco de primera mano cómo se manifiestan las alucinaciones. El *grounding* original medía **cobertura de vocabulario**: qué fracción de las palabras del claim aparecen en la fuente. Esa métrica tiene un agujero grave:

> Una respuesta puede reutilizar casi todas las palabras de la fuente y aun así afirmar **exactamente lo contrario**, porque la cobertura de tokens **ignora la negación**.

Evidencia (sonda real):

```text
claim : "The medication is completely safe for children."
fuente: "The medication is not safe for children."
ANTES  -> risk_score = 0.0   nivel = low    warnings = []      ❌ falso negativo peligroso
```

Un sistema médico, legal o financiero que confiara en esto habría aprobado una afirmación que invierte la evidencia. Para un detector de alucinaciones, este es el peor error posible.

### 3.5 Token Counter — sesgo al inglés (corregido)

La heurística sin `tiktoken` mezclaba `chars/4` y `palabras×1.33`, válida para inglés. Pero el regex de palabras es `[A-Za-z0-9']+`, así que el texto CJK aporta **cero palabras** y `chars/4` lo subestima por un orden de magnitud:

```text
"人工智能正在改变软件行业的运作方式"  ANTES -> 2 tokens   (real ~20-26)  ❌
```

Un presupuesto de coste para una app en chino habría sido ~10x demasiado optimista.

---

## 4. Mejoras implementadas (evidencia antes/después)

### 4.1 Grounding sensible a negación/polaridad (crítico)

Reescribí el *grounding* para que sea **a nivel de oración** y **consciente del alcance de la negación**:

1. Para cada claim, encuentro la oración-fuente con mayor cobertura de vocabulario.
2. Si la cobertura es alta pero **exactamente un lado niega**, es candidato a contradicción.
3. **Filtro anti-falsos-positivos:** solo se marca si la negación recae sobre una palabra *compartida* con la fuente (aproximación del alcance de la negación mirando los tokens de contenido que siguen al "not/never/...").

Así distingo *"X es seguro"* vs *"X no es seguro"* (contradicción) de *"X es rápido y no se cae"* vs *"X es rápido"* (información añadida, no contradicción).

| Caso | Antes | Después |
|------|-------|---------|
| "completely safe" vs fuente "not safe" | `0.0` / low | **`0.5` / high** + `contradicts_source` |
| "compliant with GDPR" vs "not compliant" | `0.0` / low | **`0.5` / high** + `contradicts_source` |
| "not deprecated" vs "deprecated" | `0.0` / low | **`0.5` / high** + `contradicts_source` |
| (control) "fast and does not crash" vs "fast" | low | **low** (no se marca ✓) |
| (control) afirmación positiva correcta | low | **low** ✓ |

### 4.2 Embedder con subword n-grams

`HashingEmbedder` ahora añade features de n-gramas de caracteres (subword, estilo fastText), con marcadores de frontera `<token>`, manteniéndose determinista (BLAKE2b) y sin dependencias.

| Métrica | Antes | Después |
|---------|-------|---------|
| `cosine('running','runner')` | `0.0000` | **`0.3508`** |
| recuperar "running training" → memoria del "runner" | score `0.0` | **score `0.134`** (recuperada) |

Configurable con `subword_ngrams` (def. 3) y `subword_weight` (def. 0.5); `subword_ngrams=0` restaura el comportamiento puramente léxico.

### 4.3 Conteo de tokens CJK-aware

| Texto | Antes | Después | Real aprox. |
|-------|-------|---------|-------------|
| Chino (16 car.) | 2 | **26** | ~20-26 |
| Español | 15 | 12-15 | ~15 |
| Inglés | sin cambio | sin cambio | — |

---

## 5. Limitaciones honestas que permanecen

Un análisis serio dice también lo que el toolkit **no** puede hacer:

- **El grounding sigue siendo léxico/heurístico, no NLI.** Detecto inversión de polaridad, pero no errores relacionales sutiles ("A causa B" cuando la fuente dice "B causa A") ni implicaciones que requieren razonamiento. La solución correcta es un verificador por entailment (NLI) o un juez LLM — encaja como plugin del extra `llm` y queda en el roadmap.
- **Las contradicciones parafraseadas con poco solape léxico se escapan.** Bajar el umbral de solape generaría falsos positivos; preferí no degradar la precisión. Es una limitación inherente a los métodos léxicos.
- **El embedder por defecto no capta sinónimos.** Es léxico + subword, no semántico. Para semántica real, enchufar embeddings vía la interfaz `Embedder`.
- **El conteo sin `tiktoken` es estimación.** Mejoró para CJK, pero para exactitud por modelo hay que instalar el extra `tokenizers`.

Estas no son excusas: son la frontera correcta entre un núcleo determinista y barato (lo que el toolkit promete) y la inteligencia opcional vía plugins (lo que el toolkit habilita).

---

## 6. Recomendaciones

1. **v0.2 — Validación con NLI opcional.** Un `EntailmentValidator` (plugin `llm`) que confirme/cuantifique las contradicciones que el heurístico señala. El heurístico actúa de pre-filtro barato; el LLM solo se invoca en los casos dudosos (control de coste).
2. **Embeddings semánticos enchufables** documentados con un ejemplo (sentence-transformers) detrás del extra `llm`.
3. **Exponer los supuestos de coste** del Architecture Generator como campos de `ProjectSpec` (tokens/petición, picos).
4. **Conteo exacto multilingüe** recomendando `tiktoken` en la doc de coste cuando el texto no es inglés.
5. **Telemetría de riesgo** en producción: registrar `risk_score` por respuesta para detectar regresiones del modelo con el tiempo.

---

## 7. Reproducibilidad

Todo lo anterior se verifica de forma determinista:

```bash
pip install -e ".[dev]"
pytest --cov=agent_essentials --cov-report=term-missing   # 78 tests, ~91% cobertura
ruff check . && ruff format --check .                      # estilo
mypy                                                       # tipos estrictos
```

Los casos adversariales de §3-§4 son reproducibles con el detector y el embedder directamente; las regresiones quedaron fijadas en `tests/unit/test_validation.py`, `test_memory.py` y `test_utilities.py`.

---

## 8. Conclusión

El toolkit cumple su promesa: decisiones explicables, deterministas y sin dependencias. El análisis desde la lógica de cómo fallan los LLM reveló un agujero de seguridad real (aprobar respuestas que invierten su fuente) que ahora está cerrado, más dos mejoras de robustez (morfología y multilingüe). Igual de importante: documenté con franqueza dónde un heurístico no alcanza y por qué la respuesta correcta a eso es el sistema de plugins, no forzar la heurística hasta romper su precisión.


---

## Anexo — Ronda 2: ataque exhaustivo a los cinco módulos

Tras la primera ronda (validación, memoria, tokens), ataqué los **cinco** módulos de forma sistemática, con foco en los dos que no había estresado: Architecture y Planner. Cinco hallazgos nuevos, todos corregidos y cubiertos con tests.

| # | Módulo | Hallazgo | Severidad | Estado |
|---|--------|----------|-----------|--------|
| 4 | Architecture | El coste mensual era **idéntico** para `economy`/`balanced`/`premium` (ignoraba el tier recomendado) | **Alta** (coherencia) | Corregido |
| 5 | Planner | Sesgo monolingüe: una meta en español detectaba 1 de 4 features | Media | Corregido |
| 6 | Memory | `alpha` fuera de `[0,1]` se aceptaba sin validar | Robustez | Corregido |
| 7 | Memory | Un recuerdo más grande que el presupuesto dejaba el contexto **vacío** | Media | Corregido |
| 8 | Validation | No detectaba cifras **mal atribuidas** cuando el número erróneo aparece en otra parte de la fuente | Media | Corregido |
| 9 | Optimization | `compare()` aceptaba tokens negativos | Robustez | Corregido |

### A.1 Coherencia de coste (Architecture) — el hallazgo clave de esta ronda

El coste se calculaba con tarifas fijas (Haiku/Sonnet) sin mirar el `budget`. Prueba:

```text
ANTES  economy   low/high = 12155 / 36155
       balanced  low/high = 12155 / 36155   ❌ idénticos
       premium   low/high = 12155 / 36155
```

Ahora las bandas se derivan del **catálogo de precios real** (`optimization.pricing`) según los tiers de routing recomendados (`default` → banda baja, `escalation` → banda alta):

```text
DESPUÉS economy   tiers=economy/balanced   low/high =  7255 / 26030
        balanced  tiers=economy/frontier   low/high =  7255 / 33905
        premium   tiers=balanced/frontier  low/high = 26030 / 33905
```

Además de corregir la incoherencia, esto **conecta dos módulos** (Architecture consume el pricing de Optimization), que es justo la promesa del toolkit: decisiones de diseño ancladas en costes reales.

### A.2 Planner bilingüe

```text
meta ES: "plataforma SaaS de ligas deportivas con pagos y usuarios"
ANTES   features = ['multitenant']
DESPUÉS features = ['auth', 'multitenant', 'payments', 'scheduling']   (= que el inglés)
```

Detección ahora EN+ES e **insensible a acentos** (`análisis` → `analisis`).

### A.3 Memory: robustez

- `retrieve_memory(alpha=5.0)` → ahora `ValidationError`.
- `optimize_context` con un recuerdo más grande que el presupuesto: antes devolvía `incluidos=0, contexto=""`; ahora incluye un **fragmento truncado** del más relevante (marcado `truncated=True`), respetando el presupuesto.

### A.4 Validación: discrepancia numérica

```text
claim : "The tower opened in 1925."
fuente: "The tower opened in 1889. A nearby museum opened in 1925."
ANTES  -> sin señal (1925 existe en la fuente, aunque para otra cosa)
DESPUÉS-> numeric_mismatch=1, warning, riesgo a 'moderate'
```

Complementa a `fabricated_specifics` (que solo mira si el número existe en *alguna* parte). **Limitación honesta:** depende del desempate de la "mejor oración" (orden de las fuentes); es un pre-filtro barato, no un verificador relacional. La solución robusta sigue siendo NLI/juez LLM como plugin.

### A.5 Estado final tras Ronda 2

`78 tests` en verde · cobertura `91.3%` · `ruff` + `ruff format` + `mypy --strict` sin errores · 6 ejemplos corriendo · CLI operando también en español. Cero regresiones respecto a la Ronda 1.


---

## Anexo — Ronda 3: hiperescala y validación por entailment

Tercera ronda, atacando lo que quedaba: el comportamiento de Architecture a escalas extremas y el límite de fondo de la validación heurística.

### B.1 Architecture a hiperescala (cap de réplicas)

El cálculo de réplicas e infraestructura era **lineal y sin tope**, produciendo cifras sin sentido a gran escala y sin avisar de que ahí ya no sirve una sola flota:

```text
ANTES   users=500,000,000 -> replicas=57,871   infra=$2,893,605/mes   (sin aviso)
DESPUÉS users=500,000,000 -> replicas=500 (cap) infra=$25,055/mes     hyperscale=True
        + finding 'hyperscale' (severidad alta)
        + recomendación 'Design a cell-based, multi-region architecture'
        + patrones 'Cell-based architecture', 'Multi-region active-active'
```

La lógica nueva: por encima de `MAX_REPLICAS` (500) o `HYPERSCALE_USER_FLOOR` (10M usuarios), una sola flota deja de escalar linealmente, así que en vez de extrapolar un número absurdo el toolkit **marca el régimen** y recomienda partir en celdas y regiones. La cifra de infra pasa a ser un piso explícito, no una falsa precisión.

### B.2 Validación por entailment (NLI) — el límite de fondo, ahora con salida

En las rondas 1-2 documenté que el detector heurístico no hace NLI: no razona implicación, solo solapamiento + polaridad + números. La Ronda 3 cierra eso con un **módulo nuevo** (`EntailmentValidator`, plugin `entailment`) que clasifica **cada claim** contra su mejor oración-fuente:

```text
output : "The medication is safe. Revenue was 999."
fuentes: ["The medication is not safe.", "Revenue was 12."]
-> contradiction  <- "The medication is safe."   (polaridad)
-> contradiction  <- "Revenue was 999."           (número)
-> risk=0.7 (high), contradicted=2
```

La clave de diseño es el **scorer inyectable**: el `Scorer` por defecto es determinista y offline (reutiliza los checks de validación), así que corre en CI sin claves; pero se puede inyectar un scorer respaldado por LLM o por un modelo NLI de `transformers` (extra `llm`) **sin tocar el módulo**:

```python
EntailmentValidator(scorer=mi_scorer_llm).validate(output, sources=[...])
```

Esto materializa el principio del toolkit —*núcleo determinista, inteligencia opcional vía plugin*— y es la respuesta correcta a las limitaciones de validación que documenté con franqueza, en vez de forzar la heurística.

### B.3 Estado final tras Ronda 3

`86 tests` en verde (8 nuevos) · cobertura `91.7%` · `ruff` + `ruff format` + `mypy --strict` (40 archivos) sin errores · 8 ejemplos corriendo · **6 módulos** registrados (`architecture`, `memory`, `planning`, `validation`, `entailment`, `optimization`). Tres rondas de ataque adversarial, **9 fallos** encontrados y corregidos, cero regresiones.
