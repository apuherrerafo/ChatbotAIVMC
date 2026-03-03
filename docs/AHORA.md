# Qué hacer ahora — Día 1 (Jue 26 feb)

Sigue estos pasos en orden. Cuando termines uno, avisa y pasamos al siguiente.

---

## Paso 1 — Firecrawl (≈10 min)

1. Abre **[firecrawl.dev](https://firecrawl.dev)** en el navegador.
2. Regístrate o inicia sesión (plan gratuito).
3. Ve a **API Keys** o **Dashboard** y **copia tu API key**.
4. En el proyecto `vmc-bot`:
   - Si no existe `vmc-bot/.env`, copia `.env.example` y renómbralo a `.env`.
   - Pega la key en `.env`: `FIRECRAWL_API_KEY=fc-xxxxxxxx`
5. **Configura el MCP en Cursor:**
   - Abre la config de MCP de Cursor (en Windows suele ser `C:\Users\TuUsuario\.cursor\mcp.json` o desde Cursor: **Settings → MCP**).
   - Si el archivo está vacío o no existe, usa esta estructura (ajustando si ya tienes otros MCPs):

```json
{
  "mcpServers": {
    "firecrawl": {
      "command": "npx",
      "args": ["-y", "@anthropic-ai/firecrawl-mcp"],
      "env": {
        "FIRECRAWL_API_KEY": "PEGA_AQUI_TU_KEY"
      }
    }
  }
}
```

6. Guarda y **reinicia Cursor** (o recarga ventana) para que cargue el MCP.

**Listo cuando:** Tengas la API key en `.env` y en `mcp.json`, y Cursor haya recargado.

---

## Paso 2 — Pinecone (≈10 min)

1. Abre **[pinecone.io](https://www.pinecone.io)** y crea cuenta (plan gratis).
2. En el **Pinecone Console** crea un **Index**:
   - **Name:** `vmc-bot-rag`
   - **Dimensions:** `1024` (multilingual-e5-large; si usas otro modelo, ajusta)
   - **Metric:** cosine
   - Deja el resto por defecto.
3. Copia tu **API Key** desde la consola (en API Keys).
4. En `vmc-bot/.env` añade o completa:
   - `PINECONE_API_KEY=tu_key`
   - `PINECONE_INDEX_NAME=vmc-bot-rag`
5. *(Opcional para hoy)* Si quieres usar Pinecone desde Cursor por MCP, busca un MCP de Pinecone (ej. `@pinecone-io/pinecone-mcp` o similar) y añádelo a `mcp.json`. Para Semana 1 podemos usar solo el SDK de Python; el MCP es opcional.

**Listo cuando:** Tengas índice `vmc-bot-rag` creado y la API key en `.env`.

---

## Paso 3 — Primer crawl con Firecrawl

Cuando los pasos 1 y 2 estén hechos, **avisa**. Haremos juntos:

1. Crawl de **ayuda.vmcsubastas.com** (con Firecrawl MCP o con script).
2. Guardar resultado en `data/raw/helpcenter_crawl.json`.
3. Clasificar URLs: tiene texto / solo imágenes / mixto.

---

**Resumen:** Ahora mismo → **Paso 1 (Firecrawl)**. Luego Paso 2 (Pinecone). Después te guío para el crawl.
