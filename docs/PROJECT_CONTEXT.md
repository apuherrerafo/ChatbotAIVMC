# Contexto del proyecto VMC-Bot

> Resumen para Cursor y para cualquier iteración futura. Basado en el prompt de contexto inicial.

## Quién lidera

Lead AI Engineer. No hay equipo de programadores — desarrollo 100% AI-driven con Cursor y MCPs.

## Qué construimos

Chatbot de IA para **VMC Subastas** (subastas de vehículos en Perú) por **WhatsApp Business API**:

1. Responder FAQs (registro, SubasCoins, comisiones, consignaciones, etc.)
2. Buscar vehículos en inventario con datos reales (scraping)
3. Procesar notas de voz (STT/TTS)
4. Escalar a agente humano cuando no pueda resolver
5. Notificaciones proactivas sobre vehículos de interés

## Stack tecnológico

- **LLM principal:** Claude Sonnet 4.5 (conversación + RAG)
- **LLM router:** Claude Haiku 4.5 (clasificación: FAQ vs stock vs soporte humano)
- **Embeddings:** Pinecone Inference (multilingual-e5-large)
- **Vector DB:** Pinecone (Starter, gratis)
- **Scraping:** Firecrawl (Centro de Ayuda + inventario diario vmcsubastas.com)
- **STT:** Gemini 2.5 Flash (voz WhatsApp)
- **TTS:** ElevenLabs
- **Canal:** WhatsApp Business API (Meta Cloud API o Twilio)
- **Servidor:** FastAPI (webhook ligero)
- **Hosting:** Railway o Render
- **IDE:** Cursor + MCPs (Firecrawl, Pinecone)

## Fase actual: Semana 1 — Discovery + Base de Conocimiento

1. Recolectar contenido del Centro de Ayuda (ayuda.vmcsubastas.com) — **~95% en infografías/imágenes**
2. Limpiar y chunkear por tema/sección (no por tamaño arbitrario)
3. Generar embeddings y cargar en Pinecone
4. Redactar system prompt v1 (persona VMC, glosario, guardrails, tono español peruano)
5. Golden dataset: 50 preguntas con respuestas esperadas
6. Configurar proyecto en Cursor con MCPs

## Contexto crítico del negocio

- **Idioma:** Español peruano ("carro", "jalar", etc.)
- **Glosario:** SubasCoins, Ganador Directo, Riesgo Usuario, Calidad de Miembro, comisiones por tramo
- **Meta 2026:** Bot con propósito definido; solo dominio VMC Subastas
- **Guardrail financiero:** Precios, comisiones y plazos NUNCA del LLM; siempre RAG o JSON scrapeado
- **KPIs:** Deflexión 40%, alucinación < 2%, latencia < 3s, errores de precio = 0

## Cómo trabajar

1. Priorizar calidad de datos para RAG
2. Código limpio y modular
3. Estructura de carpetas clara desde el inicio
4. Decisiones técnicas: explicar opciones y pros/contras antes de implementar
5. Documentar en DECISIONS.md y comentarios
6. Comentarios en español; nombres de variables descriptivos
7. Chunks semánticos (por tema/pregunta) antes que por tamaño
8. Si algo no es posible o tiene riesgo, decirlo directo

## Visión estratégica (fuente: Strategic Brief v2)

**No es solo un chatbot.** Es la construcción de un **sistema de inteligencia de demanda** con interfaz conversacional. El bot es la interfaz; el producto es la capa de inteligencia.

### Las tres fases (más allá de las 6 semanas)

| Fase | Timeline | Enfoque |
|------|----------|---------|
| **1 — Build Trust** | Semanas 1–6 | Soporte WhatsApp + bot de inventario (lo que cubre el Roadmap) |
| **2 — Monetize Attention** | Semanas 7–14 | Co-piloto de subasta en vivo (WebSocket/SSE, eventos en tiempo real, throttling 5–7 msgs/evento) |
| **3 — Flip the Model** | Continuo | Conversación → señales de demanda (preferencias, pujas, ubicación, preguntas sin respuesta → consignación, precios reserva, SEO, roadmap, retención) |

**SEO Synergy Loop:** Consultas no respondidas del bot → nuevas páginas → mejor ranking → más señales de demanda.

## Fases de desarrollo Semana 1–6 (Roadmap)

| Semana | Fase |
|--------|------|
| 1 | Discovery + Vector Store |
| 2 | MVP RAG en WhatsApp |
| 3 | Stock + Router |
| 4 | Audio |
| 5 | Pilot + Handoff |
| 6 | Proactivo + Escalar |

**Costos (60 chats/día):** $135–$168/mes (o $81–$109 Meta directo); ~$0.08/conversación.  
**Métricas por fase:** Deflexión 40%→55%→70%; Lead→Bid +15%→+30%→+40%; cost/conv $0.08→$0.06→&lt;$0.04 (ver Strategic Brief).

## Documentos de referencia (en repo)

- **docs/VMC_Bot_Roadmap_AI_Driven_v2.md** — Roadmap técnico (KPIs, stack, costos, 6 semanas, desafíos)
- **docs/VMC_Bot_Strategic_Brief_v2.md** — Brief estratégico (3 fases, visión demanda, SEO loop, prerequisitos VMC, métricas por fase)
