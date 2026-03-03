"""
Auditoría sistemática del contenido RAG.

- Resume los chunks por tema (topic): cuántos hay, cuántos con datos numéricos, de cuántas URLs.
- Compara los topics del RAG con los topics del golden dataset.
- Si existe data/golden_dataset/eval_results.jsonl, cruza también con los últimos resultados
  de eval_golden (por topic: cuántas preguntas, cuántas con respuesta, cuántos errores).

Uso (desde la raíz del proyecto vmc-bot):
  python scripts/audit_rag_content.py
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CHUNKS_PATH = ROOT / "data" / "processed" / "chunks.json"
GOLDEN_PATH = ROOT / "data" / "golden_dataset" / "faqs_golden.json"
EVAL_RESULTS_PATH = ROOT / "data" / "golden_dataset" / "eval_results.jsonl"
OUTPUT_PATH = ROOT / "data" / "processed" / "rag_audit_summary.json"


def load_chunks():
    if not CHUNKS_PATH.exists():
        print(f"No existe {CHUNKS_PATH}. Ejecuta antes el pipeline de ingest (chunks).")
        sys.exit(1)
    with open(CHUNKS_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("chunks", [])


def load_golden_topics():
    topics = set()
    if not GOLDEN_PATH.exists():
        return topics
    with open(GOLDEN_PATH, encoding="utf-8") as f:
        data = json.load(f)
    for ent in data.get("entries", []):
        t = (ent.get("topic") or "").strip()
        if t:
            topics.add(t)
    return topics


def load_eval_by_topic():
    """
    Lee eval_results.jsonl (si existe) y resume por topic:
    - total
    - con respuesta
    - errores
    - intents por tipo
    """
    if not EVAL_RESULTS_PATH.exists():
        return {}
    stats = {}
    with open(EVAL_RESULTS_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            topic = (rec.get("topic") or "").strip() or "Unknown"
            intent = rec.get("intent") or ""
            has_answer = bool(rec.get("has_answer"))
            error = rec.get("error")
            st = stats.setdefault(
                topic,
                {
                    "total": 0,
                    "with_answer": 0,
                    "errors": 0,
                    "intents": defaultdict(int),
                },
            )
            st["total"] += 1
            if has_answer:
                st["with_answer"] += 1
            if error:
                st["errors"] += 1
            st["intents"][intent] += 1
    # Convert defaultdicts to dicts
    for t, st in stats.items():
        st["intents"] = dict(st["intents"])
    return stats


def main():
    chunks = load_chunks()
    golden_topics = load_golden_topics()
    eval_by_topic = load_eval_by_topic()

    topics_stats = {}
    for c in chunks:
        topic = (c.get("topic") or "").strip() or "Unknown"
        url = (c.get("source_url") or "").strip()
        has_numeric = bool(c.get("has_numeric_data"))
        st = topics_stats.setdefault(
            topic,
            {
                "chunks": 0,
                "numeric_chunks": 0,
                "source_urls": set(),
            },
        )
        st["chunks"] += 1
        if has_numeric:
            st["numeric_chunks"] += 1
        if url:
            st["source_urls"].add(url)

    # Convert sets to sorted lists for JSON
    for topic, st in topics_stats.items():
        st["source_urls"] = sorted(st["source_urls"])

    # Detect topics del golden sin chunks
    missing_topics = sorted(t for t in golden_topics if t not in topics_stats)

    # Adjuntar info de eval (si existe)
    for topic, st in topics_stats.items():
        eval_st = eval_by_topic.get(topic)
        if not eval_st:
            continue
        total = eval_st.get("total", 0)
        with_answer = eval_st.get("with_answer", 0)
        errors = eval_st.get("errors", 0)
        intents = eval_st.get("intents", {})
        st["eval"] = {
            "total_questions": total,
            "with_answer": with_answer,
            "errors": errors,
            "answer_rate": round(100 * with_answer / total, 1) if total else 0.0,
            "intents": intents,
        }

    summary = {
        "topics": topics_stats,
        "golden_topics": sorted(golden_topics),
        "missing_topics_in_chunks": missing_topics,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    # Imprimir resumen corto en consola
    print("=== Auditoría RAG por topic ===")
    print(f"Topics en chunks: {len(topics_stats)}")
    if golden_topics:
        print(f"Topics en golden: {len(golden_topics)}")
    if missing_topics:
        print("\nTopics del golden SIN chunks asociados:")
        for t in missing_topics:
            print(f"  - {t}")

    print("\nResumen por topic (top 10 por cantidad de chunks):")
    for topic, st in sorted(topics_stats.items(), key=lambda kv: -kv[1]["chunks"])[:10]:
        eval_info = st.get("eval") or {}
        rate = eval_info.get("answer_rate")
        rate_str = f" | answer_rate={rate}%" if rate is not None else ""
        print(
            f"- {topic}: chunks={st['chunks']}, numeric={st['numeric_chunks']}, urls={len(st['source_urls'])}{rate_str}"
        )

    print(f"\nResumen detallado guardado en: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()

