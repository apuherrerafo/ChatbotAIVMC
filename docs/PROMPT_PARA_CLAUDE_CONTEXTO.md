# Prompt de contexto para Claude — VMC-Bot

**Objetivo:** Pegar este texto (o el bloque "Para copiar") en una conversación con Claude para que esté al tanto de la situación del proyecto, lo ya hecho, las conexiones y pueda sugerir en qué seguir.

---

## Para copiar (bloque único)

```
Estamos desarrollando el chatbot de IA para VMC Subastas (subastas de vehículos en Perú). El canal objetivo es WhatsApp Business API; por ahora no está conectado (pendiente número/eSIM). El desarrollo es 100% AI-driven con Cursor y MCPs; no hay equipo de programadores, solo un Lead AI Engineer.

**Stack actual:**
- Backend: Python, FastAPI (puerto 8000), Uvicorn.
- LLM: Anthropic Claude — Sonnet para RAG/respuestas, Haiku para router y multi-query.
- Vector DB: Pinecone (índice `vmc-bot-rag`, 1024 dims, cosine). Embeddings con Pinecone Inference (multilingual-e5-large).
- Scraping: Firecrawl (Centro de Ayuda ayuda.vmcsubastas.com; futuro: inventario vmcsubastas.com).
- Config: variables en `.env` (FIRECRAWL_API_KEY, PINECONE_API_KEY, PINECONE_INDEX_NAME, ANTHROPIC_API_KEY; opcionales: WhatsApp/Twilio, STT/TTS).
- Frontend de prueba: HTML estático en `static/index.html` que llama a POST /api/ask.

**Conexiones y servicios ya integrados:**
- Anthropic: router de intención (faq | stock_search | soporte_humano | fuera_dominio), multi-query (3 variaciones de la pregunta), respuesta RAG con Sonnet.
- Pinecone: ingest de chunks (Centro de Ayuda + FAQs), búsqueda por embeddings; namespaces (helpcenter, etc.).
- Firecrawl: crawl del Centro de Ayuda, export a markdown; fuente en vivo para SubasPass (scrape de vmcsubastas.com/subaspass inyectado al contexto cuando preguntan por SubasPass).
- No hay BD SQL/NoSQL; no hay auth ni websockets en el código. MCPs en Cursor: Firecrawl y Pinecone (documentados en docs/MCP_SETUP.md).

**Lo que ya está hecho:**
- Centro de Ayuda crawleado y texto en data/raw (helpcenter_crawl, text/*.md, faqs_vmc.md).
- Taxonomía de temas y chunking semántico (por sección/tema, no por tamaño) en src/rag/chunks.py y src/ingest/taxonomy.py.
- Embeddings de Centro de Ayuda + FAQs en Pinecone (embed.py, embed_faqs.py).
- RAG: búsqueda simple + multi-query + RRF (Reciprocal Rank Fusion) → contexto → respuesta con Claude Sonnet (query_rag.py).
- Router Haiku integrado en la API: POST /api/ask usa router y según intención va a RAG, mensaje de inventario (placeholder), o soporte humano.
- Fuente en vivo SubasPass (live_source.py) para precios/planes actuales cuando preguntan por SubasPass.
- System prompt v1 (persona Subastin, glosario VMC, guardrails, español peruano) en prompts/system_prompt_v1.md.
- Web de prueba con formulario, fragmentos, respuesta y badge de intención (GET /, POST /api/ask; opción skip_router).
- Golden dataset inicial (14 entradas en data/golden_dataset/faqs_golden.json; meta 50).
- Documentación: PROJECT_CONTEXT.md, ESTRUCTURA_PROYECTO.md, DECISIONS.md, FLUJO_QUE_TENEMOS_Y_FALTA.md, RESUMEN_ESTADO_Y_SIGUIENTES_PASOS.md, roadmap y brief en docs/.

**Contexto de negocio importante:**
- Idioma: español peruano. Guardrail: precios, comisiones y plazos NUNCA inventados por el LLM; siempre desde RAG o datos scrapeados.
- Roadmap 6 semanas: Semana 1 (Discovery + base conocimiento) en curso; Semana 2 MVP RAG en WhatsApp; Semana 3 Stock + Router; luego Audio, Pilot/Handoff, Proactivo.

**Lo que falta (prioridad):**
1. Infografías y videos del Centro de Ayuda: ~95% del contenido útil está en imágenes/videos. Necesitamos pipeline: extracción de texto de infografías (Claude multimodal o OCR), transcripción de videos (Whisper + opcional Claude), chunkear y embeber en Pinecone. Ver docs/RESUMEN_ESTADO_Y_SIGUIENTES_PASOS.md §3 y docs/EXTRACCION_CENTRO_AYUDA.md.
2. Scraping de inventario: cuando intent = stock_search, buscar en datos reales (Firecrawl sobre vmcsubastas.com → JSON con vehículos y timestamp).
3. WhatsApp: webhook Meta/Twilio cuando el número esté listo.
4. Mejoras: ampliar golden dataset a ~50, prompt caching Claude, logging básico.

**Workspace:** c:\ChatBotAI; proyecto principal en la carpeta vmc-bot. Código en src/ (ingest/, rag/, server/), datos en data/raw y data/processed, prompts en prompts/.

Dado este contexto, ¿en qué deberíamos seguir trabajando ahora y qué pasos concretos recomiendas?
```

---

## Versión corta (si necesitas limitar caracteres)

```
Proyecto: chatbot RAG para VMC Subastas (Perú), canal WhatsApp (aún no conectado). Stack: Python, FastAPI, Claude (Anthropic), Pinecone (vector DB), Firecrawl. Hecho: crawl Centro de Ayuda, chunking semántico, embeddings en Pinecone, RAG con multi-query+RRF, router de intención (Haiku), fuente en vivo SubasPass, system prompt v1, web de prueba POST /api/ask, golden dataset (14 entradas). Falta: extracción de infografías/videos del Centro de Ayuda (~95% contenido en imágenes/video), scraping inventario para stock_search, WhatsApp webhook, ampliar golden dataset, prompt caching y logs. Workspace: c:\ChatBotAI\vmc-bot. ¿En qué seguir y qué pasos concretos recomiendas?
```

---

*Generado para dar contexto a Claude. Actualizar este archivo cuando cambie el estado del proyecto.*
