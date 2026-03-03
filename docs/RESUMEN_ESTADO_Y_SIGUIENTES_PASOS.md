# VMC-Bot — Resumen de lo hecho y qué sigue

**Última actualización:** Feb 2026

---

## 1. Resumen de lo que hemos hecho hasta ahora

### Base de datos de conocimiento
| Qué | Dónde |
|-----|--------|
| **Centro de Ayuda** crawleado (ayuda.vmcsubastas.com) | `data/raw/helpcenter_crawl.json`, `data/raw/text/*.md` |
| **FAQs oficiales** VMC en texto | `data/raw/faqs_vmc.md` → `data/processed/faq_chunks.json` |
| **Taxonomía de temas** (registro, SubasCoins, consignación, etc.) | `src/ingest/taxonomy.py` |
| **Chunking semántico** (por `##`/`###`, limpieza, flag numérico) | `src/rag/chunks.py` |
| **Embeddings + Pinecone** (multilingual-e5-large, índice `vmc-bot-rag`, namespace `helpcenter`) | `src/rag/embed.py`, `embed_faqs.py` |

### RAG (retrieval + respuesta)
| Qué | Dónde |
|-----|--------|
| Búsqueda en Pinecone (1 query) | `src/rag/query_rag.py` → `search()` |
| **Multi-Query:** Haiku genera 3 variaciones de la pregunta | `src/rag/multi_query.py` |
| **RRF** (Reciprocal Rank Fusion) para fusionar las 3 búsquedas | `src/rag/rrf.py` |
| Pipeline: pregunta → 3 queries → 3 búsquedas → RRF → contexto | `query_rag.py` → `search_multi_query_rrf()` |
| Respuesta con **Claude Sonnet** (system prompt + contexto) | `query_rag.py` → `answer_with_claude()` |
| **Fuente en tiempo real SubasPass:** cuando preguntan por SubasPass, se scrapea https://www.vmcsubastas.com/subaspass con Firecrawl y se inyecta al contexto (precios/planes actuales) | `src/rag/live_source.py` + integrado en `ask_rag()` |

### Router de intención
| Qué | Dónde |
|-----|--------|
| **Clasificador Haiku:** faq \| stock_search \| soporte_humano \| fuera_dominio | `src/rag/router.py` → `classify_intent()` |
| Integración: API llama al router y según intención va a RAG, mensaje de inventario, o mensaje de soporte/escalamiento | `src/rag/query_rag.py` → `ask_with_router()`, `src/server/app.py` |

### Interfaz y API
| Qué | Dónde |
|-----|--------|
| **Web de prueba** (formulario + fragmentos + respuesta + badge de intención) | `src/server/app.py`, `static/index.html` |
| **POST /api/ask** con opción `skip_router` para ir directo a RAG | `src/server/app.py` |

### Prompts y evaluación
| Qué | Dónde |
|-----|--------|
| System prompt v1 (persona Subastin, glosario, guardrails, tono español peruano) | `prompts/system_prompt_v1.md` |
| Golden dataset inicial (14 entradas; meta 50) | `data/golden_dataset/faqs_golden.json` |

### Configuración
| Qué | Dónde |
|-----|--------|
| API keys y env | `vmc-bot/.env` (FIRECRAWL, PINECONE, ANTHROPIC), `.env.example` |
| Reglas Cursor (contexto proyecto, bRAG sin LangChain) | `.cursor/rules/vmc-bot-context.mdc`, `bRAG-langchain-referencia.mdc` |

---

## 2. Qué sigue (orden sugerido)

### Inmediato / corto plazo
1. **Infografías y videos del Centro de Ayuda**  
   Hoy el Centro de Ayuda tiene ~95% del contenido útil en **imágenes/infografías y videos**. Necesitamos un pipeline que:
   - **Infografías/gráficos:** extraiga texto (y estructura) desde imágenes (Claude multimodal o OCR).
   - **Videos:** transcribir y/o resumir (Whisper + Claude o servicio de transcripción) y usar ese texto en RAG.  
   Ver sección 3 más abajo.

2. **Scraping de inventario**  
   Cuando la intención es `stock_search`, buscar en datos reales: Firecrawl (o similar) sobre vmcsubastas.com → JSON con vehículos y timestamp → búsqueda por texto/filtros y respuesta con disclaimer de fecha.

3. **WhatsApp**  
   Cuando el número/eSIM esté listo: webhook (Meta Cloud API o Twilio), verificación, conectar el flujo actual (router → RAG o stock o mensaje fijo).

### Mejoras de calidad y producción
4. **Ampliar golden dataset** a ~50 entradas y usarlo para evaluación (métricas de deflexión, alucinación, errores de precio).
5. **Prompt caching** en Claude (system + contexto) para reducir costo y latencia.
6. **Logging** básico (pregunta, intención, latencia, errores) sin LangSmith.

