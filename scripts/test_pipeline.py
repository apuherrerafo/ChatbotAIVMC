"""
Test mínimo del pipeline completo de VMC-Bot.
Corre UNA pregunta real con los modelos de producción y muestra el costo exacto.

Uso:
  python scripts/test_pipeline.py
  python scripts/test_pipeline.py "¿Cómo me registro en VMC?"

Costo típico por ejecución:
  - Pregunta corta (≤5 palabras, activa multi-query): ~$0.010–0.016
  - Pregunta larga (>5 palabras, sin multi-query):   ~$0.005–0.009
  - Segunda ejecución en adelante (cache activo):     ~$0.005–0.008
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

# Precios Anthropic API (feb 2026)
SONNET_INPUT_PER_M  = 3.00
SONNET_OUTPUT_PER_M = 15.00
SONNET_CACHE_R_PER_M = 0.30   # cache read (ahorro del prompt caching)
SONNET_CACHE_W_PER_M = 3.75   # cache write (primera vez que se cachea)
HAIKU_INPUT_PER_M   = 0.80
HAIKU_OUTPUT_PER_M  = 4.00
HAIKU_CACHE_R_PER_M = 0.08
HAIKU_CACHE_W_PER_M = 1.00


def tokens_cost(tokens: dict, model: str) -> float:
    inp  = tokens.get("input", 0)
    out  = tokens.get("output", 0)
    cr   = tokens.get("cached_read", 0)
    cw   = tokens.get("cached_creation", 0)
    # Los tokens cacheados no se cobran como input normal
    fresh_inp = max(0, inp - cr - cw)
    if "haiku" in model:
        return (
            fresh_inp * HAIKU_INPUT_PER_M / 1e6 +
            cw        * HAIKU_CACHE_W_PER_M / 1e6 +
            cr        * HAIKU_CACHE_R_PER_M / 1e6 +
            out       * HAIKU_OUTPUT_PER_M / 1e6
        )
    return (
        fresh_inp * SONNET_INPUT_PER_M / 1e6 +
        cw        * SONNET_CACHE_W_PER_M / 1e6 +
        cr        * SONNET_CACHE_R_PER_M / 1e6 +
        out       * SONNET_OUTPUT_PER_M / 1e6
    )


def fmt_tokens(t: dict) -> str:
    parts = [f"in={t.get('input',0)}"]
    if t.get("cached_read"):
        parts.append(f"cache_read={t['cached_read']} ✅")
    if t.get("cached_creation"):
        parts.append(f"cache_write={t['cached_creation']}")
    parts.append(f"out={t.get('output',0)}")
    return "  ".join(parts)


def run_test(question: str):
    print("\n" + "=" * 60)
    print(f"PREGUNTA: {question}")
    print("=" * 60)

    from src.rag.query_rag import ask_with_router_debug

    chunks, answer, intent, debug = ask_with_router_debug(question)

    # --- Resultados ---
    print(f"\n🎯 Intent detectado : {intent}")

    mq = debug.get("multi_queries") or []
    if len(mq) > 1:
        print(f"🔀 Multi-query       : SÍ ({len(mq)} queries)")
    else:
        print(f"🔀 Multi-query       : NO (pregunta larga/específica)")

    print(f"\n💬 Respuesta:\n{answer}")

    # --- Tokens y costo ---
    print("\n" + "-" * 40)
    print("TOKENS Y COSTO")
    print("-" * 40)

    total_cost = 0.0

    # Router (Haiku)
    it = debug.get("intent_tokens") or {}
    router_cost = tokens_cost(it, "haiku")
    total_cost += router_cost
    print(f"Router  (Haiku)  : {fmt_tokens(it)}  → ${router_cost:.6f}")

    # Multi-query (Haiku, si aplica)
    mt = debug.get("multi_query_tokens") or {}
    if mt.get("input") or mt.get("output"):
        mq_cost = tokens_cost(mt, "haiku")
        total_cost += mq_cost
        print(f"Multi-q (Haiku)  : {fmt_tokens(mt)}  → ${mq_cost:.6f}")
    else:
        print(f"Multi-q (Haiku)  : skipped (pregunta >5 palabras)  → $0.000000")

    # Generación (Sonnet)
    gen = debug.get("generation") or {}
    gt = gen.get("tokens") or {}
    if gt.get("input") or gt.get("output"):
        gen_cost = tokens_cost(gt, "sonnet")
        total_cost += gen_cost
        cached = gt.get("cached_read", 0)
        cache_label = f" — {cached} tokens desde cache ✅" if cached else " — sin cache (primera vez)"
        print(f"Sonnet  (gen)    : {fmt_tokens(gt)}{cache_label}  → ${gen_cost:.6f}")
    else:
        print(f"Sonnet  (gen)    : no aplica (intent={intent})")

    # Latencia
    print(f"\n⏱  Latencia total  : {debug.get('total_latency_ms', 0)} ms")

    # Total
    print(f"\n💰 COSTO ESTA LLAMADA : ${total_cost:.6f}  (~${total_cost*100:.4f} centavos)")
    if total_cost > 0:
        print(f"   Equivale a        : {int(1/total_cost) if total_cost > 0 else '∞'} mensajes por $1 USD")

    # Aviso de cache
    if not (gt.get("cached_read") or gt.get("cached_creation")):
        print("\n⚠️  Prompt caching aún no activo en Sonnet.")
        print("   Corre el script una segunda vez para ver el ahorro de cache.")
    else:
        saving_pct = int(gt["cached_read"] / max(gt.get("input", 1), 1) * 100)
        print(f"\n✅ Prompt caching activo — {saving_pct}% de tokens de input servidos desde cache.")

    print("=" * 60 + "\n")


def main():
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
    else:
        # Pregunta por defecto — corta para activar multi-query y ver el pipeline completo
        question = "¿Qué son los SubasCoins?"

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ERROR: Falta ANTHROPIC_API_KEY en .env")
        sys.exit(1)

    run_test(question)


if __name__ == "__main__":
    main()
