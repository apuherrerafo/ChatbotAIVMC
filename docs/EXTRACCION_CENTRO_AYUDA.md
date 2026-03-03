# Estrategia de extracción — Centro de Ayuda VMC

**Problema:** En ayuda.vmcsubastas.com ~95% del contenido útil está en **infografías e imágenes**, no en texto HTML.

---

## Objetivo

Obtener texto estructurado por tema (registro, SubasCoins, comisiones, consignaciones, etc.) para chunkear, embeber y usar en RAG, respetando el guardrail de no inventar números (precios, comisiones, plazos).

---

## Enfoque multicapa (recomendado)

Combinar varias fuentes para maximizar cobertura y calidad.

### Capa 1 — Firecrawl (HTML + metadatos)

- **Acción:** Scrapear todas las URLs del Centro de Ayuda con Firecrawl (por MCP o SDK).
- **Obtienes:** Texto HTML existente, títulos, estructura de secciones, **URLs de imágenes**.
- **Uso:** Estructura de temas, enlaces a imágenes que luego se procesan en Capa 2.

### Capa 2 — Extracción de texto desde imágenes

Opciones (de mayor a menor prioridad sugerida):

| Opción | Pros | Contras |
|--------|------|--------|
| **A) Modelo multimodal (ej. GPT-4V / Claude con imagen)** | Buen contexto, entiende tablas e infografías | Coste por imagen, hay que descargar/adjuntar cada imagen |
| **B) OCR (Tesseract / Google Vision)** | Barato, escalable | Peor en diseños complejos e infografías |
| **C) Google Cache / versiones antiguas** | Si antes el contenido era texto, puede haber versión cacheada en texto | No siempre existe; puede estar desactualizado |

**Recomendación:** Empezar con **A** para un subconjunto de artículos clave (ej. comisiones, SubasCoins, registro) y comparar calidad con **B**. Si el presupuesto aprieta, usar **B** para el resto y **A** solo para las páginas más críticas.

### Capa 3 — Fuentes alternativas de verdad

- **FAQ antigua:** Si existe documento o export de FAQ en texto, usarlo como base y cruzar con lo extraído.
- **Términos y Condiciones / documentos legales:** Suelen estar en texto; extraer y chunkear por sección para preguntas sobre reglas, plazos, obligaciones.
- **Datos estructurados:** Cualquier JSON/CSV oficial con precios, comisiones o plazos debe ser la **única** fuente de números; el RAG solo recupera y el LLM redacta, no calcula.

---

## Flujo propuesto (Semana 1)

1. **Inventario:** Listar todas las URLs del Centro de Ayuda (sitemap o crawl con Firecrawl).
2. **Clasificar:** Marcar por tipo: “solo texto”, “texto + imágenes”, “solo imágenes/infografías”.
3. **Extracción texto:** Para “solo texto” → Firecrawl. Para “imágenes” → descargar imágenes, pasar por modelo multimodal o OCR, guardar resultado en texto por artículo.
4. **Normalización:** Unificar formato (ej. Markdown por artículo), etiquetar tema/sección (registro, SubasCoins, comisiones, etc.).
5. **Chunking:** Chunkear por **tema/pregunta** (semántico), no por tamaño fijo.
6. **Embeddings + Pinecone:** Generar embeddings (Pinecone Inference, multilingual-e5-large) y cargar en Pinecone con metadata (tema, fuente, tipo).

---

## Guardrails de contenido

- Los **números** (precios, %, plazos) que se usen en respuestas deben provenir **solo** de:
  - texto extraído de documentos oficiales (T&C, FAQ), o
  - datos scrapeados/JSON del sitio,
  - **nunca** generados por el LLM.
- Marcar en metadata qué chunks contienen “datos numéricos sensibles” para que el sistema de respuesta priorice citarlos y no inventar.

---

## Próximos pasos concretos

1. Configurar Firecrawl MCP y hacer un crawl de ayuda.vmcsubastas.com para obtener lista de URLs y contenido HTML disponible.
2. Descargar y revisar 3–5 imágenes tipo infografía; probar extracción con un modelo multimodal (Claude/GPT-4V) y con OCR; decidir estrategia por tipo de página.
3. Definir taxonomía de temas (registro, SubasCoins, comisiones, consignaciones, Ganador Directo, etc.) y aplicar en el chunking.
4. Implementar pipeline de ingest (script o notebook) que ejecute Capas 1 y 2 y escriba en `data/raw/` y `data/processed/` antes de embeber.
