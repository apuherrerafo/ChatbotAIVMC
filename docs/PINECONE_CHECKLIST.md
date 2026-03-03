# Checklist Pinecone — 5 min

**Guía detallada:** Ver **`docs/PINECONE_PASO_A_PASO.md`** (qué hacer en la consola, paso a paso).

Para poder cargar embeddings (script `python -m src.rag.embed`) necesitas:

1. **Cuenta:** [pinecone.io](https://www.pinecone.io) → Sign up (plan gratis).
2. **Crear índice con inferencia integrada** (recomendado):
   - En la consola: Create Index → elegir **embedding model** (ej. multilingual-e5-large).
   - Name: `vmc-bot-rag`
   - Field map: el campo de texto debe llamarse **`text`** (el script envía `record["text"]`).
   - Si en tu plan solo puedes crear índice clásico: dimension 1024, metric cosine; entonces habría que generar embeddings fuera (otro script) y hacer upsert de vectores.
3. **API Key:** En la consola → API Keys → copiar.
4. **En `vmc-bot/.env`:**  
   `PINECONE_API_KEY=tu_key`  
   `PINECONE_INDEX_NAME=vmc-bot-rag`

Luego ejecutar: `python -m src.rag.embed`
