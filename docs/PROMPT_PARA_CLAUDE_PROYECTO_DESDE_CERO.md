# Prompt para Claude — Proyecto desde cero y ayuda a estructurar

Copia todo el bloque **"Para pegar en Claude"** y pégalo en una conversación nueva con Claude. Así Claude no asume que sabe nada del proyecto y puede ayudarte a estructurar todo (incluido rules, skills y subagents que ves vacíos).

---

## Para pegar en Claude

```
No conoces este proyecto. Te doy contexto desde cero para que puedas ayudarme a estructurarlo y a que nada quede “en el aire”.

---

## 1. Qué es el proyecto

- **Nombre:** VMC-Bot (dentro del workspace ChatBotAI).
- **Qué es:** Un chatbot de IA para **VMC Subastas**, una plataforma de subastas de vehículos en **Perú**. El canal objetivo es **WhatsApp Business API** (por ahora no está conectado; se prueba en una web).
- **Quién lo desarrolla:** Un Lead AI Engineer. No hay equipo de programadores; el desarrollo es **100% AI-driven** con Cursor y MCPs (Firecrawl, Pinecone, etc.).
- **Visión:** No es “solo un chatbot”. Es un **sistema de inteligencia de demanda** con interfaz conversacional: el bot es la interfaz; el producto es la capa de inteligencia (señales de demanda, preferencias, etc.). Roadmap en 6 semanas: Semana 1 Discovery + base de conocimiento; Semana 2 MVP RAG en WhatsApp; Semana 3 Stock + Router; luego Audio, Pilot/Handoff, Proactivo.

---

## 2. Dónde está todo (workspace y estructura)

- **Workspace raíz:** `c:\ChatBotAI` (o la ruta que tengas). Dentro hay una carpeta **`vmc-bot`** que es el proyecto principal.
- **Estructura relevante de vmc-bot:**

  - **`src/`** — Código:
    - `src/ingest/` — Crawl Centro de Ayuda (Firecrawl), taxonomía, scripts de ingest (imágenes, FAQs).
    - `src/rag/` — Embeddings, Pinecone, búsqueda, multi-query, RRF, router de intención (Haiku), respuesta con Claude (Sonnet), fuente en vivo SubasPass.
    - `src/server/` — FastAPI: GET / (página de prueba), POST /api/ask (router + RAG), rate limit, logs.
  - **`data/`** — Datos:
    - `data/raw/` — Contenido crudo: crawl del Centro de Ayuda (text/*.md), FAQs, términos.
    - `data/processed/` — Chunks procesados, listos para embeber.
    - `data/golden_dataset/` — Preguntas con respuestas esperadas (evaluación).
  - **`prompts/`** — System prompt v1 (persona Subastin, glosario VMC, guardrails, español peruano).
  - **`static/`** — Frontend de prueba (index.html) que llama a POST /api/ask.
  - **`docs/`** — Toda la documentación: PROJECT_CONTEXT.md, ESTRUCTURA_PROYECTO.md, DECISIONS.md, FLUJO_QUE_TENEMOS_Y_FALTA.md, RESUMEN_ESTADO_Y_SIGUIENTES_PASOS.md, PROMPT_PARA_CLAUDE_CONTEXTO.md, roadmap, brief, MCP_SETUP.md, etc.
  - **`.env`** — API keys (Anthropic, Pinecone, Firecrawl, etc.). No se sube al repo.
  - **`.cursor/rules/`** — Reglas de Cursor para el proyecto (están **dentro de vmc-bot**, no en la raíz del workspace).

- Si tu workspace en Cursor está abierto en **`c:\ChatBotAI`** (la raíz), Cursor puede no estar aplicando las reglas que están en **`vmc-bot/.cursor/rules/`**. Por eso a veces parece que “rules, skills y subagents están vacíos”: las reglas existen pero bajo `vmc-bot`, y skills/subagents de Cursor pueden no estar definidos a nivel de workspace.

---

## 3. Stack técnico (resumen)

| Componente        | Tecnología                                      |
|------------------|--------------------------------------------------|
| Backend          | Python, FastAPI, Uvicorn (puerto 8000)          |
| LLM principal    | Claude Sonnet 4.5 (Anthropic) — RAG, respuestas |
| LLM router       | Claude Haiku 4.5 (Anthropic) — intención, multi-query |
| Embeddings       | Pinecone Inference (multilingual-e5-large)     |
| Vector DB        | Pinecone (índice `vmc-bot-rag`, 1024 dims)      |
| Scraping         | Firecrawl (Centro de Ayuda, SubasPass en vivo)  |
| Canal objetivo   | WhatsApp Business API (aún no conectado)        |
| Sin LangChain    | Llamadas directas a Anthropic y Pinecone       |

Regla de negocio crítica: **precios, comisiones y plazos NUNCA los inventa el LLM**; siempre vienen del RAG o de datos scrapeados.

---

## 4. Qué está hecho hoy

- Centro de Ayuda (ayuda.vmcsubastas.com) crawleado; texto en `data/raw/text/*.md` y FAQs en `data/raw/faqs_vmc.md`.
- Taxonomía de temas y chunking semántico (por sección/tema) en `src/rag/chunks.py` y `src/ingest/taxonomy.py`.
- Embeddings del Centro de Ayuda + FAQs en Pinecone (namespace `helpcenter`).
- RAG: búsqueda → multi-query (3 variaciones con Haiku) → RRF → contexto → respuesta con Claude Sonnet (`query_rag.py`).
- Router de intención (Haiku): `faq | stock_search | soporte_humano | fuera_dominio`; la API usa el router y según la intención va a RAG, mensaje de inventario (placeholder) o soporte humano.
- Fuente en vivo SubasPass: cuando preguntan por SubasPass se scrapea vmcsubastas.com/subaspass y se inyecta al contexto.
- System prompt v1 en `prompts/system_prompt_v1.md`.
- Web de prueba: GET / y POST /api/ask (con opción skip_router); muestra fragmentos, respuesta y badge de intención.
- Golden dataset inicial (14 entradas; meta 50) en `data/golden_dataset/faqs_golden.json`.
- Algunas reglas de Cursor en `vmc-bot/.cursor/rules/` (regla general, contexto, RAG, router, Firecrawl, WhatsApp, tono, skills de ingest/infografías/golden/inventario, subagents evaluador/auditor/monitor costos/validador WhatsApp/tester tono/refinador prompt). No hay AGENTS.md ni .cursorrules en la raíz del workspace; las “skills” y “subagents” que ves en la UI pueden estar vacíos porque no están definidos a nivel del workspace raíz.

---

## 5. Qué falta (prioridad)

- **Contenido multimodal:** ~95% del contenido útil del Centro de Ayuda está en infografías y videos. Falta pipeline: extracción de texto de imágenes (Claude Vision/OCR), transcripción de videos (Whisper), chunkear y embeber.
- **Inventario:** Cuando la intención es `stock_search`, usar datos reales (scraping vmcsubastas.com → vehículos con timestamp).
- **WhatsApp:** Webhook cuando el número esté listo (Meta Cloud API o Twilio).
- **Calidad:** Ampliar golden dataset a ~50; evaluación sistemática; prompt caching; logging (pregunta, intención, latencia, errores).
- **Rate limits:** Recientemente hubo errores 429 de Anthropic (límite de tokens por minuto). Se añadieron: límite de tamaño de contexto RAG (MAX_CONTEXT_CHARS), mensaje amigable al usuario cuando hay rate limit, y opcionalmente auditoría en logs. Si quieres, podemos revisar que la estrategia esté bien documentada y que no vuelva a “explotar” en cara al usuario.

---

## 6. Lo que necesito de ti

1. **Estructurar todo el proyecto** desde tu perspectiva: qué documentos son la “fuente de verdad”, qué carpeta hace qué, y cómo debería alguien (o otra IA) orientarse en `c:\ChatBotAI` y `vmc-bot` sin asumir conocimiento previo.
2. **Rules, skills y subagents “vacíos”:** En Cursor, las reglas están en `vmc-bot/.cursor/rules/` pero el workspace puede ser `c:\ChatBotAI`. Ayúdame a decidir:
   - Si conviene tener un único punto de entrada (por ejemplo un AGENTS.md o .cursor/rules en la raíz) que describa el proyecto y enlace o incluya lo de vmc-bot.
   - Cómo definir **skills** y **subagents** de forma que no queden vacíos: qué skills tendría sentido (por ejemplo: “ingest Pinecone”, “evaluar RAG con golden dataset”, “auditar contenido”) y qué subagents (evaluador RAG, auditor de contenido, monitor de costos, etc.) y dónde documentarlos.
3. **Revisar** que la respuesta a problemas recientes (rate limit 429, mensaje al usuario, límite de contexto) esté bien reflejada en la estructura y en las reglas, para que no vuelva a pasar sin control.

Cuando me des recomendaciones, indícame pasos concretos (por ejemplo: “crear en la raíz del workspace el archivo X con el contenido Y” o “añadir en vmc-bot/.cursor la regla Z”) para que pueda aplicarlos sin tener que interpretar.
```

---

*Puedes editar el bloque anterior si quieres añadir o quitar detalles antes de pegarlo en Claude.*
