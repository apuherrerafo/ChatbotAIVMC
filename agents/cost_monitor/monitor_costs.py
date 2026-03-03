"""
agents/cost_monitor/monitor_costs.py
-------------------------------------
Monitor de costos real para VMC-Bot.

Lee los logs generados por src/core/logger.py y calcula:
  - Total de tokens consumidos en el período
  - Costo real en dólares por modelo
  - Costo promedio por mensaje y por conversación
  - Alerta si se supera el 70% o 90% del presupuesto mensual

Uso:
  python agents/cost_monitor/monitor_costs.py
  python agents/cost_monitor/monitor_costs.py --dias 7
  python agents/cost_monitor/monitor_costs.py --mes 2026-03
"""

import json
import argparse
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import defaultdict

# ---------------------------------------------------------------------------
# 1. Configuración de presupuesto
#    Basado en el roadmap VMC-Bot. Actualizar si cambian los planes.
# ---------------------------------------------------------------------------
PRESUPUESTO_MENSUAL_USD = 168.0  # Escenario máximo del roadmap

ALERTAS = {
    "precaucion": 0.70,   # 70% → advertencia amarilla
    "critico":    0.90,   # 90% → alerta roja
}

# Rutas
_ROOT = Path(__file__).resolve().parents[2]
_COST_LOG = _ROOT / "logs" / "cost_tracker.jsonl"
_REPORTS_DIR = _ROOT / "logs"


# ---------------------------------------------------------------------------
# 2. Lectura de logs
# ---------------------------------------------------------------------------
def leer_eventos_costo(desde: datetime | None = None) -> list[dict]:
    """
    Lee todos los eventos de costo desde logs/cost_tracker.jsonl.
    
    Args:
        desde: Filtrar solo eventos a partir de esta fecha (UTC).
               Si es None, lee todos los eventos.
    
    Returns:
        Lista de dicts con los eventos de costo.
    """
    if not _COST_LOG.exists():
        return []

    eventos = []
    with open(_COST_LOG, "r", encoding="utf-8") as f:
        for linea in f:
            linea = linea.strip()
            if not linea:
                continue
            try:
                evento = json.loads(linea)
                # Solo procesar eventos de tipo costo
                if evento.get("type") != "cost_llamada":
                    continue
                # Filtrar por fecha si se especificó
                if desde:
                    ts = datetime.fromisoformat(evento["ts"])
                    if ts < desde:
                        continue
                eventos.append(evento)
            except (json.JSONDecodeError, KeyError):
                continue

    return eventos


# ---------------------------------------------------------------------------
# 3. Cálculo de métricas
# ---------------------------------------------------------------------------
def calcular_metricas(eventos: list[dict]) -> dict:
    """
    Calcula métricas de costo a partir de los eventos de log.
    
    Returns:
        Dict con todas las métricas calculadas.
    """
    if not eventos:
        return {
            "total_eventos": 0,
            "total_tokens_in": 0,
            "total_tokens_out": 0,
            "costo_total_usd": 0.0,
            "por_modelo": {},
            "costo_promedio_mensaje": 0.0,
            "costo_promedio_chat": 0.0,
        }

    total_tokens_in = 0
    total_tokens_out = 0
    costo_total = 0.0
    por_modelo = defaultdict(lambda: {
        "llamadas": 0,
        "tokens_in": 0,
        "tokens_out": 0,
        "costo_usd": 0.0
    })

    for evento in eventos:
        tokens_in  = evento.get("tokens_in", 0)
        tokens_out = evento.get("tokens_out", 0)
        costo      = evento.get("cost_usd", 0.0)
        modelo     = evento.get("model", "desconocido")

        total_tokens_in  += tokens_in
        total_tokens_out += tokens_out
        costo_total      += costo

        por_modelo[modelo]["llamadas"]   += 1
        por_modelo[modelo]["tokens_in"]  += tokens_in
        por_modelo[modelo]["tokens_out"] += tokens_out
        por_modelo[modelo]["costo_usd"]  += costo

    n = len(eventos)
    # Estimamos 3 mensajes del bot por chat (6 mensajes totales, 3 respuestas)
    costo_promedio_chat = (costo_total / n * 3) if n > 0 else 0.0

    return {
        "total_eventos":          n,
        "total_tokens_in":        total_tokens_in,
        "total_tokens_out":       total_tokens_out,
        "costo_total_usd":        round(costo_total, 4),
        "por_modelo":             dict(por_modelo),
        "costo_promedio_mensaje": round(costo_total / n, 6) if n > 0 else 0.0,
        "costo_promedio_chat":    round(costo_promedio_chat, 4),
    }


