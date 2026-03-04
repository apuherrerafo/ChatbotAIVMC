"""
Auditoría de calidad: cruza eval_results.jsonl con faqs_golden.json,
clasifica cada respuesta generada vs esperada (Correcto / Parcial / Incorrecto)
y escribe data/golden_dataset/quality_report.md.

Requisito: eval_results.jsonl debe contener la respuesta generada.
  Generar con: python scripts/eval_golden.py --save-answers

O usar --fetch-answers para obtener respuestas llamando al RAG (sin servidor).
"""
import json
import argparse
import sys
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

GOLDEN_PATH = ROOT / "data" / "golden_dataset" / "faqs_golden.json"
EVAL_RESULTS_PATH = ROOT / "data" / "golden_dataset" / "eval_results.jsonl"
REPORT_PATH = ROOT / "data" / "golden_dataset" / "quality_report.md"

CLASSIFY_SYSTEM = """Eres un evaluador de respuestas de un chatbot de Centro de Ayuda.

Clasifica la respuesta generada frente a la respuesta esperada en UNA de estas tres categorías:
- CORRECTO: la respuesta cubre la información esperada (datos clave presentes, sin errores).
- PARCIAL: responde pero le falta información clave o es vaga/imprecisa.
- INCORRECTO: dato equivocado, contradice la esperada, o no responde la pregunta.

Responde SOLO con una línea en este formato exacto:
CLASIFICACION: <CORRECTO|PARCIAL|INCORRECTO>
RAZON: <una frase breve>"""


