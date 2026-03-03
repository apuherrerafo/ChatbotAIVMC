"""
Multi-Query: genera 2 variaciones de la pregunta del usuario con Claude Haiku.
Crítico para español peruano (carro/vehículo, jalar/retirar, etc.).
Sin LangChain; llamada directa a Anthropic API.
"""
import os
import time
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

# Cliente instanciado UNA vez al importar el módulo — evita cold start en cada llamada
_client = None

def _get_client():
    global _client
    if _client is None:
        from anthropic import Anthropic
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return None
        _client = Anthropic(api_key=api_key)
    return _client


def _usage_to_dict(usage) -> dict:
    if usage is None:
        return {"input": 0, "output": 0, "cached_read": 0, "cached_creation": 0}
    return {
        "input":            getattr(usage, "input_tokens", 0) or 0,
        "output":           getattr(usage, "output_tokens", 0) or 0,
        "cached_read":      getattr(usage, "cache_read_input_tokens", 0) or 0,
        "cached_creation":  getattr(usage, "cache_creation_input_tokens", 0) or 0,
    }


# Prompt del sistema — cacheado porque nunca cambia entre llamadas
_SYSTEM_PROMPT = """Eres un asistente de VMC Subastas (plataforma de subastas de vehículos en Perú).
Tu única tarea es generar variaciones de preguntas usando sinónimos peruanos:
- carro / vehículo / auto / unidad
- jalar / retirar
- cuánto cobran / comisión / tarifas
- plata / dinero / monto
Responde SOLO con las frases solicitadas, una por línea, sin numeración ni explicación."""


def generate_multi_queries(question: str, num_queries: int = 2) -> list[str]:
    """
    Devuelve la pregunta original + 1 variación para mejorar retrieval.
    Reducido de 3 a 2 queries para bajar latencia ~40%.
    """
    queries, _, _ = generate_multi_queries_with_debug(question, num_queries)
    return queries


def generate_multi_queries_with_debug(
    question: str, num_queries: int = 2
) -> tuple[list[str], dict, int]:
    """Retorna (queries, tokens_dict, latency_ms)."""
    question = (question or "").strip()
    if not question:
        return [], _usage_to_dict(None), 0

    client = _get_client()
    if not client:
        return [question], _usage_to_dict(None), 0

    prompt_usuario = (
        f"Genera exactamente {num_queries} variaciones de esta pregunta con sinónimos peruanos. "
        f"Solo las frases, una por línea:\n\n{question}"
    )

    try:
        t0 = time.perf_counter()
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=120,
            system=[
                {
                    "type": "text",
                    "text": _SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},  # cachea el system prompt
                }
            ],
            messages=[
                {"role": "user", "content": prompt_usuario}
            ],
        )
        latency_ms = int((time.perf_counter() - t0) * 1000)
        tokens     = _usage_to_dict(getattr(msg, "usage", None))

        block = msg.content[0] if msg.content else None
        text  = block.text if block and hasattr(block, "text") else ""
        lines = [ln.strip() for ln in text.strip().split("\n") if ln.strip()][:num_queries]

        if not lines:
            return [question], tokens, latency_ms

        # Siempre incluir la pregunta original
        variaciones = [l for l in lines if l != question][: num_queries - 1]
        return [question] + variaciones, tokens, latency_ms

    except Exception:
        return [question], _usage_to_dict(None), 0