# ---------------------------------------------------------------------------
# 4. Evaluación de alertas
# ---------------------------------------------------------------------------
def evaluar_alerta(costo_total: float) -> tuple[str, str]:
    """
    Evalúa el nivel de alerta según el presupuesto mensual.
    
    Returns:
        Tuple (nivel, mensaje) donde nivel es "ok", "precaucion" o "critico".
    """
    pct = costo_total / PRESUPUESTO_MENSUAL_USD

    if pct >= ALERTAS["critico"]:
        return (
            "critico",
            f"ALERTA CRITICA: {pct*100:.0f}% del presupuesto usado "
            f"(${costo_total:.2f} / ${PRESUPUESTO_MENSUAL_USD:.2f})"
        )
    elif pct >= ALERTAS["precaucion"]:
        return (
            "precaucion",
            f"PRECAUCION: {pct*100:.0f}% del presupuesto usado "
            f"(${costo_total:.2f} / ${PRESUPUESTO_MENSUAL_USD:.2f})"
        )
    else:
        return (
            "ok",
            f"OK: {pct*100:.0f}% del presupuesto usado "
            f"(${costo_total:.2f} / ${PRESUPUESTO_MENSUAL_USD:.2f})"
        )


# ---------------------------------------------------------------------------
# 5. Generación del reporte
# ---------------------------------------------------------------------------
def generar_reporte(metricas: dict, periodo: str, alerta: tuple) -> str:
    """Genera el texto del reporte de costos."""
    nivel, msg_alerta = alerta
    icono = {"ok": "OK", "precaucion": "PRECAUCION", "critico": "ALERTA"}[nivel]

    lineas = [
        f"",
        f"=== REPORTE DE COSTOS VMC-Bot — {periodo} ===",
        f"",
        f"[{icono}] {msg_alerta}",
        f"",
        f"TOKENS CONSUMIDOS:",
        f"  Input:  {metricas['total_tokens_in']:,} tokens",
        f"  Output: {metricas['total_tokens_out']:,} tokens",
        f"  Total:  {metricas['total_tokens_in'] + metricas['total_tokens_out']:,} tokens",
        f"",
        f"COSTOS POR MODELO:",
    ]

    for modelo, datos in metricas["por_modelo"].items():
        lineas.append(
            f"  {modelo}: {datos['llamadas']} llamadas | "
            f"${datos['costo_usd']:.4f}"
        )

    lineas += [
        f"",
        f"METRICAS:",
        f"  Llamadas totales:        {metricas['total_eventos']}",
        f"  Costo total:             ${metricas['costo_total_usd']:.4f}",
        f"  Costo promedio/mensaje:  ${metricas['costo_promedio_mensaje']:.6f}",
        f"  Costo promedio/chat:     ${metricas['costo_promedio_chat']:.4f}",
        f"",
        f"PRESUPUESTO MENSUAL: ${PRESUPUESTO_MENSUAL_USD:.2f}",
        f"  Gastado:   ${metricas['costo_total_usd']:.4f}",
        f"  Restante:  ${PRESUPUESTO_MENSUAL_USD - metricas['costo_total_usd']:.4f}",
        f"",
    ]

    if nivel == "critico":
        lineas.append("ACCION REQUERIDA: Revisar y reducir uso de tokens inmediatamente.")
        lineas.append("  - Reducir max_tokens en llamadas a Sonnet")
        lineas.append("  - Verificar que prompt caching este activado")
        lineas.append("  - Considerar rutear mas queries a Haiku")
    elif nivel == "precaucion":
        lineas.append("RECOMENDACION: Monitorear de cerca el resto del mes.")
        lineas.append("  - Verificar que prompt caching este activado")

    lineas.append("")
    return "\n".join(lineas)


# ---------------------------------------------------------------------------
# 6. Entry point
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Monitor de costos VMC-Bot")
    parser.add_argument(
        "--dias", type=int, default=30,
        help="Analizar los últimos N días (default: 30)"
    )
    parser.add_argument(
        "--mes", type=str, default=None,
        help="Analizar un mes específico en formato YYYY-MM (ej: 2026-03)"
    )
    args = parser.parse_args()

    # Determinar período
    ahora = datetime.now(timezone.utc)
    if args.mes:
        año, mes = map(int, args.mes.split("-"))
        desde = datetime(año, mes, 1, tzinfo=timezone.utc)
        periodo = f"{args.mes}"
    else:
        desde = ahora - timedelta(days=args.dias)
        periodo = f"Ultimos {args.dias} dias"

    # Leer, calcular y reportar
    eventos  = leer_eventos_costo(desde=desde)
    metricas = calcular_metricas(eventos)
    alerta   = evaluar_alerta(metricas["costo_total_usd"])
    reporte  = generar_reporte(metricas, periodo, alerta)

    print(reporte)

    # Guardar reporte en logs/
    fecha_str = ahora.strftime("%Y%m%d_%H%M")
    reporte_path = _REPORTS_DIR / f"cost_report_{fecha_str}.txt"
    reporte_path.write_text(reporte, encoding="utf-8")
    print(f"Reporte guardado en: {reporte_path}")


if __name__ == "__main__":
    main()