# Semana 1 — To‑Do: Hecho vs Falta

Solo lo que corresponde a **Semana 1** (Discovery + Vector Store). Formato: bullet, claro.

---

## ✅ Hecho / Ya integrado

### Día 1 — Setup + Crawl
- [x] Firecrawl configurado (API key en `.env`, MCP opcional)
- [x] Pinecone configurado (índice `vmc-bot-rag`, multilingual-e5-large)
- [x] Crawl del Centro de Ayuda (ayuda.vmcsubastas.com) → `data/raw/helpcenter_crawl.json`
- [x] Export de markdown por URL → `data/raw/text/*.md` (páginas con texto)

### Día 2 — Extracción
- [x] Páginas con texto extraídas con Firecrawl y guardadas en `data/raw/text/`
- [x] Taxonomía de temas definida → `src/ingest/taxonomy.py`
- [ ] **Páginas con imágenes/infografías:** extracción con Claude (vision) o OCR — **falta**
- [ ] T&C / documentos legales en `data/raw/legal/` — **falta** (o no aplica si no se priorizó)
- [ ] Exploración fuentes alternativas en `data/raw/fuentes_alternativas.md` — **falta** (opcional)

### Día 3 — Limpieza + Chunking
- [x] Chunking semántico (por tema/pregunta, no por tamaño fijo) → `src/rag/chunks.py`
- [x] Chunks con metadata (tema, fuente, `has_numeric_data`) → `data/processed/chunks.json`
- [x] FAQs oficiales chunkeadas → `data/processed/faq_chunks.json`
- [ ] Revisión manual de chunks con números (comisiones, precios, plazos) — **recomendado**

### Día 4 — Embeddings + System Prompt
- [x] Embeddings con Pinecone Inference (multilingual-e5-large)
- [x] Upsert a Pinecone (Centro de Ayuda + FAQs) → `src/rag/embed.py`, `embed_faqs.py`
- [x] System prompt v1 → `prompts/system_prompt_v1.md` (persona, glosario, guardrails, tono)

### Día 5 — Golden + Test RAG
- [x] Golden dataset iniciado → `data/golden_dataset/faqs_golden.json` (14 entradas)
- [x] Test RAG end-to-end: pregunta → Pinecone (multi-query + RRF) → Claude → respuesta
- [x] Web de prueba (GET /, POST /api/ask) para probar sin WhatsApp
- [ ] Golden dataset ampliado a **50 preguntas** — **falta**
- [ ] Ejecutar test con 10+ preguntas del golden y documentar resultados — **falta**

### Extra ya integrado (fuera del plan original S1)
- [x] Multi-query + RRF en el RAG
- [x] Router de intención (Haiku): faq | stock_search | soporte_humano | fuera_dominio
- [x] Fuente en tiempo real SubasPass (scrape de la página al preguntar por SubasPass)

---

## ❌ Falta (solo Semana 1)

- **Infografías/imágenes del Centro de Ayuda:** descargar imágenes de páginas clave, extraer texto con Claude (vision) o OCR, guardar en `data/raw/images_extracted/` y sumar al pipeline de chunks/embed.
- **Videos del Centro de Ayuda:** transcribir (ej. Whisper), opcional resumen, chunkear y embeber (igual que texto).
- **Golden dataset a 50:** llegar a 50 preguntas con respuesta esperada y usarlas para evaluar el RAG.
- **Revisión manual** de chunks que tengan precios/comisiones/plazos para no inventar números.
- **Opcional:** T&C/legal en `data/raw/legal/` y fuentes alternativas en `data/raw/fuentes_alternativas.md`.

---

## Resumen en una línea

**Hecho:** crawl, texto extraído, taxonomía, chunking, embeddings en Pinecone, system prompt, RAG con multi-query+RRF, router, SubasPass en vivo, web de prueba, golden 14.  
**Falta (S1):** infografías + videos extraídos e integrados al RAG, golden 50, revisión manual de chunks numéricos.
