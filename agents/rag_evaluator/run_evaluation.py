"""
agents/rag_evaluator/run_evaluation.py
---------------------------------------
Evaluador de calidad RAG para VMC-Bot.

Corre cada pregunta del golden dataset contra el bot,
evalúa la respuesta con Claude Haiku como juez, y genera
un reporte de calidad con score por criterio.

Uso:
  python agents/rag_evaluator/run_evaluation.py
  python agents/rag_evaluator/run_evaluation.py --limite 5
"""

import json
import argparse
import httpx
import sys
from pathlib import Path
from datetime import datetime, timezone

import anthropic
from src.core.logger import log_event, log_error
from src.core.resilience import call_claude_with_retry
from src.core.budget_guard import check_daily_budget, BudgetExceededError

# ---------------------------------------------------------------------------
# 1. Configuración
# ---------------------------------------------------------------------------
_ROOT          = Path(__file__).resolve().parents[2]
_GOLDEN_FILE   = _ROOT / "data" / "golden_dataset" / "faqs_golden.json"
_REPORTS_DIR   = _ROOT / "logs"
_BOT_URL       = "http://localhost:8000/api/ask"

# Umbrales de calidad (definidos en AGENTS.md)
UMBRAL_PILOTO   = 4.0
UMBRAL_MEJORAR  = 3.0

# Cliente Anthropic para el juez evaluador
client = anthropic.Anthropic()

# ---------------------------------------------------------------------------
# 2. Prompt del juez evaluador
#    Haiku actúa como juez neutral. Evalúa cada respuesta del bot
#    comparándola con la respuesta esperada del golden dataset.
# ---------------------------------------------------------------------------
JUEZ_SYSTEM = """Eres un evaluador de calidad estricto para un chatbot de subastas de vehículos en Perú llamado VMC-Bot.

Tu trabajo es evaluar la respuesta del bot comparándola con la respuesta esperada.
Debes devolver SOLO un JSON con esta estructura exacta, sin texto adicional:

{
  "accuracy": <1-5>,
  "sin_alucinacion": <1-5>,
  "intent_routing": <1-5>,
  "relevancia": <1-5>,
  "guardrail": <1-5>,
  "comentario": "<una línea explicando el puntaje más bajo>"
}

Criterios de evaluación:
- accuracy (1-5): ¿La información es correcta y completa? 5=perfecta, 3=correcta pero incompleta, 1=incorrecta
- sin_alucinacion (1-5): ¿Inventó datos financieros (precios, comisiones, plazos)? 5=nada inventado, 1=inventó números
- intent_routing (1-5): ¿Clasificó bien la intención? 5=correcta, 3=relacionada, 1=incorrecta
- relevancia (1-5): ¿Respondió lo que se preguntó? 5=exactamente, 3=parcialmente, 1=no respondió
- guardrail (1-5): ¿Manejó bien preguntas fuera del dominio VMC? 5=rechazó correctamente o no aplica, 1=respondió fuera de dominio

REGLA CRÍTICA: Si el bot inventó cualquier número (porcentaje, precio, plazo), sin_alucinacion = 1 automáticamente."""


def evaluar_respuesta(pregunta: str, respuesta_bot: str,
                      respuesta_esperada: str, intencion_esperada: str,
                      intencion_clasificada: str) -> dict:
    """
    Usa Claude Haiku como juez para evaluar la respuesta del bot.
    
    Returns:
        Dict con scores por criterio o scores de 0 si falla la evaluación.
    """
    prompt = f"""Pregunta del usuario: {pregunta}

Intención esperada: {intencion_esperada}
Intención clasificada por el bot: {intencion_clasificada}

Respuesta esperada (golden):
{respuesta_esperada}

Respuesta real del bot:
{respuesta_bot}

Evalúa la respuesta del bot según los criterios indicados."""

    try:
        respuesta = call_claude_with_retry(
            client=client,
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            system=JUEZ_SYSTEM,
            messages=[{"role": "user", "content": prompt}]
        )
        texto = respuesta.content[0].text.strip()
        # Limpiar posibles backticks de markdown
        texto = texto.replace("```json", "").replace("```", "").strip()
        return json.loads(texto)

    except Exception as e:
        log_error("evaluador_juez_error", message=str(e), pregunta=pregunta[:50])
        return {
            "accuracy": 0, "sin_alucinacion": 0, "intent_routing": 0,
            "relevancia": 0, "guardrail": 0,
            "comentario": f"Error en evaluación: {e}"
        }


