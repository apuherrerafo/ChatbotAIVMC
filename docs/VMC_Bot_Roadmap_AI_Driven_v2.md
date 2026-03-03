# VMC-Bot --- Roadmap AI-Driven | Confidencial

## ROADMAP DEFINITIVO

### VMC-Bot: Chatbot IA para VMC Subastas

- **Enfoque:** 100% AI-Driven | Sin programadores | Quick Wins
- **Canal:** WhatsApp Business API
- **Herramienta de desarrollo:** Cursor + MCPs
- **Versión:** AI-Driven (Febrero 2026)

---

# 1. Resumen Ejecutivo

Este documento detalla la ruta completa para construir el chatbot de VMC Subastas bajo un enfoque 100% AI-driven.

## KPIs

- Deflexión de tickets: **40%** reducción (Alucinación **< 2%**)
- Conversión Lead → Puja: **+15%** (Latencia **< 3s**)
- NPS Soporte: **> 4.5/5** (Errores de precio **= 0**)

---

# 2. Stack Tecnológico

## Desarrollo

- Cursor Pro — $20/mes
- MCPs — Incluido

## IA

- Claude Sonnet 4.5 (LLM principal)
- Claude Haiku 4.5 (Router)
- Pinecone (Embeddings + Vector DB)

## Datos

- Firecrawl (Scraping Centro de Ayuda + Inventario)

## Audio

- Gemini 2.5 Flash (STT)
- ElevenLabs (TTS)

## Canal

- WhatsApp Business API (Meta Cloud o Twilio)

---

# 3. Costos Estimados

**Escenario:** 60 chats/día (~10,800 mensajes/mes)

- LLM: $35–$61/mes (con caching + router)
- Cursor: $20
- Firecrawl: $16
- Pinecone: $0
- ElevenLabs: $5
- Hosting: $5–$7
- WhatsApp (Twilio opcional): ~$54

**TOTAL ESTIMADO:** $135–$168/mes  
**Alternativa optimizada (Meta directo):** $81–$109/mes  

**Costo por conversación:** ~$0.08

---

# 4. Fases de Desarrollo (6 semanas)

| Semana | Fase |
|--------|------|
| **1** | Discovery + Vector Store |
| **2** | MVP RAG en WhatsApp |
| **3** | Stock + Router |
| **4** | Audio |
| **5** | Pilot + Handoff |
| **6** | Proactivo + Escalar |

---

# 5. Desafíos Clave

- Política Meta 2026 (solo bots con propósito definido)
- Stock dinámico (scraping 2x/día)
- Evitar alucinaciones financieras (datos solo desde RAG/JSON)
- Español peruano contextualizado
- Picos en subastas (hosting escalable)

---

# 6. Inversión y Timing

- **Inversión mensual estimada:** $135–$168
- **Costo por conversación:** ~$0.08
- **Tiempo de implementación:** 6 semanas
