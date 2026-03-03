# Semana 1 — Discovery + Vector Store

**Objetivo:** Construir la base de conocimiento del bot (RAG-ready) y tener el primer pipeline funcional de pregunta → respuesta con datos reales.

**Fecha inicio:** Jueves 26 feb 2026  
**Milestone:** Architecture (knowledge base + system prompt + Pinecone con datos)

> **WhatsApp Business API:** BLOQUEADO (tema eSIM). Se resuelve cuando el chip esté listo. No bloquea nada de Semana 1; se necesita para Semana 2 (MVP RAG en WhatsApp).

### Horario de referencia

- Jornada laboral hasta las 18:00
- Día 1 (jue 26 feb): arranca 14:30 → **3.5 horas**
- Días siguientes: jornada completa (confirmar horarios)

---

## Día 1 — Jueves 26 feb (14:30–18:00, ~3.5h): Setup + Primer Crawl

### Objetivo: Tener MCPs funcionando y el mapa del Centro de Ayuda.

**Bloque 1 (14:30–15:30) — Setup MCPs:**

1. **Configurar Firecrawl MCP en Cursor**
   - Crear cuenta en firecrawl.dev, obtener API key
   - Configurar en `mcp.json` de Cursor
   - Test: scrapear una URL simple para verificar que funciona

2. **Configurar Pinecone**
   - Crear cuenta en pinecone.io (plan Starter, gratis)
   - Crear índice `vmc-bot-rag` (dimensión según multilingual-e5-large)
   - Guardar API key + host en `.env`

**Bloque 2 (15:30–17:00) — Primer crawl:**

3. **Crawl de ayuda.vmcsubastas.com**
   - Crawl con Firecrawl → obtener lista de todas las URLs
   - Guardar resultado en `data/raw/helpcenter_crawl.json`
   - Clasificar cada URL: "tiene texto", "solo imágenes", "mixto"

**Bloque 3 (17:00–18:00) — Exploración:**

4. **Explorar fuentes alternativas**
   - Revisar vmcsubastas.com por T&C, FAQ antigua, páginas con texto
   - Buscar si hay sitemap.xml o robots.txt que nos dé más URLs
   - Guardar hallazgos en `data/raw/fuentes_alternativas.md`

**Entregable:** MCPs configurados + mapa de URLs del Centro de Ayuda clasificadas por tipo de contenido.

---

## Día 2 — Viernes 27 feb: Extracción de contenido

### Objetivo: Tener texto extraído de las páginas más importantes (incluidas las que son imágenes).

**Tareas:**

1. **Páginas con texto** → extraer con Firecrawl, guardar markdown por artículo en `data/raw/text/`

2. **Páginas con imágenes/infografías** (el grueso del contenido):
   - Descargar las imágenes de las 5–10 páginas más críticas (comisiones, SubasCoins, registro, Ganador Directo, consignaciones)
   - Probar extracción con Claude (vision) — pasar imagen y pedir texto estructurado
   - Si los resultados son buenos → definir eso como pipeline principal
   - Guardar texto extraído en `data/raw/images_extracted/`

3. **T&C y documentos legales** — extraer y guardar en `data/raw/legal/`

4. **Definir taxonomía de temas:**
   - Registro / Cuenta
   - SubasCoins
   - Comisiones (por tramo de precio)
   - Consignaciones
   - Ganador Directo
   - Riesgo Usuario / Calidad de Miembro
   - Proceso de subasta
   - Pagos y plazos
   - Retiro de vehículo
   - Soporte / Contacto
   - *(añadir según lo que salga del crawl)*

**Entregable:** Contenido en texto/markdown de las páginas clave, taxonomía de temas definida.

---

## Día 3 — Lunes 2 mar: Limpieza + Chunking semántico

### Objetivo: Contenido limpio, chunkeado por tema, listo para embeber.

**Tareas:**

1. **Normalizar** todo el contenido extraído (Día 2) a Markdown unificado:
   - Un archivo por artículo/tema en `data/processed/`
   - Metadata en el header: tema, fuente (URL o imagen), tiene_datos_numericos (sí/no)

2. **Chunking semántico:**
   - Dividir por pregunta/tema, NO por tamaño fijo
   - Cada chunk = una unidad de respuesta (ej. "¿Qué son los SubasCoins?", "¿Cómo funcionan las comisiones?")
   - Chunks con datos numéricos marcados con metadata especial (guardrail financiero)
   - Guardar chunks en `data/processed/chunks.json` (o jsonl) con metadata

