"""
Prueba RAG: pregunta → búsqueda en Pinecone → (opcional) respuesta con Claude.
Uso:
  python -m src.rag.query_rag "¿Qué son los SubasCoins?"
  python -m src.rag.query_rag   # modo interactivo
Requiere PINECONE_API_KEY. Con ANTHROPIC_API_KEY genera respuesta con Claude.
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

from src.core.logger import log_error, log_cost, log_rag_query, log_rag_response
from src.core.resilience import call_claude_with_retry, UserFacingError, MENSAJE_OCUPADO
import anthropic as _anthropic_module

NAMESPACE = "helpcenter"
TOP_K = 5
SYSTEM_PROMPT_PATH = ROOT / "prompts" / "system_prompt_v1.md"
MAX_CONTEXT_CHARS = int(os.getenv("MAX_CONTEXT_CHARS", "20000"))

# Cliente singleton — instanciado una vez, reutilizado en todas las llamadas
_claude_client = None

def _get_claude_client():
    global _claude_client
    if _claude_client is None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return None
        _claude_client = _anthropic_module.Anthropic(api_key=api_key)
    return _claude_client


def get_index():
    api_key = os.getenv("PINECONE_API_KEY")
    index_name = os.getenv("PINECONE_INDEX_NAME", "vmc-bot-rag")
    if not api_key:
        raise SystemExit("Falta PINECONE_API_KEY en .env")
    from pinecone import Pinecone
    pc = Pinecone(api_key=api_key)
    return pc.Index(index_name)


def search(index, question: str):
    """Busca en Pinecone por texto; devuelve lista de chunks con score."""
    resp = index.search(
        namespace=NAMESPACE,
        query={"inputs": {"text": question}, "top_k": TOP_K},
        fields=["text", "topic", "source_url"],
    )
    result = getattr(resp, "result", None) or getattr(resp, "result", resp)
    hits = getattr(result, "hits", None) or getattr(resp, "matches", []) or []
    out = []
    for h in hits:
        hid = getattr(h, "_id", None) or getattr(h, "id", "")
        score = getattr(h, "_score", None) or getattr(h, "score", 0)
        score = float(score) if score is not None else 0.0
        fields = getattr(h, "fields", None) or {}
        if hasattr(fields, "get"):
            text = fields.get("text", "")
            topic = fields.get("topic", "")
            source_url = fields.get("source_url", "")
        else:
            text = getattr(fields, "text", "")
            topic = getattr(fields, "topic", "")
            source_url = getattr(fields, "source_url", "")
        if not text:
            continue
        out.append({
            "id": hid,
            "score": score,
            "text": text,
            "topic": topic,
            "source_url": source_url,
        })
    return out


def build_context(matches, live_block: str | None = None):
    """Convierte los chunks en un solo texto para el LLM, limitando el tamaño total del contexto."""
    parts: list[str] = []
    total_len = 0
    if live_block:
        live_text = "[Fuente en tiempo real — precios y planes actuales: https://www.vmcsubastas.com/subaspass]\n" + live_block
        if MAX_CONTEXT_CHARS > 0:
            live_text = live_text[:MAX_CONTEXT_CHARS]
        parts.append(live_text)
        total_len += len(live_text)
    if not matches:
        return "\n\n---\n\n".join(parts) if parts else ""
    for i, m in enumerate(matches, 1):
        chunk_text = f"[Fragmento {i}] (tema: {m.get('topic', '')})\n{m.get('text', '')}"
        if MAX_CONTEXT_CHARS > 0:
            remaining = MAX_CONTEXT_CHARS - total_len
            if remaining <= 0:
                break
            if len(chunk_text) > remaining:
                chunk_text = chunk_text[:remaining]
            parts.append(chunk_text)
            total_len += len(chunk_text)
        else:
            parts.append(chunk_text)
    return "\n\n---\n\n".join(parts)


def _is_subaspass_question(question: str) -> bool:
    q = (question or "").lower().strip()
    if not q:
        return False
    keywords = ("subaspass", "subas pass", "pase", "membresía", "membresia", "planes subas", "precio subas", "cuánto cuesta el pase", "costo subaspass")
    return any(k in q for k in keywords)


# --- PASO 3: multi-query condicional ---
def _needs_multi_query(q: str) -> bool:
    """
    Multi-query solo vale la pena en preguntas cortas o ambiguas (≤5 palabras).
    Preguntas largas y específicas ya tienen suficiente señal para Pinecone.
    Ahorro: elimina ~1 llamada Haiku por cada FAQ de más de 5 palabras.
    """
    return len(q.split()) <= 5


def _usage_to_dict(usage) -> dict:
    if usage is None:
        return {"input": 0, "output": 0, "cached_read": 0, "cached_creation": 0}
    return {
        "input":            getattr(usage, "input_tokens", 0) or 0,
        "output":           getattr(usage, "output_tokens", 0) or 0,
        "cached_read":      getattr(usage, "cache_read_input_tokens", 0) or 0,
        "cached_creation":  getattr(usage, "cache_creation_input_tokens", 0) or 0,
    }


def answer_with_claude(question: str, context: str, history: list[dict] | None = None) -> str:
    text, *_ = answer_with_claude_with_debug(question, context, history=history)
    return text


def answer_with_claude_with_debug(
    question: str,
    context: str,
    history: list[dict] | None = None,
) -> tuple[str, dict, int, str, str]:
    """Retorna (texto_respuesta, tokens_dict, latency_ms, system_prompt_used, rag_context_used)."""
    import time

    client = _get_claude_client()
    if not client:
        return "", _usage_to_dict(None), 0, "", context

    # PASO 5: dos bloques separados.
    # Bloque 1: system prompt completo (fijo, se cachea).
    # Bloque 2: contexto RAG (varía por pregunta, no se cachea).
    # Nota: usamos el archivo completo sin recortar por "## Texto del prompt"
    # para asegurar que supera el mínimo de 1,024 tokens que exige Anthropic.
    system_raw = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8") if SYSTEM_PROMPT_PATH.exists() else ""
    system_blocks = [
        {
            "type": "text",
            "text": system_raw + "\n\nCuando respondas, usa SOLO la información del siguiente contexto del Centro de Ayuda de VMC. No inventes nada.",
            "cache_control": {"type": "ephemeral"},
        },
        {
            "type": "text",
            "text": "Contexto:\n" + context,
        },
    ]

    messages = []
    if history:
        for turn in history:
            r = turn.get("role", "")
            c = turn.get("content", "")
            if r in ("user", "assistant") and c:
                messages.append({"role": r, "content": c})
    messages.append({"role": "user", "content": question})

    try:
        t0  = time.perf_counter()
        msg = call_claude_with_retry(
            client=client,
            model="claude-sonnet-4-20250514",
            max_tokens=300,  # PASO 4: reducido de 500 → 300 (respuestas WhatsApp deben ser concisas)
            system=system_blocks,  # PASO 5: lista de bloques en vez de string plano
            messages=messages,
        )
        latency_ms = int((time.perf_counter() - t0) * 1000)

        usage  = getattr(msg, "usage", None)
        tokens = _usage_to_dict(usage)
        block  = msg.content[0] if msg.content else None
        text   = block.text if block and hasattr(block, "text") else str(msg.content)

        log_cost(
            model="claude-sonnet-4-20250514",
            tokens_in=tokens.get("input", 0),
            tokens_out=tokens.get("output", 0),
        )
        log_rag_response(response_preview=text, model="claude-sonnet-4-20250514")

        system_full = system_blocks[0]["text"] + "\n\nContexto:\n" + context
        return text, tokens, latency_ms, system_full, context

    except UserFacingError as e:
        system_full = system_blocks[0]["text"] + "\n\nContexto:\n" + context
        log_error("query_rag_user_facing", message=str(e))
        return e.mensaje, _usage_to_dict(None), 0, system_full, context

    except Exception as e:
        system_full = system_blocks[0]["text"] + "\n\nContexto:\n" + context
        err_text = str(e)
        log_error("query_rag_claude_error", message=err_text, question=question[:80])
        return MENSAJE_OCUPADO, _usage_to_dict(None), 0, system_full, context


def main():
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
    else:
        question = input("Pregunta sobre VMC Subastas: ").strip()
    if not question:
        print("Escribe una pregunta.")
        return

    index = get_index()
    if os.getenv("ANTHROPIC_API_KEY"):
        matches = search_multi_query_rrf(index, question, top_k_per_query=5)
        print("(Usando multi-query + RRF)")
    else:
        matches = search(index, question)
    if not matches:
        print("No se encontraron fragmentos relevantes en Pinecone.")
        return

    print("\n--- Chunks recuperados (top {}) ---\n".format(len(matches)))
    for i, m in enumerate(matches, 1):
        sc = m.get("score")
        sc = float(sc) if sc is not None else 0.0
        print(f"[{i}] score={sc:.3f} | {m.get('topic', '')}")
        print(m.get("text", "")[:400] + ("..." if len(m.get("text", "")) > 400 else ""))
        print()

    context = build_context(matches)
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        print("--- Respuesta (Claude + RAG) ---\n")
        answer = answer_with_claude(question, context)
        print(answer)
    else:
        print("(Para generar respuesta con Claude, añade ANTHROPIC_API_KEY en .env)")


def search_by_queries_rrf(index, queries: list[str], top_k_per_query: int = 5):
    from src.rag.rrf import reciprocal_rank_fusion
    list_of_results = []
    for q in (queries or []):
        if not q:
            continue
        hits = search(index, q)
        if hits:
            list_of_results.append(hits)
    if not list_of_results:
        return []
    fused = reciprocal_rank_fusion(list_of_results, id_key="id")
    return fused[: top_k_per_query * 2]


def search_multi_query_rrf(index, question: str, top_k_per_query: int = 5):
    from src.rag.multi_query import generate_multi_queries
    # PASO 3: respetar la misma lógica condicional en el flujo no-debug
    if _needs_multi_query(question):
        queries = generate_multi_queries(question, num_queries=2)
    else:
        queries = [question]
    result = search_by_queries_rrf(index, queries, top_k_per_query)
    if not result:
        return search(index, question)
    return result


def search_multi_query_rrf_with_debug(index, question: str, top_k_per_query: int = 5) -> tuple:
    import time
    from src.rag.multi_query import generate_multi_queries_with_debug
    from src.rag.rrf import reciprocal_rank_fusion
    # PASO 3: respetar la misma lógica condicional en el flujo debug
    if _needs_multi_query(question):
        queries, _, _ = generate_multi_queries_with_debug(question, num_queries=2)
    else:
        queries = [question]
    t0 = time.perf_counter()
    list_of_results = []
    for q in queries:
        if not q:
            continue
        hits = search(index, q)
        if hits:
            list_of_results.append(hits)
    if not list_of_results:
        fallback = search(index, question)
        latency_ms = int((time.perf_counter() - t0) * 1000)
        return fallback, queries, [], latency_ms
    fused = reciprocal_rank_fusion(list_of_results, id_key="id")
    fused = fused[: top_k_per_query * 2]
    latency_ms = int((time.perf_counter() - t0) * 1000)
    return fused, queries, list_of_results, latency_ms


def ask_rag(question: str, use_multi_query: bool = True, history: list[dict] | None = None):
    question = (question or "").strip()
    if not question:
        return [], ""
    index = get_index()
    # PASO 3: respetar la misma lógica condicional en ask_rag
    if use_multi_query and os.getenv("ANTHROPIC_API_KEY") and _needs_multi_query(question):
        matches = search_multi_query_rrf(index, question, top_k_per_query=5)
    else:
        matches = search(index, question)

    live_block = None
    subaspass_chunk = None
    if _is_subaspass_question(question):
        try:
            from src.rag.live_source import fetch_subaspass_live
            live_text, live_url = fetch_subaspass_live()
            if live_text:
                live_block = live_text[:12000]
                subaspass_chunk = {
                    "id": "live-subaspass",
                    "score": 1.0,
                    "topic": "SubasPass (tiempo real)",
                    "text": live_text[:2000] + ("..." if len(live_text) > 2000 else ""),
                    "source_url": live_url,
                }
        except Exception:
            pass

    if not matches and not live_block:
        return [], "No se encontraron fragmentos relevantes."

    context = build_context(matches, live_block=live_block)
    answer = answer_with_claude(question, context, history=history) if os.getenv("ANTHROPIC_API_KEY") else ""
    chunks_out = []
    if subaspass_chunk:
        chunks_out.append(subaspass_chunk)
    for m in matches:
        sc = m.get("rrf_score") if m.get("rrf_score") is not None else m.get("score", 0)
        chunks_out.append({
            "id": m.get("id", ""),
            "score": round(float(sc), 3),
            "topic": m.get("topic", ""),
            "text": m.get("text", ""),
            "source_url": m.get("source_url", ""),
        })
    return chunks_out, answer


def _last_assistant_message(history: list[dict] | None) -> str | None:
    if not history:
        return None
    for turn in reversed(history):
        if turn.get("role") == "assistant":
            return (turn.get("content") or "").strip() or None
    return None


def ask_with_router(question: str, use_multi_query: bool = True, history: list[dict] | None = None):
    question = (question or "").strip()
    if not question:
        return [], "", "faq"
    last_bot = _last_assistant_message(history)
    try:
        from src.rag.router import classify_intent
        intent = classify_intent(question, last_assistant_message=last_bot)
    except Exception:
        intent = "faq"
    if intent == "faq":
        chunks, answer = ask_rag(question, use_multi_query=use_multi_query, history=history)
        return chunks, answer, "faq"
    if intent == "stock_search":
        try:
            from src.rag.inventory import search_vehicles, format_stock_answer
            vehicles = search_vehicles(question)
            answer = format_stock_answer(question, vehicles)
            chunks = [
                {
                    "id": v.get("id"),
                    "score": 1.0,
                    "topic": "inventario",
                    "text": (v.get("snippet") or v.get("title") or "")[:500],
                    "source_url": v.get("url"),
                }
                for v in (vehicles or [])
            ]
            return chunks, answer, "stock_search"
        except Exception:
            msg = "Por ahora puedes revisar las ofertas disponibles en vmcsubastas.com. Cuando esté listo, podré ayudarte a buscar carros y camionetas en tiempo real desde aquí."
            return [], msg, "stock_search"
    if intent == "soporte_humano":
        msg = "Entendido. Puedes contactarnos de Lunes a Viernes de 9am a 6pm por nuestro chat en vivo en la web o al correo contigo@vmcsubastas.com. Un agente te atenderá."
        return [], msg, "soporte_humano"
    msg = "Solo puedo ayudarte con dudas sobre VMC Subastas: registro, SubasCoins, consignación, ofertas, etc. Si tienes alguna pregunta sobre la plataforma, escríbela y con gusto te ayudo."
    return [], msg, "fuera_dominio"


def ask_with_router_debug(question: str, history: list[dict] | None = None) -> tuple[list, str, str, dict]:
    import time
    from src.rag.router import classify_intent_with_debug
    from src.rag.multi_query import generate_multi_queries_with_debug

    question = (question or "").strip()
    if not question:
        return [], "", "faq", {"intent": "faq", "total_latency_ms": 0}

    last_bot = _last_assistant_message(history)
    total_start = time.perf_counter()
    intent, intent_latency_ms, intent_tokens, intent_explanation = classify_intent_with_debug(
        question, last_assistant_message=last_bot
    )

    debug = {
        "intent": intent,
        "intent_latency_ms": intent_latency_ms,
        "intent_tokens": intent_tokens,
        "intent_explanation": intent_explanation,
        "multi_queries": None,
        "multi_query_latency_ms": None,
        "multi_query_tokens": None,
        "retrieval": None,
        "generation": None,
    }

    if intent != "faq":
        if intent == "stock_search":
            try:
                from src.rag.inventory import search_vehicles, format_stock_answer
                vehicles = search_vehicles(question)
                msg = format_stock_answer(question, vehicles)
                debug["stock"] = {
                    "results_count": len(vehicles or []),
                    "sample": [
                        {"id": v.get("id"), "title": v.get("title"), "url": v.get("url")}
                        for v in (vehicles or [])[:5]
                    ],
                }
                debug["total_latency_ms"] = int((time.perf_counter() - total_start) * 1000)
                return [], msg, intent, debug
            except Exception as e:
                msg = "Por ahora puedes revisar las ofertas disponibles en vmcsubastas.com. Cuando esté listo, podré ayudarte a buscar carros y camionetas en tiempo real desde aquí."
                debug["stock_error"] = str(e)
                debug["total_latency_ms"] = int((time.perf_counter() - total_start) * 1000)
                return [], msg, intent, debug
        elif intent == "soporte_humano":
            msg = "Entendido. Puedes contactarnos de Lunes a Viernes de 9am a 6pm por nuestro chat en vivo en la web o al correo contigo@vmcsubastas.com. Un agente te atenderá."
        else:
            msg = "Solo puedo ayudarte con dudas sobre VMC Subastas: registro, SubasCoins, consignación, ofertas, etc. Si tienes alguna pregunta sobre la plataforma, escríbela y con gusto te ayudo."
        debug["total_latency_ms"] = int((time.perf_counter() - total_start) * 1000)
        return [], msg, intent, debug

    # FAQ: multi-query condicional (PASO 3)
    # Solo preguntas cortas/ambiguas (≤5 palabras) generan variaciones con Haiku.
    # Preguntas largas tienen suficiente señal para Pinecone sin variaciones.
    if _needs_multi_query(question):
        queries, mq_tokens, mq_latency_ms = generate_multi_queries_with_debug(question, num_queries=2)
    else:
        queries = [question]
        mq_tokens = {"input": 0, "output": 0, "cached_read": 0, "cached_creation": 0}
        mq_latency_ms = 0

    debug["multi_queries"] = queries
    debug["multi_query_latency_ms"] = mq_latency_ms
    debug["multi_query_tokens"] = mq_tokens

    index = get_index()
    t0 = time.perf_counter()
    matches = search_by_queries_rrf(index, queries, top_k_per_query=5)
    if not matches:
        matches = search(index, question)
    retrieval_latency_ms = int((time.perf_counter() - t0) * 1000)

    live_block = None
    subaspass_chunk = None
    if _is_subaspass_question(question):
        try:
            from src.rag.live_source import fetch_subaspass_live
            live_text, live_url = fetch_subaspass_live()
            if live_text:
                live_block = live_text[:12000]
                subaspass_chunk = {
                    "id": "live-subaspass",
                    "score": 1.0,
                    "topic": "SubasPass (tiempo real)",
                    "text": live_text[:2000] + ("..." if len(live_text) > 2000 else ""),
                    "source_url": live_url,
                }
        except Exception:
            pass

    if not matches and not live_block:
        debug["retrieval"] = {
            "chunks": [],
            "rrf_applied": bool(queries and len(queries) > 1),
            "retrieval_latency_ms": retrieval_latency_ms,
            "queries": queries,
        }
        debug["total_latency_ms"] = int((time.perf_counter() - total_start) * 1000)
        return [], "No se encontraron fragmentos relevantes.", "faq", debug

    context = build_context(matches, live_block=live_block)
    answer, gen_tokens, gen_latency_ms, system_used, rag_context_used = answer_with_claude_with_debug(
        question, context, history=history
    )

    chunks_out = []
    if subaspass_chunk:
        chunks_out.append(subaspass_chunk)
    for m in matches:
        sc = m.get("rrf_score") if m.get("rrf_score") is not None else m.get("score", 0)
        chunks_out.append({
            "id": m.get("id", ""),
            "score": round(float(sc), 3),
            "topic": m.get("topic", ""),
            "text": m.get("text", ""),
            "source_url": m.get("source_url", ""),
        })

    retrieval_chunks_debug = []
    for c in (chunks_out or [])[:10]:
        retrieval_chunks_debug.append({
            "id": c.get("id"),
            "score": c.get("score"),
            "category": c.get("topic"),
            "text_preview": (c.get("text") or "")[:100] + ("..." if len(c.get("text") or "") > 100 else ""),
        })

    debug["retrieval"] = {
        "chunks": retrieval_chunks_debug,
        "rrf_applied": bool(queries and len(queries) > 1),
        "retrieval_latency_ms": retrieval_latency_ms,
        "queries": queries,
    }
    cached = (gen_tokens.get("cached_read") or 0) + (gen_tokens.get("cached_creation") or 0)
    debug["generation"] = {
        "model": "claude-sonnet-4-20250514",
        "tokens": gen_tokens,
        "cached_tokens": cached,
        "latency_ms": gen_latency_ms,
        "system_prompt": system_used,
        "rag_context": rag_context_used,
        "response_text": answer,
    }
    debug["total_latency_ms"] = int((time.perf_counter() - total_start) * 1000)
    return chunks_out, answer, "faq", debug


if __name__ == "__main__":
    main()