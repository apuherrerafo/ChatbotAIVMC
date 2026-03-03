"""
Evalúa el RAG contra el golden dataset (50 preguntas).
Llama a ask_with_router por cada entrada, registra intent, latencia, chunks y longitud de respuesta.
Escribe resultados en data/golden_dataset/eval_results.jsonl y un resumen en consola.

Uso (desde la raíz del proyecto vmc-bot):
  python scripts/eval_golden.py
  python scripts/eval_golden.py --limit 10   # solo las primeras 10
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

from src.core.budget_guard import check_daily_budget, BudgetExceededError

GOLDEN_PATH = ROOT / "data" / "golden_dataset" / "faqs_golden.json"
RESULTS_PATH = ROOT / "data" / "golden_dataset" / "eval_results.jsonl"


def main():
    parser = argparse.ArgumentParser(description="Evaluar RAG con golden dataset")
    parser.add_argument("--limit", type=int, default=0, help="Máximo de entradas a evaluar (0 = todas)")
    parser.add_argument("--skip-router", action="store_true", help="Ir directo a RAG (skip router)")
    args = parser.parse_args()

    # Guard de presupuesto diario específico para scripts de evaluación.
    try:
        check_daily_budget(limit_usd=2.0)
    except BudgetExceededError as e:
        print(f"[BUDGET] {e}")
        sys.exit(1)

    if not GOLDEN_PATH.exists():
        print(f"No existe {GOLDEN_PATH}")
        sys.exit(1)

    with open(GOLDEN_PATH, encoding="utf-8") as f:
        data = json.load(f)
    entries = data.get("entries", [])
    if args.limit:
        entries = entries[: args.limit]
    total = len(entries)

    print(f"Evaluando {total} preguntas del golden dataset...")
    print("(Usando ask_with_router desde Python, no el servidor)\n")

    from src.rag.query_rag import ask_with_router, ask_rag

    results = []
    intents = {}
    latencies = []
    with_answer = 0
    errors = 0

    for i, ent in enumerate(entries, 1):
        eid = ent.get("id", "")
        question = ent.get("pregunta", "").strip()
        topic = ent.get("topic", "")
        if not question:
            continue
        t0 = time.perf_counter()
        try:
            if args.skip_router:
                chunks, answer = ask_rag(question)
                intent = "faq"
            else:
                chunks, answer, intent = ask_with_router(question)
        except Exception as e:
            answer = ""
            chunks = []
            intent = "error"
            errors += 1
        t1 = time.perf_counter()
        latency_ms = round((t1 - t0) * 1000, 1)
        latencies.append(latency_ms)
        if (answer or "").strip():
            with_answer += 1
        intents[intent] = intents.get(intent, 0) + 1

        rec = {
            "id": eid,
            "topic": topic,
            "pregunta": question[:80] + ("…" if len(question) > 80 else ""),
            "intent": intent,
            "latency_ms": latency_ms,
            "chunks_count": len(chunks or []),
            "answer_len": len(answer or ""),
            "has_answer": bool((answer or "").strip()),
            "error": str(e) if intent == "error" else None,
        }
        results.append(rec)
        print(f"  [{i}/{total}] {eid} -> {intent} ({latency_ms} ms) chunks={len(chunks or [])} answer_len={rec['answer_len']}")

    # Resumen
    avg_latency = round(sum(latencies) / len(latencies), 1) if latencies else 0
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    print(f"  Total evaluadas:    {total}")
    print(f"  Con respuesta:      {with_answer} ({100 * with_answer / total:.0f}%)")
    print(f"  Errores:            {errors}")
    print(f"  Latencia promedio:  {avg_latency} ms")
    print(f"  Intent:")
    for k, v in sorted(intents.items(), key=lambda x: -x[1]):
        print(f"    {k}: {v}")
    print(f"\n  Resultados guardados en: {RESULTS_PATH}")


if __name__ == "__main__":
    main()
