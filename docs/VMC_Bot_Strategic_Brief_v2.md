# VMC-Bot: The Demand Intelligence Layer

## Strategic Brief v2.0

- **Organization:** VMC Subastas
- **Version:** 2.0 — Revised Strategic Framework
- **Date:** February 2026
- **Author:** SubasPM
- **Classification:** Confidential
- **Timeline:** Phase 1: 6 weeks | Phase 2: 8 weeks | Phase 3: Ongoing

---

# 1. The Strategic Thesis

**This is not a chatbot project.** It is the construction of a **demand intelligence system** with a conversational interface.

## Core Insight

Auctions generate anxiety. Buyers operate in high-speed environments with limited clarity.  
The fundamental problem is **not access** — it is **trust and comprehension in real time**.

VMC-Bot becomes the **intelligence layer** between chaotic auction inventory and buyers who need certainty.

### The System Solves Three Problems

| Problem | Solution |
|--------|----------|
| **Access** | WhatsApp-native experience eliminates friction. |
| **Comprehension** | Explains auction mechanics (SubasCoins, Riesgo Usuario, comisiones) in conversational Peruvian Spanish. |
| **Timing** | Surfaces inventory changes when they matter to each specific buyer. |

---

# 2. The Three-Phase Evolution

## Phase 1 — Build Trust (Weeks 1–6)

Deploy WhatsApp support + inventory bot.

### Weekly Roadmap

| Week | Focus | Deliverable | Milestone |
|------|--------|-------------|-----------|
| 1 | Discovery + Vector Store | Knowledge base + system prompt | Architecture |
| 2 | MVP RAG | FAQs via WhatsApp | Alpha |
| 3 | Stock + Router | Real inventory lookup | Middleware |
| 4 | Audio | Multimodal bot | Pilot 10% |
| 5 | Pilot + Handoff | Escalation to human | Public Pilot |
| 6 | Proactive Alerts | Notifications + dashboard | Full Deployment |

### Phase 1 KPIs

- Ticket deflection: **40%**
- Lead → Bid: **+15%**
- Support NPS: **> 4.5/5**
- Hallucination rate: **< 2%**
- Price errors: **Zero**
- Latency: **< 3s**

---

## Phase 2 — Monetize Attention (Weeks 7–14)

**Live auction co-pilot** via WhatsApp.

### Live Event Feed Experience

Examples:

- 🚗 La RAV4 2019 acaba de entrar. Precio base S/. 42,000.
- ⚠️ Tu Hilux fue adjudicada. Otra entra en 15 min.
- ⏰ La subasta empieza en 5 min.

### Technical Requirements

- Real-time WebSocket/SSE feed
- Sub-second processing
- Smart throttling (5–7 msgs per event)
- Personalized event summarization

---

## Phase 3 — Flip the Model (Ongoing)

**Turn conversation data into demand intelligence.**

### Demand Signals

| Signal | Source | Decision |
|--------|--------|----------|
| Vehicle demand map | Preferences | Consignment |
| Price sensitivity | Bid history | Reserve pricing |
| Geographic demand | User location | Inspection hubs |
| Content gaps | Unanswered questions | SEO strategy |
| Feature requests | Conversation clusters | Roadmap |
| Churn indicators | Drop-off patterns | Retention |

---

# 3. SEO Synergy Loop

The bot becomes an **SEO feedback engine**.

| Bot Component | SEO Connection |
|---------------|----------------|
| Firecrawl scrape | SEO monitoring |
| Vehicle JSON | JSON-LD rich results |
| Help Center scrape | FAQ schema |
| Conversation logs | Keyword research |

**Unanswered bot queries → New pages → Better rankings → More demand signals.**

---

# 4. Unit Economics

**Assumption:** 60 chats/day (~1,800/month, 10,800 messages)

| Component | Monthly Cost |
|-----------|---------------|
| LLM | $35–$61 |
| Cursor | $20 |
| Firecrawl | $16 |
| Pinecone | $0 |
| ElevenLabs | $5 |
| Hosting | $5–$7 |
| WhatsApp | $0–$54 |

**TOTAL:** $81–$168/month  
**Cost per chat:** $0.04–$0.09  

**At scale (200 chats/day):** < $0.03 per chat.

---

# 5. Risks & Mitigations

| Risk | Mitigation |
|------|-------------|
| Meta AI policy | Domain-scoped bot |
| Inventory staleness | Timestamp + 2x scraping |
| Financial hallucinations | Data only from RAG/JSON |
| Firecrawl failures | Validation layer |
| Audio cost spikes | Monitor pilot |
| Traffic spikes | Auto-scaling + rate limits |
| Intercom complexity | Structured handoff protocol |

---

# 6. Prerequisites from VMC

| # | Item | Priority |
|---|------|----------|
| 1 | WhatsApp Business access | **CRITICAL** |
| 2 | Intercom ticket history | **CRITICAL** |
| 3 | Tone + prohibited topics | **CRITICAL** |
| 4 | Customer scripts | HIGH |
| 5 | Fee schedule | HIGH |
| 6 | Vehicle status catalog | HIGH |
| 7 | Inventory URL confirmed | HIGH |
| 8 | WebSocket/SSE access | PHASE 2 |
| 9 | Meta template approval | MEDIUM |

---

# 7. Success Metrics by Phase

| Metric | Phase 1 | Phase 2 | Phase 3 |
|--------|---------|---------|---------|
| Ticket deflection | 40% | 55% | 70% |
| Lead → Bid | +15% | +30% | +40% |
| Support NPS | >4.5 | >4.7 | >4.8 |
| Response time | <3s | <2s | <2s |
| SEO score | 8→45 | 45→70 | 70→85+ |
| Cost per conversation | $0.08 | $0.06 | <$0.04 |

---

# Bottom Line

- **Phase 1:** 6 weeks | $135–$168/month
- **Phase 2:** 8 weeks | Engineering required
- **Phase 3:** Ongoing | Data compounds

**The bot is not the product.**  
**The bot is the interface to a demand intelligence system.**
