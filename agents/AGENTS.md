# VMC-Bot — Mapa de Agentes y Skills

`vmc-bot/agents/` | Actualizado: Marzo 2026

Este documento es la fuente de verdad de todos los agentes, subagentes y skills del proyecto. Antes de crear un script nuevo, revisar si ya existe un agente que lo cubra.

---

## Agente Principal

**Rol:** Orquestador central. Recibe mensajes del usuario, clasifica la intención, ejecuta el pipeline RAG o stock_search, y devuelve una respuesta.

| Dato | Valor |
|------|-------|
| Entry point | `src/server/app.py → POST /api/ask` |
| LLM respuestas | Claude Sonnet 4.5 |
| LLM router | Claude Haiku 4.5 |
| Vector DB | Pinecone (índice `vmc-bot-rag`) |
| Canal actual | Web de prueba (`static/index.html`) |
| Canal objetivo | WhatsApp Business API |

**Flujo:**
```
Mensaje usuario
  → Haiku clasifica intención (faq | stock_search | soporte_humano | fuera_dominio)
  → Si faq:
      → Haiku genera 3 variaciones (multi-query)
      → Búsqueda en Pinecone con RRF
      → Claude Sonnet genera respuesta con contexto RAG
  → Si stock_search: → Playwright scraper (Semana 3)
  → Si soporte_humano: → Mensaje de escalamiento
  → Si fuera_dominio: → Rechazo amable
```

**Infraestructura de soporte:**
- Logging: `src/core/logger.py`
- Reintentos Anthropic: `src/core/resilience.py`
- Scraping seguro: `src/core/firecrawl_client.py`

---

## Subagentes

### 1. Monitor de Costos
**Archivo:** `agents/cost_monitor/monitor_costs.py`
**Rol:** Calcula el costo real del período leyendo `logs/cost_tracker.jsonl`. Alerta si se supera el 70% o 90% del presupuesto mensual ($168).

**Cuándo usarlo:**
- Después de sesiones de prueba intensivas
- Una vez por semana en operación normal
- Antes de escalar a más usuarios

**Cómo invocarlo:**
```bash
# Últimos 30 días (default)
python agents/cost_monitor/monitor_costs.py

# Últimos 7 días
python agents/cost_monitor/monitor_costs.py --dias 7

# Mes específico
python agents/cost_monitor/monitor_costs.py --mes 2026-03
```

**Output:** Reporte en consola + archivo `logs/cost_report_YYYYMMDD_HHMM.txt`

---

### 2. Evaluador de Calidad RAG
**Archivo:** `agents/rag_evaluator/run_evaluation.py` ⚠️ Pendiente de crear
**Rol:** Corre el golden dataset contra el pipeline RAG y evalúa calidad de respuestas en 5 criterios: accuracy, no alucinación, intent routing, relevancia, y guardrails.

**Cuándo usarlo:**
- Después de ingestar contenido nuevo en Pinecone
- Después de modificar el system prompt
- Antes de cualquier deploy o piloto

**Cómo invocarlo:**
```bash
python agents/rag_evaluator/run_evaluation.py
```

**Output:** Reporte en consola + archivo `logs/eval_report_YYYYMMDD.json`

**Umbrales:**
- Score ≥ 4.0/5 → listo para piloto
- Score 3.0–3.9 → necesita mejoras
- Score < 3.0 → no deployar
- Cualquier alucinación financiera → bloqueante

---

### 3. Auditor de Contenido
**Archivo:** `agents/content_auditor/audit_rag_content.py` ⚠️ Pendiente de crear
**Rol:** Detecta gaps en el knowledge base: qué temas faltan en Pinecone, qué preguntas no tienen cobertura, qué infografías del Centro de Ayuda aún no se han extraído.

**Cuándo usarlo:**
- Después de cada ingest de contenido nuevo
- Cuando el evaluador RAG muestra muchas preguntas sin cobertura
- Antes de un piloto público

**Cómo invocarlo:**
```bash
python agents/content_auditor/audit_rag_content.py
```

**Output:** Reporte en `docs/auditoria_contenido_YYYYMMDD.md`

---

### 4. Scraper de Inventario
**Archivo:** `agents/inventory_scraper/scrape_inventory.py` ⚠️ Pendiente de crear (Semana 3)
**Rol:** Scrapea el catálogo de vehículos de vmcsubastas.com con Playwright (sin créditos, sin costo). Genera `data/raw/inventory.json` con estructura validada.

**Cuándo usarlo:**
- Diario (cron job automático)
- 2x/día en días de subasta
- Bajo demanda cuando se necesita inventario actualizado

**Cómo invocarlo:**
```bash
python agents/inventory_scraper/scrape_inventory.py
```

**Output:** `data/raw/inventory.json` con timestamp de scraping

---

### 5. Refinador de Prompts
**Archivo:** `agents/prompt_refiner/refine_prompt.py` ⚠️ Pendiente de crear
**Rol:** Analiza preguntas que el bot respondió mal (desde los logs) y propone cambios al system prompt con justificación. **Nunca aplica cambios automáticamente — requiere aprobación humana.**

**Cuándo usarlo:**
- Cuando el evaluador RAG detecta fallos recurrentes en una categoría
- Después de revisar conversaciones reales del piloto

**Cómo invocarlo:**
```bash
python agents/prompt_refiner/refine_prompt.py
```

**Output:** Sugerencias en consola. Cambios en `prompts/` solo con aprobación manual.

---

## Skills Disponibles

| Skill | Script | Estado | Descripción |
|-------|--------|--------|-------------|
| monitor_costos | `agents/cost_monitor/monitor_costs.py` | ✅ Listo | Reporte de costos real |
| evaluar_golden | `agents/rag_evaluator/run_evaluation.py` | ⚠️ Pendiente | Evaluación de calidad RAG |
| auditar_contenido | `agents/content_auditor/audit_rag_content.py` | ⚠️ Pendiente | Gaps en knowledge base |
| scrapear_inventario | `agents/inventory_scraper/scrape_inventory.py` | ⚠️ Pendiente | Catálogo de vehículos |
| refinar_prompt | `agents/prompt_refiner/refine_prompt.py` | ⚠️ Pendiente | Mejoras al system prompt |

---

## Infraestructura Base (`src/core/`)

Estos no son agentes sino módulos de soporte que todos los agentes y el bot principal deben usar:

| Módulo | Propósito |
|--------|-----------|
| `src/core/logger.py` | Logging unificado + fix UTF-8 Windows |
| `src/core/resilience.py` | Reintentos automáticos para errores 429 de Anthropic |
| `src/core/firecrawl_client.py` | Cliente seguro para Firecrawl con fallbacks |

---

## Cuándo activar cada agente

| Acción que realizas | Agente a activar después |
|--------------------|--------------------------|
| Ingestas contenido nuevo en Pinecone | Evaluador RAG + Auditor de Contenido |
| Modificas el system prompt | Evaluador RAG |
| Terminas una sesión de pruebas | Monitor de Costos |
| Antes de un piloto público | Evaluador RAG + Auditor de Contenido + Monitor de Costos |
| Ves respuestas malas en conversaciones reales | Refinador de Prompts |
| Necesitas inventario actualizado | Scraper de Inventario |