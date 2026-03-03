# Estructura del proyecto VMC-Bot

```
vmc-bot/
├── README.md
├── requirements.txt
├── .env.example          # Copiar a .env (no subir .env)
├── docs/
│   ├── PROJECT_CONTEXT.md      # Contexto completo del proyecto
│   ├── DECISIONS.md            # Decisiones técnicas
│   ├── MCP_SETUP.md            # Config Firecrawl + Pinecone MCPs
│   ├── EXTRACCION_CENTRO_AYUDA.md  # Estrategia extracción (imágenes)
│   ├── ESTRUCTURA_PROYECTO.md  # Este archivo
│   └── ...
├── src/
│   ├── ingest/                 # Recolectar contenido
│   │   ├── helpcenter.py       # Centro de Ayuda (Firecrawl + imágenes)
│   │   └── inventory.py        # (futuro) Inventario diario vmcsubastas.com
│   ├── rag/                    # Embeddings, Pinecone, retrieval
│   │   ├── embed.py            # (futuro) Generar embeddings
│   │   ├── chunks.py           # (futuro) Chunking semántico por tema
│   │   └── retrieve.py         # (futuro) Query Pinecone + contexto
│   └── server/                 # FastAPI webhook WhatsApp
│       └── app.py              # (futuro) Webhook + router + RAG
├── prompts/
│   └── system_prompt_v1.md     # System prompt v1 (persona, glosario, guardrails)
├── data/
│   ├── raw/                    # Contenido scrapeado/descargado crudo
│   ├── processed/              # Texto limpio, chunked, listo para embeber
│   └── golden_dataset/         # 50 preguntas con respuestas esperadas
└── tests/                      # (futuro) Tests por componente
```

## Convenciones

- **Comentarios y docs:** español.
- **Nombres de variables/funciones:** descriptivos en inglés o español según convención del equipo.
- **Chunks:** semánticos (por tema/pregunta), no por tamaño fijo.
- **Números (precios, comisiones):** nunca generados por el LLM; siempre desde RAG o datos scrapeados.
