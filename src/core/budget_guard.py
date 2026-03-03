"""
src/core/budget_guard.py
------------------------
Guardas de presupuesto diario basados en logs/cost_tracker.jsonl.

Se usan para proteger scripts batch (evaluación, extracción de imágenes, etc.)
de sobrepasar un límite diario estimado de gasto en LLMs.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


class BudgetExceededError(Exception):
    """Lanzada cuando el costo estimado diario supera el límite configurado."""


_ROOT = Path(__file__).resolve().parents[2]
_COST_LOG = _ROOT / "logs" / "cost_tracker.jsonl"


def _is_today_utc(ts: str) -> bool:
    """True si el timestamp ISO8601 pertenece al día de hoy en UTC."""
    try:
        dt = datetime.fromisoformat(ts)
    except Exception:
        return False
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    today = datetime.now(timezone.utc).date()
    return dt.date() == today


def check_daily_budget(limit_usd: float = 2.0) -> None:
    """
    Lee logs/cost_tracker.jsonl y suma cost_usd de las llamadas de HOY (UTC).

    Si el total supera limit_usd, lanza BudgetExceededError.
    Si el archivo no existe o está vacío, asume $0 gastado.
    """
    if not _COST_LOG.exists():
        return

    total = 0.0
    try:
        with _COST_LOG.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                ts = entry.get("ts")
                if not ts or not _is_today_utc(ts):
                    continue
                cost = entry.get("cost_usd")
                if isinstance(cost, (int, float)):
                    total += float(cost)
    except OSError:
        # Si no se puede leer el archivo, ser conservador y no bloquear.
        return

    if total > limit_usd:
        raise BudgetExceededError(f"Gasto hoy: ${total:.3f} — límite: ${limit_usd:.3f}")


__all__ = ["check_daily_budget", "BudgetExceededError"]

