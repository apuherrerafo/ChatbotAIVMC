## Evaluación del golden dataset (RAG VMC-Bot)

Este documento explica **cómo evaluar el bot** usando el golden dataset y el script de evaluación.

---

### 1. Golden dataset

- **Archivo**: `data/golden_dataset/faqs_golden.json`
- **Contenido**:
  - `description`, `source`
  - `entries`: array de objetos con:
    - `id` (ej. `g1`)
    - `topic` (ej. `Comisión`, `SubasCoins y billetera`)
    - `pregunta`
    - `respuesta_esperada` (texto de referencia, NO prompt)
- Incluye:
  - FAQs textuales originales.
  - Preguntas que dependen de contenido de **infografías** (comisión, Pacífico, ganador habilitado, sanciones, devoluciones, etc.).

---

### 2. Script de evaluación

- **Archivo**: `scripts/eval_golden.py`
- **Qué hace**:
  - Carga el golden dataset.
  - Para cada entrada llama a:
    - `ask_with_router(pregunta)` (router + RAG) o
    - `ask_rag(pregunta)` si se usa `--skip-router`.
  - Mide:
    - `intent` clasificado.
    - `latency_ms`.
    - `chunks_count` (cuántos fragmentos se usaron).
    - `answer_len` y `has_answer`.
  - Escribe una línea JSON por entrada en:
    - `data/golden_dataset/eval_results.jsonl`
  - Imprime un resumen en consola.

---

### 3. Cómo ejecutar la evaluación

Desde la raíz del proyecto `vmc-bot`:

```bash
# Evaluar las 50 preguntas
python scripts/eval_golden.py

# Solo las primeras N (pruebas rápidas)
python scripts/eval_golden.py --limit 10

# Ir directo a RAG (sin router)
python scripts/eval_golden.py --skip-router
```

Requisitos:
- `.env` con `ANTHROPIC_API_KEY` y `PINECONE_API_KEY` configurados.
- Pinecone con el índice `vmc-bot-rag` y los embeddings ya cargados (incluyendo infografías).

---

### 4. Cómo leer los resultados

- **Archivo de resultados**: `data/golden_dataset/eval_results.jsonl`
  - Cada línea es un JSON con campos como:
    - `id`, `topic`, `pregunta` (truncada)
    - `intent`
    - `latency_ms`
    - `chunks_count`
    - `answer_len`
    - `has_answer`
    - `error` (si hubo excepción)

- **Resumen en consola** (al final de la ejecución):
  - `Total evaluadas`
  - `Con respuesta` (% de preguntas donde el bot devolvió algo no vacío)
  - `Errores`
  - `Latencia promedio`
  - Conteo por `intent`

---

### 5. Uso recomendado

- **Antes de cambios grandes** (ej. retraining de embeddings, cambios de prompt, cambios en chunking):
  - Corre `python scripts/eval_golden.py` y guarda el `eval_results.jsonl` (snapshot).
- **Después de cambios**:
  - Vuelve a correr el script.
  - Compara:
    - % de preguntas con respuesta.
    - Latencia promedio.
    - Cambios en `intent` para ciertas preguntas.
    - Para preguntas críticas, compara manualmente `respuesta_esperada` con lo que responde el bot.

Esto permite ver **si mejoró o empeoró** la calidad después de tocar RAG, prompt, infografías, etc., sin depender solo de pruebas manuales sueltas.

