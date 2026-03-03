"""
src/core/logger.py
------------------
Logger unificado para VMC-Bot.

Resuelve:
  - UnicodeEncodeError en consola Windows (cp1252 → UTF-8 forzado)
  - Logs dispersos entre módulos → un solo punto de entrada
  - Falta de trazabilidad por evento → JSONL estructurado por tipo

Archivos de salida:
  - logs/rag_audit.jsonl     → queries, chunks usados, respuestas
  - logs/cost_tracker.jsonl  → tokens y costo estimado por llamada
  - logs/errors.jsonl        → errores de Anthropic, Firecrawl, Pinecone
"""

import sys
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# 1. Fix UTF-8 en Windows
#    sys.stdout/stderr usan cp1252 por defecto en Windows.
#    reconfigure() los fuerza a UTF-8 para que caracteres como →, ✓, ñ
#    no rompan los scripts de QA y validación.
# ---------------------------------------------------------------------------
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        # Python < 3.7 no tiene reconfigure(); fallback silencioso.
        pass

# ---------------------------------------------------------------------------
# 2. Logger de consola estándar
#    Usa el logging de Python para mensajes humanos en consola.
#    Nivel INFO por defecto; se puede subir a DEBUG con set_console_level().
# ---------------------------------------------------------------------------
_console_logger = logging.getLogger("vmc_bot")
_console_logger.setLevel(logging.DEBUG)

if not _console_logger.handlers:
    _handler = logging.StreamHandler(sys.stdout)
    _handler.setLevel(logging.INFO)
    _handler.setFormatter(
        logging.Formatter("[%(asctime)s] %(levelname)s — %(message)s", "%H:%M:%S")
    )
    _console_logger.addHandler(_handler)


def set_console_level(level: str = "INFO") -> None:
    """Cambia el nivel de la consola en runtime. Útil para debug puntual."""
    _console_logger.handlers[0].setLevel(getattr(logging, level.upper(), logging.INFO))


# ---------------------------------------------------------------------------
# 3. Rutas de archivos JSONL
#    Los logs viven en vmc-bot/logs/. Se crean automáticamente si no existen.
# ---------------------------------------------------------------------------
_LOGS_DIR = Path(__file__).resolve().parents[2] / "logs"
_LOGS_DIR.mkdir(parents=True, exist_ok=True)

_LOG_FILES = {
    "rag":   _LOGS_DIR / "rag_audit.jsonl",
    "cost":  _LOGS_DIR / "cost_tracker.jsonl",
    "error": _LOGS_DIR / "errors.jsonl",
}


def _resolve_log_file(event_type: str) -> Path:
    """
    Elige el archivo de log según el tipo de evento.
    Regla:
      - contiene 'error' o 'fail'  → errors.jsonl
      - contiene 'cost' o 'token'  → cost_tracker.jsonl
      - cualquier otro             → rag_audit.jsonl
    """
    t = event_type.lower()
    if any(k in t for k in ("error", "fail", "429", "credit")):
        return _LOG_FILES["error"]
    if any(k in t for k in ("cost", "token")):
        return _LOG_FILES["cost"]
    return _LOG_FILES["rag"]


# ---------------------------------------------------------------------------
# 4. Función principal: log_event()
#    Punto de entrada único para TODOS los módulos del proyecto.
#
#    Uso básico:
#      log_event("rag_query", query="¿Qué es SubasCoins?", intent="faq")
#      log_event("anthropic_error_429", model="claude-sonnet-4", attempt=2)
#      log_event("cost_llamada", tokens_in=1200, tokens_out=300, cost_usd=0.008)
# ---------------------------------------------------------------------------
def log_event(event_type: str, **fields) -> None:
    """
    Escribe un evento estructurado en JSONL y lo imprime en consola.

    Args:
        event_type: Identificador del evento. Determina el archivo de destino.
                    Ejemplos: "rag_query", "anthropic_error_429",
                              "cost_llamada", "firecrawl_no_credits",
                              "rag_response", "golden_eval_result"
        **fields:   Datos adicionales del evento. Se serializan a JSON.
                    Los valores no serializables se convierten a str.
    """
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "type": event_type,
        **fields,
    }

    # Escritura en JSONL (append, UTF-8 explícito)
    log_path = _resolve_log_file(event_type)
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
    except OSError as e:
        # Si falla escribir el log, al menos lo mostramos en consola.
        _console_logger.error(f"No se pudo escribir log en {log_path}: {e}")

    # Salida en consola según severidad
    if any(k in event_type.lower() for k in ("error", "fail", "429", "credit")):
        _console_logger.warning(f"[{event_type}] {fields}")
    else:
        _console_logger.info(f"[{event_type}] {fields}")


# ---------------------------------------------------------------------------
# 5. Helpers semánticos (opcionales pero recomendados)
#    Simplifican el uso en los módulos más comunes.
#    En lugar de recordar los nombres de campos, usas funciones con firma clara.
# ---------------------------------------------------------------------------

def log_rag_query(query: str, intent: str, chunks_used: int,
                  tokens_in: int, tokens_out: int, latency_ms: float) -> None:
    """Registra una query RAG con sus métricas clave."""
    log_event(
        "rag_query",
        query=query,
        intent=intent,
        chunks_used=chunks_used,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        latency_ms=round(latency_ms, 2),
    )


def log_rag_response(response_preview: str, model: str) -> None:
    """Registra los primeros 200 chars de la respuesta final del bot."""
    log_event(
        "rag_response",
        response_preview=response_preview[:200],
        model=model,
    )


def log_cost(model: str, tokens_in: int, tokens_out: int) -> None:
    """
    Registra el costo estimado de una llamada a Claude.
    Tarifas hardcodeadas según roadmap (actualizar si cambian).
    """
    # Tarifas por millón de tokens (USD)
    RATES = {
        "claude-sonnet": {"in": 3.0, "out": 15.0},
        "claude-haiku":  {"in": 1.0, "out": 5.0},
    }
    rate_key = "claude-haiku" if "haiku" in model.lower() else "claude-sonnet"
    rates = RATES[rate_key]
    cost_usd = (tokens_in / 1_000_000 * rates["in"]) + \
               (tokens_out / 1_000_000 * rates["out"])

    log_event(
        "cost_llamada",
        model=model,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        cost_usd=round(cost_usd, 6),
    )


def log_error(error_type: str, message: str, **extra) -> None:
    """Registra un error de integración (429, Firecrawl, Pinecone, etc.)."""
    log_event(
        f"error_{error_type}",
        message=message,
        **extra,
    )