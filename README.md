# VMC-Bot

Chatbot de IA para VMC Subastas (plataforma de subastas de vehículos en Perú).  
Opera por WhatsApp Business API. Desarrollo 100% AI-driven con Cursor + MCPs.

## Stack

| Componente | Tecnología |
|------------|------------|
| LLM principal | Claude Sonnet 4.5 (RAG + conversación) |
| LLM router | Claude Haiku 4.5 (intención: FAQ / stock / soporte humano) |
| Embeddings | Pinecone Inference (multilingual-e5-large) |
| Vector DB | Pinecone (Starter) |
| Scraping | Firecrawl (Centro de Ayuda + inventario) |
| STT | Gemini 2.5 Flash |
| TTS | ElevenLabs |
| Canal | WhatsApp Business API (Meta Cloud API / Twilio) |
| Servidor | FastAPI (webhook) |
| Hosting | Vercel (web) / Railway / Render |

## Fase actual

**Semana 1 — Discovery + Base de Conocimiento**

- Recolectar contenido del Centro de Ayuda (ayuda.vmcsubastas.com)
- Limpiar, chunkear por tema, generar embeddings, cargar en Pinecone
- System prompt v1, golden dataset 50 preguntas, config MCPs

## Documentos de referencia

- **docs/VMC_Bot_Roadmap_AI_Driven_v2.md** — Roadmap técnico (KPIs, stack, costos, 6 semanas, desafíos)
- **docs/VMC_Bot_Strategic_Brief_v2.md** — Brief estratégico (3 fases: Build Trust → Monetize Attention → Flip the Model; visión demanda, SEO loop, prerequisitos VMC)

## Uso

```bash
cd vmc-bot
pip install -r requirements.txt
# Copiar .env.example a .env y configurar variables
```

### Probar el RAG en el navegador (sin WhatsApp)

```bash
python -m uvicorn src.server.app:app --reload --port 8000
```

Abre **http://127.0.0.1:8000** en el navegador: escribe una pregunta, pulsa Enviar y verás los fragmentos recuperados y la respuesta del modelo.

### Probar el RAG por terminal

```bash
# Solo búsqueda (muestra chunks recuperados)
python -m src.rag.query_rag "¿Qué son los SubasCoins?"

# Con respuesta generada por Claude (requiere ANTHROPIC_API_KEY en .env)
python -m src.rag.query_rag "¿Cómo consigno?"
```

Ver `docs/PROJECT_CONTEXT.md` para contexto completo y `docs/DECISIONS.md` para decisiones técnicas.

## Deploy en Vercel y GitHub

- **Entrypoint:** la app FastAPI se expone en `src/index.py` para que Vercel la detecte.
- **Repositorio:** sube el proyecto a GitHub y en [Vercel](https://vercel.com) conecta el repo; cada push a `main` despliega automáticamente.
- **Variables de entorno (Vercel):** en el proyecto de Vercel → Settings → Environment Variables, configura al menos:
  - `ANTHROPIC_API_KEY`
  - `PINECONE_API_KEY`
  - `PINECONE_INDEX_NAME` (ej. `vmc-bot-rag`)
  - Opcional: `UPSTASH_REDIS_REST_URL` y `UPSTASH_REDIS_REST_TOKEN` para saldo persistente; si no, se usa saldo en memoria.
- **Deploy desde CLI:** `npm i -g vercel` y en la raíz del proyecto ejecuta `vercel` (o `vercel --prod`).