# ---------------------------------------------------------------------------
# 3. Llamada al bot
# ---------------------------------------------------------------------------
def preguntar_al_bot(pregunta: str) -> dict:
    """
    Envía la pregunta al endpoint del bot y devuelve la respuesta.
    
    Returns:
        Dict con respuesta, intención, y chunks usados.
        En caso de error devuelve valores vacíos.
    """
    try:
        r = httpx.post(
            _BOT_URL,
            json={"message": pregunta},
            timeout=30.0
        )
        r.raise_for_status()
        data = r.json()
        return {
            "respuesta":  data.get("response", ""),
            "intencion":  data.get("intent", "desconocida"),
            "chunks":     data.get("chunks_used", 0),
            "error":      None
        }
    except httpx.ConnectError:
        return {
            "respuesta": "", "intencion": "error", "chunks": 0,
            "error": "Bot no disponible. Asegurate de que el servidor esta corriendo en localhost:8000"
        }
    except Exception as e:
        return {
            "respuesta": "", "intencion": "error", "chunks": 0,
            "error": str(e)
        }


# ---------------------------------------------------------------------------
# 4. Evaluación completa
# ---------------------------------------------------------------------------
def correr_evaluacion(limite: int | None = None) -> dict:
    """
    Corre el golden dataset completo contra el bot y evalúa cada respuesta.
    
    Args:
        limite: Si se especifica, solo evalúa las primeras N preguntas.
    
    Returns:
        Dict con resultados detallados y métricas agregadas.
    """
    # Cargar golden dataset
    if not _GOLDEN_FILE.exists():
        print(f"ERROR: No se encontro el golden dataset en {_GOLDEN_FILE}")
        return {}

    with open(_GOLDEN_FILE, "r", encoding="utf-8") as f:
        golden = json.load(f)

    preguntas = golden if not limite else golden[:limite]
    total = len(preguntas)

    print(f"\n=== EVALUACION RAG VMC-Bot ===")
    print(f"Preguntas a evaluar: {total}")
    print(f"Bot URL: {_BOT_URL}")
    print(f"{'='*40}\n")

    resultados = []
    fallos_criticos = []
    sin_cobertura   = []

    for i, entrada in enumerate(preguntas, 1):
        pregunta          = entrada.get("pregunta", "")
        respuesta_esperada = entrada.get("respuesta_esperada", "")
        intencion_esperada = entrada.get("intencion", "faq")
        id_pregunta        = entrada.get("id", f"GD-{i:03d}")

        print(f"[{i}/{total}] {id_pregunta}: {pregunta[:60]}...")

        # Preguntar al bot
        bot_result = preguntar_al_bot(pregunta)

        if bot_result["error"]:
            print(f"  ERROR: {bot_result['error']}\n")
            if "no disponible" in bot_result["error"]:
                print("Detener evaluacion: el servidor no esta corriendo.")
                break
            continue

        # Detectar sin cobertura (respuesta muy corta o genérica)
        if len(bot_result["respuesta"]) < 50 or bot_result["chunks"] == 0:
            sin_cobertura.append({
                "id": id_pregunta,
                "pregunta": pregunta,
                "chunks": bot_result["chunks"]
            })

        # Evaluar con Haiku como juez
        scores = evaluar_respuesta(
            pregunta=pregunta,
            respuesta_bot=bot_result["respuesta"],
            respuesta_esperada=respuesta_esperada,
            intencion_esperada=intencion_esperada,
            intencion_clasificada=bot_result["intencion"]
        )

        score_promedio = sum([
            scores.get("accuracy", 0),
            scores.get("sin_alucinacion", 0),
            scores.get("intent_routing", 0),
            scores.get("relevancia", 0),
            scores.get("guardrail", 0),
        ]) / 5

        # Detectar fallos críticos
        if scores.get("sin_alucinacion", 5) == 1:
            fallos_criticos.append({
                "id": id_pregunta,
                "pregunta": pregunta,
                "tipo": "ALUCINACION FINANCIERA",
                "comentario": scores.get("comentario", "")
            })
        elif score_promedio < 2.0:
            fallos_criticos.append({
                "id": id_pregunta,
                "pregunta": pregunta,
                "tipo": "SCORE CRITICO",
                "comentario": scores.get("comentario", "")
            })

        resultado = {
            "id":                  id_pregunta,
            "pregunta":            pregunta,
            "intencion_esperada":  intencion_esperada,
            "intencion_real":      bot_result["intencion"],
            "chunks_usados":       bot_result["chunks"],
            "scores":              scores,
            "score_promedio":      round(score_promedio, 2),
        }
        resultados.append(resultado)

        estado = "OK" if score_promedio >= 4.0 else ("REVISAR" if score_promedio >= 3.0 else "FALLO")
        print(f"  Score: {score_promedio:.1f}/5 [{estado}] — {scores.get('comentario', '')}\n")

        log_event("eval_pregunta", id=id_pregunta, score=score_promedio,
                  intencion_real=bot_result["intencion"])

    # ---------------------------------------------------------------------------
    # 5. Métricas agregadas
    # ---------------------------------------------------------------------------
    if not resultados:
        return {}

    scores_promedios = [r["score_promedio"] for r in resultados]
    score_global = sum(scores_promedios) / len(scores_promedios)

    por_criterio = {}
    for criterio in ["accuracy", "sin_alucinacion", "intent_routing", "relevancia", "guardrail"]:
        valores = [r["scores"].get(criterio, 0) for r in resultados]
        por_criterio[criterio] = round(sum(valores) / len(valores), 2)

    # Determinar estado del bot
    if any(f["tipo"] == "ALUCINACION FINANCIERA" for f in fallos_criticos):
        estado_bot = "BLOQUEADO — alucinacion financiera detectada"
    elif score_global >= UMBRAL_PILOTO:
        estado_bot = "LISTO PARA PILOTO"
    elif score_global >= UMBRAL_MEJORAR:
        estado_bot = "NECESITA MEJORAS"
    else:
        estado_bot = "NO DEPLOYAR — score critico"

    reporte = {
        "fecha":           datetime.now(timezone.utc).isoformat(),
        "total_preguntas": len(resultados),
        "score_global":    round(score_global, 2),
        "por_criterio":    por_criterio,
        "estado_bot":      estado_bot,
        "fallos_criticos": fallos_criticos,
        "sin_cobertura":   sin_cobertura,
        "detalle":         resultados,
    }

    return reporte


