"""
Estimación de costo por mensaje (subagente Monitor de Costos).
Usado para log de requests y reportes mensuales.
Interfaz de debug: calculate_cost con tokens reales de la API.
"""

PRICES = {
    "haiku": {"input": 1.0, "output": 5.0, "cached_input": 0.10},
    "sonnet": {"input": 3.0, "output": 15.0, "cached_input": 0.30},
}


def calculate_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
    cached_tokens: int = 0,
) -> float:
    """Costo en USD a partir de tokens reales (input, output, cached). Precios por M tokens."""
    p = PRICES.get(model, PRICES["haiku"])
    uncached = max(0, input_tokens - cached_tokens)
    cost = (
        (uncached * p["input"] / 1_000_000)
        + (cached_tokens * p["cached_input"] / 1_000_000)
        + (output_tokens * p["output"] / 1_000_000)
    )
    return round(cost, 6)


def estimate_message_cost(
    system_prompt_tokens: int = 2000,
    rag_context_tokens: int = 500,
    user_message_tokens: int = 100,
    history_tokens: int = 500,
    response_tokens: int = 300,
    cached: bool = True,
) -> dict:
    """Estima costo en USD por mensaje (Sonnet + Haiku router + multi-query)."""
    input_tokens = (
        system_prompt_tokens
        + rag_context_tokens
        + user_message_tokens
        + history_tokens
    )
    if cached:
        cached_portion = system_prompt_tokens
        uncached_portion = input_tokens - cached_portion
        input_cost = (cached_portion * 0.30 / 1_000_000) + (
            uncached_portion * 3.0 / 1_000_000
        )
    else:
        input_cost = input_tokens * 3.0 / 1_000_000
    output_cost = response_tokens * 15.0 / 1_000_000
    haiku_input = user_message_tokens + 200
    haiku_output = 20
    haiku_cost = (haiku_input * 1.0 / 1_000_000) + (haiku_output * 5.0 / 1_000_000)
    mq_input = user_message_tokens + 300
    mq_output = 150
    mq_cost = (mq_input * 1.0 / 1_000_000) + (mq_output * 5.0 / 1_000_000)
    total_per_message = input_cost + output_cost + haiku_cost + mq_cost
    return {
        "sonnet_input_cost_usd": round(input_cost, 6),
        "sonnet_output_cost_usd": round(output_cost, 6),
        "haiku_router_cost_usd": round(haiku_cost, 6),
        "haiku_multiquery_cost_usd": round(mq_cost, 6),
        "total_per_message_usd": round(total_per_message, 6),
    }


def estimate_from_request(
    question_len: int,
    answer_len: int,
    num_chunks: int = 5,
    cached: bool = True,
) -> dict:
    """
    Estima costo a partir de longitudes de pregunta y respuesta (aprox 4 chars/token).
    """
    user_tokens = max(10, question_len // 4)
    response_tokens = max(50, answer_len // 4)
    rag_tokens = num_chunks * 100
    return estimate_message_cost(
        rag_context_tokens=rag_tokens,
        user_message_tokens=user_tokens,
        response_tokens=response_tokens,
        cached=cached,
    )
