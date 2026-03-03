# Configuración de MCPs — VMC-Bot

Guía para configurar los MCPs necesarios en Cursor para el proyecto.

---

## MCPs requeridos

| MCP | Uso en el proyecto |
|-----|--------------------|
| **Firecrawl** | Scraping del Centro de Ayuda (ayuda.vmcsubastas.com) e inventario diario de vmcsubastas.com |
| **Pinecone** | Vector DB para embeddings del RAG (índices, upsert, query) |

*(Otros MCPs opcionales según necesidad: no hay MCP oficial de ElevenLabs/Twilio en la lista por defecto.)*

---

## 1. Firecrawl MCP

**Qué hace:** Convierte URLs en markdown/JSON limpio; útil para páginas con texto. Para páginas que son sobre todo imágenes, Firecrawl puede devolver la estructura y URLs de imágenes; la extracción de texto de esas imágenes se hace aparte (ver `EXTRACCION_CENTRO_AYUDA.md`).

**Configuración en Cursor:**

1. Obtener API key en [firecrawl.dev](https://firecrawl.dev) (plan gratuito disponible).
2. Añadir el servidor MCP de Firecrawl en la config de Cursor:
   - **Archivo:** `~/.cursor/mcp.json` (o la config de MCP que use tu instalación).
   - **Ejemplo de entrada:**

```json
{
  "mcpServers": {
    "firecrawl": {
      "command": "npx",
      "args": ["-y", "@anthropic-ai/firecrawl-mcp"],
      "env": {
        "FIRECRAWL_API_KEY": "<tu_api_key>"
      }
    }
  }
}
```

3. Sustituir `<tu_api_key>` por tu clave.
4. Reiniciar Cursor o recargar MCPs.

**Variables de entorno del proyecto:** Añadir `FIRECRAWL_API_KEY` en `.env` del repo para scripts que usen Firecrawl por SDK (no solo por MCP).

---

## 2. Pinecone MCP

**Qué hace:** Gestionar índices en Pinecone, hacer upsert de vectores y queries por similitud (para RAG).

**Configuración en Cursor:**

1. Cuenta en [pinecone.io](https://www.pinecone.io) — plan Starter (gratis).
2. Crear un índice (ej. `vmc-bot-rag`) con dimensión acorde a tu modelo de embeddings (multilingual-e5-large suele ser 1024; ver documentación de Pinecone Inference).
3. Añadir MCP de Pinecone en la config de Cursor. Depende del paquete que uses; ejemplo genérico:

```json
{
  "mcpServers": {
    "pinecone": {
      "command": "npx",
      "args": ["-y", "pinecone-mcp"],
      "env": {
        "PINECONE_API_KEY": "<tu_api_key>",
        "PINECONE_INDEX_HOST": "<host_del_indice>"
      }
    }
  }
}
```

*(Comprobar en la documentación del MCP de Pinecone el nombre exacto del paquete y las variables; a veces el host es opcional si se usa solo API key + nombre del índice.)*

4. En el proyecto, usar las mismas credenciales en `.env` para los scripts de ingest y el servidor:

- `PINECONE_API_KEY`
- `PINECONE_INDEX_NAME` (o `PINECONE_INDEX_HOST` según el cliente)

---

## 3. Verificación

- **Firecrawl:** En Cursor, usar el MCP para scrapear una URL de prueba (ej. una página de ayuda con algo de texto) y comprobar que devuelve contenido.
- **Pinecone:** Crear un índice de prueba, hacer upsert de un vector de prueba y una query; comprobar en la consola de Pinecone que los datos aparecen.

---

## 4. Referencias

- Firecrawl: [firecrawl.dev](https://firecrawl.dev)  
- Pinecone: [docs.pinecone.io](https://docs.pinecone.io)  
- Cursor MCP: documentación de Cursor sobre “MCP” / “Model Context Protocol” para la ruta exacta de `mcp.json` en tu OS.

Cuando tengas los nombres exactos de los paquetes npm (o comandos) de los MCPs que uses, actualiza este doc con los ejemplos finales.