# ---------------------------------------------------------------------------
# 6. Imprimir y guardar reporte
# ---------------------------------------------------------------------------
def imprimir_reporte(reporte: dict) -> None:
    """Imprime el resumen del reporte en consola."""
    if not reporte:
        return

    print(f"\n{'='*40}")
    print(f"=== RESULTADO FINAL ===")
    print(f"{'='*40}")
    print(f"Score global:     {reporte['score_global']}/5")
    print(f"Estado del bot:   {reporte['estado_bot']}")
    print(f"\nPOR CRITERIO:")
    for criterio, score in reporte["por_criterio"].items():
        print(f"  {criterio:<20} {score}/5")

    if reporte["fallos_criticos"]:
        print(f"\nFALLOS CRITICOS ({len(reporte['fallos_criticos'])}):")
        for f in reporte["fallos_criticos"]:
            print(f"  [{f['id']}] {f['tipo']}: {f['pregunta'][:50]}...")
            print(f"         → {f['comentario']}")

    if reporte["sin_cobertura"]:
        print(f"\nSIN COBERTURA EN RAG ({len(reporte['sin_cobertura'])}):")
        for s in reporte["sin_cobertura"]:
            print(f"  [{s['id']}] {s['pregunta'][:60]}...")

    print(f"\n{'='*40}\n")


def main():
    parser = argparse.ArgumentParser(description="Evaluador de calidad RAG — VMC-Bot")
    parser.add_argument(
        "--limite", type=int, default=None,
        help="Evaluar solo las primeras N preguntas del golden dataset"
    )
    args = parser.parse_args()

    # Guard de presupuesto diario: protege contra corridas masivas del evaluador.
    try:
        check_daily_budget(limit_usd=2.0)
    except BudgetExceededError as e:
        print(f"[BUDGET] {e}")
        sys.exit(1)

    reporte = correr_evaluacion(limite=args.limite)
    if not reporte:
        return

    imprimir_reporte(reporte)

    # Guardar reporte JSON
    fecha_str    = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")
    reporte_path = _REPORTS_DIR / f"eval_report_{fecha_str}.json"
    with open(reporte_path, "w", encoding="utf-8") as f:
        json.dump(reporte, f, ensure_ascii=False, indent=2)

    print(f"Reporte guardado en: {reporte_path}")


if __name__ == "__main__":
    main()