3. **Revisión manual** de los chunks más importantes (comisiones, precios, plazos):
   - Verificar que los números coinciden con la fuente
   - Si hay dudas → marcar para validar con VMC

**Entregable:** `data/processed/chunks.json` con chunks semánticos etiquetados y listos para embeddings.

---

## Día 4 — Martes 3 mar: Embeddings + Pinecone + System Prompt v1

### Objetivo: Datos en Pinecone y system prompt redactado.

**Tareas:**

1. **Generar embeddings:**
   - Usar Pinecone Inference (multilingual-e5-large) o el modelo de embedding que mejor funcione con español
   - Script en `src/rag/embed.py` que lea chunks.json, genere embeddings, haga upsert a Pinecone
   - Incluir metadata por vector: tema, fuente, tiene_datos_numericos

2. **Verificar en Pinecone:**
   - Query de prueba desde el dashboard o por SDK
   - Probar 3–5 preguntas y ver si devuelve los chunks correctos

3. **System prompt v1** (`prompts/system_prompt_v1.md`):
   - Persona: asistente de VMC Subastas, cercano, claro, en español peruano
   - Glosario de términos del negocio (SubasCoins, Ganador Directo, Riesgo Usuario, etc.)
   - Guardrails: solo dominio VMC, nunca inventar números, escalar si no sabe
   - Tono: "carro" no "vehículo", "jalar" no "retirar"
   - Restricción Meta 2026: propósito definido

**Entregable:** Pinecone con embeddings cargados + system prompt v1 redactado.

---

## Día 5 — Miércoles 4 mar: Golden Dataset + Primer test RAG

### Objetivo: Tener la línea base de evaluación y validar que el RAG funciona.

**Tareas:**

1. **Golden dataset** (`data/golden_dataset/golden_50.json`):
   - 50 preguntas con respuesta esperada, categorizadas por tema
   - Incluir preguntas fáciles (FAQ directas), medias (contexto multi-chunk), difíciles (números, comisiones, plazos)
   - Incluir preguntas fuera de dominio (para validar guardrail)
   - Incluir preguntas en español peruano coloquial

2. **Primer test RAG end-to-end:**
   - Script simple: pregunta → embedding → query Pinecone → top-K chunks → Claude con system prompt → respuesta
   - Probar con 10 preguntas del golden dataset
   - Evaluar: ¿responde correctamente? ¿usa los chunks del RAG? ¿inventa números?

3. **WhatsApp Business (si el chip está listo):**
   - Registrar número en Meta Business Suite
   - Configurar WhatsApp Business API
   - Si no está listo, no bloquea — esto es para Semana 2

**Entregable:** Golden dataset de 50 preguntas + primer test RAG con resultados.

---

## Resumen visual

```
Día 1 (Jue 26 feb, 14:30–18:00) → Setup MCPs + Crawl Centro de Ayuda
Día 2 (Vie 27 feb)              → Extracción de contenido (texto + imágenes)
Día 3 (Lun 2 mar)               → Limpieza + Chunking semántico
Día 4 (Mar 3 mar)               → Embeddings en Pinecone + System Prompt v1
Día 5 (Mié 4 mar)               → Golden Dataset + Primer test RAG
──────────────────────────────────────────────────────────────────
WhatsApp → cuando el chip esté listo (no bloquea S1)
```

---

## Qué NO hacemos en Semana 1

- WhatsApp webhook (Semana 2)
- Router de intención Haiku (Semana 3)
- Scraping de inventario (Semana 3)
- Audio STT/TTS (Semana 4)
- Handoff a humano (Semana 5)

---

## Riesgos de Semana 1

| Riesgo | Impacto | Mitigación |
|--------|---------|------------|
| Centro de Ayuda es 95% imágenes | Extracción lenta/costosa | Priorizar 10 páginas clave; multimodal para las críticas, OCR para el resto |
| Pinecone Inference no disponible o limitado en free tier | No podemos embeber | Fallback: usar modelo de embeddings local o API alternativa (OpenAI, Cohere) |
| Chunks mal cortados pierden contexto | RAG devuelve basura | Chunking manual/semántico; revisar los 10 más críticos a mano |
| Números incorrectos extraídos de imágenes | Guardrail financiero roto | Revisar manualmente todos los chunks con datos numéricos antes de subir a Pinecone |