def load_golden():
    with open(GOLDEN_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return {e["id"]: e for e in data.get("entries", [])}


def load_eval_results():
    if not EVAL_RESULTS_PATH.exists():
        return {}
    by_id = {}
    with open(EVAL_RESULTS_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            by_id[rec["id"]] = rec
    return by_id


def classify_one(pregunta: str, respuesta_esperada: str, respuesta_generada: str) -> tuple[str, str]:
    """Usa Claude Haiku para clasificar. Retorna (CORRECTO|PARCIAL|INCORRECTO, razon)."""
    try:
        import os
        from dotenv import load_dotenv
        load_dotenv(ROOT / ".env")
        if not os.getenv("ANTHROPIC_API_KEY"):
            return "DESCONOCIDO", "Sin API key"
        import anthropic
        from src.core.resilience import call_claude_with_retry
        client = anthropic.Anthropic()
        prompt = f"""Pregunta: {pregunta}

Respuesta esperada:
{respuesta_esperada}

Respuesta generada por el bot:
{respuesta_generada or '(vacía)'}

Clasifica según las instrucciones."""
        msg = call_claude_with_retry(
            client=client,
            model="claude-haiku-4-5-20251001",
            max_tokens=150,
            system=CLASSIFY_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        text = (msg.content[0].text or "").strip()
        clasif = "PARCIAL"
        razon = ""
        for line in text.split("\n"):
            line = line.strip()
            if line.upper().startswith("CLASIFICACION:"):
                val = line.split(":", 1)[-1].strip().upper()
                if "CORRECTO" in val:
                    clasif = "CORRECTO"
                elif "INCORRECTO" in val:
                    clasif = "INCORRECTO"
                else:
                    clasif = "PARCIAL"
            elif line.upper().startswith("RAZON:"):
                razon = line.split(":", 1)[-1].strip()
        return clasif, razon or text[:200]
    except Exception as e:
        return "DESCONOCIDO", str(e)[:200]


def main():
    parser = argparse.ArgumentParser(description="Auditoría de calidad: golden vs respuestas generadas")
    parser.add_argument("--fetch-answers", action="store_true", help="Obtener respuestas con ask_rag si faltan en eval_results")
    parser.add_argument("--limit", type=int, default=0, help="Evaluar solo las primeras N preguntas (0 = todas)")
    args = parser.parse_args()

    golden = load_golden()
    eval_by_id = load_eval_results()

    # Construir lista (id, pregunta, respuesta_esperada, respuesta_generada)
    entries = []
    for eid, ent in golden.items():
        esperada = ent.get("respuesta_esperada", "")
        pregunta = ent.get("pregunta", "")
        rec = eval_by_id.get(eid) or {}
        respuesta = rec.get("respuesta") if isinstance(rec.get("respuesta"), str) else None
        if respuesta is None and args.fetch_answers:
            try:
                from dotenv import load_dotenv
                load_dotenv(ROOT / ".env")
                from src.rag.query_rag import ask_with_router
                _, answer, _ = ask_with_router(pregunta)
                respuesta = (answer or "").strip()
            except Exception as e:
                respuesta = f"[Error al obtener: {e}]"
        entries.append({
            "id": eid,
            "topic": ent.get("topic", ""),
            "pregunta": pregunta,
            "respuesta_esperada": esperada,
            "respuesta_generada": respuesta or "",
        })

    if args.limit:
        entries = entries[: args.limit]

    # Solo auditar entradas que tengan respuesta generada (o se obtuvo con --fetch-answers)
    con_respuesta = [e for e in entries if (e.get("respuesta_generada") or "").strip()]
    sin_respuesta = [e for e in entries if not (e.get("respuesta_generada") or "").strip()]
    if sin_respuesta and not args.fetch_answers:
        print(f"Aviso: {len(sin_respuesta)} preguntas sin respuesta en eval_results. Ejecuta: python scripts/eval_golden.py --save-answers")

    if not con_respuesta:
        print("No hay entradas con respuesta para auditar.")
        return

    print(f"Auditando {len(con_respuesta)} preguntas (con respuesta). Clasificando con Haiku...")
    classifications = []
    for i, e in enumerate(con_respuesta, 1):
        clasif, razon = classify_one(
            e["pregunta"],
            e["respuesta_esperada"],
            e["respuesta_generada"],
        )
        e["clasificacion"] = clasif
        e["razon"] = razon
        classifications.append(e)
        sym = "✅" if clasif == "CORRECTO" else ("⚠️" if clasif == "PARCIAL" else "❌")
        print(f"  [{i}/{len(con_respuesta)}] {e['id']} {sym} {clasif} — {razon[:50]}...")

    # Resumen y patrones
    by_class = defaultdict(list)
    for e in classifications:
        by_class[e["clasificacion"]].append(e["id"])

    # Patrones de error: razones más frecuentes en PARCIAL e INCORRECTO
    razones_parcial = [e["razon"] for e in classifications if e["clasificacion"] == "PARCIAL"]
    razones_incorrecto = [e["razon"] for e in classifications if e["clasificacion"] == "INCORRECTO"]

    # Escribir reporte Markdown
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Reporte de calidad — Golden Dataset",
        "",
        "Clasificación: respuesta generada vs respuesta esperada.",
        "",
    ]
    if sin_respuesta:
        lines.append(f"*Nota: {len(sin_respuesta)} preguntas sin respuesta en eval_results (no auditadas). Para incluirlas: `python scripts/eval_golden.py --save-answers`*")
        lines.append("")
    lines.extend([
        "## Resumen",
        "",
        f"- **Correcto:** {len(by_class['CORRECTO'])}",
        f"- **Parcial:** {len(by_class['PARCIAL'])}",
        f"- **Incorrecto:** {len(by_class['INCORRECTO'])}",
        f"- **Desconocido:** {len(by_class['DESCONOCIDO'])}",
        "",
        "---",
        "",
        "## Por pregunta",
        "",
    ])
    for e in classifications:
        sym = "✅" if e["clasificacion"] == "CORRECTO" else ("⚠️" if e["clasificacion"] == "PARCIAL" else "❌")
        lines.append(f"### {sym} {e['id']} — {e['clasificacion']} ({e['topic']})")
        lines.append("")
        lines.append(f"**Pregunta:** {e['pregunta']}")
        lines.append("")
        lines.append("**Esperada:** " + (e["respuesta_esperada"][:500] + "…" if len(e["respuesta_esperada"]) > 500 else e["respuesta_esperada"]))
        lines.append("")
        lines.append("**Generada:** " + (e["respuesta_generada"][:500] + "…" if len(e["respuesta_generada"]) > 500 else (e["respuesta_generada"] or "(vacía)")))
        lines.append("")
        lines.append(f"*Razón: {e['razon']}*")
        lines.append("")
        lines.append("---")
        lines.append("")

    lines.extend([
        "",
        "## Patrones de error (revisar manualmente ⚠️ y ❌)",
        "",
    ])
    if razones_parcial:
        lines.append("### Parcial")
        for r in razones_parcial[:15]:
            lines.append(f"- {r}")
        lines.append("")
    if razones_incorrecto:
        lines.append("### Incorrecto")
        for r in razones_incorrecto[:15]:
            lines.append(f"- {r}")
        lines.append("")

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nReporte guardado en: {REPORT_PATH}")
    print(f"Resumen: Correcto={len(by_class['CORRECTO'])}, Parcial={len(by_class['PARCIAL'])}, Incorrecto={len(by_class['INCORRECTO'])}")


if __name__ == "__main__":
    main()