---

## 3. Infografías, gráficos y videos del Centro de Ayuda

### Problema
En ayuda.vmcsubastas.com la mayor parte del contenido útil está en **infografías/imágenes** y en **videos**, no en texto HTML. Para que el RAG pueda responder con esa información, hay que convertir imagen/video en texto (o descripción) y cargarla a Pinecone.

### Enfoque propuesto

#### A) Infografías y gráficos
| Opción | Descripción | Pros | Contras |
|--------|-------------|------|--------|
| **Claude (o GPT-4V) multimodal** | Enviar cada imagen al modelo y pedir descripción/transcripción (tablas, números, pasos). | Buena calidad en tablas e infografías; entiende contexto. | Coste por imagen; hay que descargar/adjuntar cada una. |
| **OCR (Tesseract / Google Vision)** | Extraer texto de la imagen. | Barato, escalable. | Peor en diseños complejos e infografías con mucho layout. |

**Recomendación:**  
- Para artículos clave (comisiones, SubasCoins, registro): **modelo multimodal** (Claude con imagen) y guardar el texto por artículo en `data/processed/` (ej. markdown por URL).  
- Para el resto: probar **OCR**; si la calidad es suficiente, usarlo; si no, ampliar el conjunto con multimodal.

**Flujo técnico sugerido:**
1. Del crawl del Centro de Ayuda, obtener lista de URLs de imágenes (Firecrawl ya puede devolver enlaces a imágenes en las páginas).
2. Script de ingest: por cada artículo “con infografías”, descargar imágenes, llamar a Claude (content block tipo image) y guardar texto en `data/processed/helpcenter_images/<slug>.md`.
3. Incluir esos markdowns en el chunking actual (o chunkear por sección) y re-embeber en Pinecone (mismo índice, mismo namespace o uno dedicado `helpcenter_images`).

#### B) Videos
| Opción | Descripción | Pros | Contras |
|--------|-------------|------|--------|
| **Transcripción (Whisper / API de transcripción)** | Obtener audio del video → transcripción en texto. | Estándar, bien soportado. | Solo audio; no describe gestos ni gráficos en pantalla. |
| **Resumen con modelo** | Pasar transcripción (y opcionalmente frames clave) a Claude para resumir por temas. | Texto listo para RAG. | Un paso más; coste por video. |
| **Servicios tipo YouTube Auto-captions** | Si los videos están en YouTube/Vimeo, usar captions existentes. | Rápido si ya existen. | No todos los videos tienen captions; puede haber que transcribir igual. |

**Recomendación:**  
1. Inventariar dónde están los videos (embed en ayuda.vmcsubastas.com, YouTube, etc.).  
2. Extraer audio (yt-dlp u otra herramienta) y transcribir con **Whisper** (local o API).  
3. Opcional: pasar la transcripción por Claude para resumir por “preguntas que responde este video” y guardar en markdown.  
4. Chunkear y embeber ese texto como cualquier otro fragmento del Centro de Ayuda; en metadata indicar `tipo: video` y `source_url` al video.

### Guardrails (igual que hoy)
- Números (precios, comisiones, plazos) **solo** desde texto extraído o datos oficiales, **nunca** inventados por el LLM.
- Marcar chunks con “datos numéricos sensibles” para que el sistema priorice citar fuente.

### Próximos pasos concretos (infografías + videos)
1. **Inventario:** Listar URLs de imágenes y de videos del Centro de Ayuda (a partir del crawl existente o un nuevo crawl que guarde también media).  
2. **Piloto infografías:** Elegir 3–5 artículos con infografías; descargar imágenes; probar extracción con Claude (multimodal) y con Tesseract; decidir estrategia por tipo de página.  
3. **Piloto videos:** Elegir 2–3 videos; extraer audio → Whisper → texto; opcional resumen Claude; guardar en `data/processed/` y añadir al pipeline de chunks/embed.  
4. **Pipeline unificado:** Script(s) en `src/ingest/` que ejecuten Capa 1 (Firecrawl) + Capa 2 (imágenes con multimodal/OCR) + Capa 3 (videos con transcripción) y escriban en `data/raw/` y `data/processed/` antes de embeber en Pinecone.

---

## 4. Referencias rápidas

- **Flujo actual (qué tenemos / qué falta):** `docs/FLUJO_QUE_TENEMOS_Y_FALTA.md`  
- **Estrategia de extracción Centro de Ayuda:** `docs/EXTRACCION_CENTRO_AYUDA.md`  
- **Contexto y stack:** `docs/PROJECT_CONTEXT.md`  
- **Plan Semana 1 y fechas:** `docs/SEMANA_1_PLAN.md`
