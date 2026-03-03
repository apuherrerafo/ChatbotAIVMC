# Flujo VMC-Bot — Qué tenemos y qué falta

Referencia: regla bRAG-langchain + Roadmap + Strategic Brief.

---

## ✅ Qué tenemos

| Componente | Estado | Dónde |
|------------|--------|--------|
| **Centro de Ayuda crawleado** | Hecho | `data/raw/helpcenter_crawl.json`, `data/raw/text/*.md` |
| **FAQs oficiales** | Hecho | `data/raw/faqs_vmc.md`, `data/processed/faq_chunks.json` |
| **Chunking semántico por tema** | Hecho | `src/rag/chunks.py`, taxonomía en `src/ingest/taxonomy.py` |
| **Embeddings + Pinecone** | Hecho | `src/rag/embed.py`, `embed_faqs.py`, índice `vmc-bot-rag` |
| **Búsqueda simple (1 query)** | Hecho | `src/rag/query_rag.py` → `search()` |
| **Multi-Query + RRF** | Hecho | `src/rag/multi_query.py`, `rrf.py`, `search_multi_query_rrf()` en query_rag |
| **Respuesta con Claude Sonnet** | Hecho | `query_rag.py` → `answer_with_claude()` |
| **Fuente en tiempo real SubasPass** | Hecho | `src/rag/live_source.py`; inyectada en ask_rag cuando preguntan por SubasPass |
| **Router de intención (Haiku)** | Hecho | `src/rag/router.py` → faq \| stock_search \| soporte_humano \| fuera_dominio |
| **Integración router en API** | Hecho | `ask_with_router()` en query_rag; POST /api/ask usa router por defecto |
| **System prompt v1** | Hecho | `prompts/system_prompt_v1.md` (persona, glosario, guardrails) |
| **Web de prueba (sin WhatsApp)** | Hecho | `src/server/app.py`, `static/index.html`, GET / + POST /api/ask, badge intención |
| **Golden dataset (inicio)** | Parcial | `data/golden_dataset/faqs_golden.json` (14 entradas, meta 50) |

---

## ❌ Qué falta (según regla bRAG + roadmap)

### Contenido multimodal (Centro de Ayuda)

| Pieza | Descripción |
|-------|-------------|
| **Extracción de infografías/gráficos** | Leer imágenes del Centro de Ayuda con modelo multimodal (Claude/GPT-4V) o OCR; guardar texto por artículo; chunkear y embeber. Ver `EXTRACCION_CENTRO_AYUDA.md` y `RESUMEN_ESTADO_Y_SIGUIENTES_PASOS.md`. |
| **Extracción de videos** | Transcribir audio (Whisper) y opcionalmente resumir con Claude; chunkear y embeber para que el RAG use ese contenido. |

### Stock / inventario (Semana 3)

| Pieza | Descripción |
|-------|-------------|
| **Scraping de inventario** | Firecrawl (o similar) sobre vmcsubastas.com para listado de vehículos; guardar JSON con timestamp. |
| **Búsqueda en stock** | Dado intent `stock_search`, buscar en ese JSON (por texto o filtros) y responder con datos reales + disclaimer de fecha. |

### Canal y producción

| Pieza | Descripción |
|-------|-------------|
| **WhatsApp Business API** | Webhook (Meta Cloud API o Twilio), verificación, envío de respuestas. Hoy bloqueado (eSIM). |
| **Prompt caching** | Habilitar en llamadas a Claude (system prompt + contexto) para reducir costo y latencia. |
| **Logging / trazabilidad** | Logs estructurados (sin LangSmith); útil para depurar y medir latencia. |

---

## Orden sugerido para cerrar gaps

1. **Infografías y videos:** pipeline de extracción (multimodal/OCR para imágenes; Whisper + opcional Claude para videos); añadir al ingest y a Pinecone. Ver `RESUMEN_ESTADO_Y_SIGUIENTES_PASOS.md` §3.
2. **Scraping de inventario** + búsqueda en JSON cuando intent = stock.
3. **WhatsApp** cuando tengas número; luego prompt caching y logs.

La regla de Cursor **bRAG-langchain-referencia** está en `.cursor/rules/bRAG-langchain-referencia.mdc` para que al tocar RAG uses solo patrones (multi-query, RRF) con nuestro stack.
