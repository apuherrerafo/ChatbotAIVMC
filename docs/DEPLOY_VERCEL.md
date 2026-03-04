# Deploy en Vercel — Variables de entorno

Configura estas variables en **Vercel → Project → Settings → Environment Variables** antes del primer deploy (o para que el bot responda correctamente).

## Obligatorias para el bot RAG

| Variable | Descripción |
|----------|-------------|
| `ANTHROPIC_API_KEY` | API key de Anthropic (Claude). Sin ella el bot no genera respuestas. |
| `PINECONE_API_KEY` | API key de Pinecone. |
| `PINECONE_INDEX_NAME` | Nombre del índice (ej. `vmc-bot-rag`). |

## Opcionales

| Variable | Descripción | Default |
|----------|-------------|---------|
| `UPSTASH_REDIS_REST_URL` | URL REST de Upstash Redis (saldo persistente). | — |
| `UPSTASH_REDIS_REST_TOKEN` | Token de Upstash Redis. | — |
| `BALANCE_ADMIN_TOKEN` | Token para proteger POST /api/balance. | — |
| `ANTHROPIC_INITIAL_BALANCE_USD` | Saldo inicial en USD para el contador. | 5.0 |
| `DEBUG_MODE` | `true` para incluir debug en POST /api/ask. | false |
| `RAG_TOP_K` | Número de chunks a recuperar. | 3 |
| `MAX_CONTEXT_TOKENS` | Límite de tokens de contexto al LLM. | 3000 |

Vercel define automáticamente `VERCEL=1`; el código lo usa para escribir logs en `/tmp` (filesystem read-only en serverless).
