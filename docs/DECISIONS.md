# Decisiones técnicas — VMC-Bot

Registro de decisiones de arquitectura y diseño. Actualizar al tomar nuevas decisiones.

**Fuente de verdad:**
- **Fases 1–6, stack, costos:** `docs/VMC_Bot_Roadmap_AI_Driven_v2.md`
- **Visión a largo plazo (3 fases, demanda, SEO, prerequisitos):** `docs/VMC_Bot_Strategic_Brief_v2.md`

---

## 2025-02-24 — Estructura inicial del proyecto

- **Decisión:** Estructura de carpetas modular por dominio (ingest, rag, server, prompts, docs).
- **Motivo:** Permitir iterar cada componente por separado y mantener responsabilidades claras.
- **Alternativas consideradas:** Monolito en un solo `src/` — descartado para facilitar pruebas y futura escalabilidad.

---

## 2025-02-24 — Estrategia de extracción del Centro de Ayuda

- **Problema:** ~95% del contenido de ayuda.vmcsubastas.com está en imágenes/infografías.
- **Decisión:** Enfoque multicapa (ver `docs/EXTRACCION_CENTRO_AYUDA.md`).
- **Opciones evaluadas:** Solo scraping HTML (insuficiente), solo OCR (coste/calidad), enfoque híbrido (elegido).

---

## 2026-02-24 — WhatsApp Business diferido

- **Problema:** El chip para WhatsApp Business está en un teléfono eSIM; no se puede registrar aún.
- **Decisión:** Diferir setup de WhatsApp Business API. No bloquea Semana 1 (Discovery + Vector Store). Se necesita para Semana 2 (MVP RAG en WhatsApp).
- **Plan:** Resolver durante la semana cuando el chip esté disponible.

---

*(Añadir nuevas entradas con fecha, decisión, motivo y alternativas.)*
