"""
Router de intención: clasifica el mensaje del usuario con Claude Haiku.
Devuelve: faq | stock_search | soporte_humano | fuera_dominio
Sin LangChain; llamada directa a Anthropic API.
"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

INTENTS = ("faq", "stock_search", "soporte_humano", "fuera_dominio")


def _looks_like_stock_query(msg: str) -> bool:
    """
    Heurística rápida para detectar búsquedas de vehículos sin llamar a Haiku.
    Se dispara cuando el usuario claramente quiere ver carros/camionetas/modelos.
    """
    text = (msg or "").lower()
    if not text:
        return False

    # Palabras que indican intención de buscar/listar stock
    verbos_stock = (
        "tienen", "tiene", "hay", "busco", "buscando", "quiero ver",
        "mostrar", "muestrame", "muéstrame", "que carros hay", "qué carros hay",
        "listar", "lista", "stock", "disponible", "disponibles",
    )
    # Palabras típicas de vehículos/modelos
    palabras_vehiculo = (
        "carro", "carros", "auto", "autos", "vehiculo", "vehículo", "camioneta",
        "camionetas", "suv", "pickup", "4x4", "kia", "hyundai", "toyota",
        "chevrolet", "nissan", "honda", "mazda", "bmw", "mercedes", "audi",
        "picanto", "sportage", "tucson", "hilux", "yaris", "corolla",
    )

    hay_verbo = any(v in text for v in verbos_stock)
    hay_vehiculo = any(w in text for w in palabras_vehiculo)
    return hay_verbo and hay_vehiculo


def _usage_to_dict(usage) -> dict:
    """Extrae input/output/cache del objeto usage de Anthropic."""
    if usage is None:
        return {"input": 0, "output": 0, "cached_read": 0, "cached_creation": 0}
    return {
        "input": getattr(usage, "input_tokens", 0) or 0,
        "output": getattr(usage, "output_tokens", 0) or 0,
        "cached_read": getattr(usage, "cache_read_input_tokens", 0) or 0,
        "cached_creation": getattr(usage, "cache_creation_input_tokens", 0) or 0,
    }


INTENT_EXPLANATIONS = {
    "faq": "Pregunta sobre la plataforma (comisiones, registro, SubasCoins, etc.). Se responde con RAG.",
    "stock_search": "El usuario quiere buscar o listar vehículos. Por ahora mostramos mensaje de próximamente.",
    "soporte_humano": "Pide hablar con un agente o humano. Se responde con contacto.",
    "fuera_dominio": "Tema fuera de VMC Subastas. Se responde con redirección al dominio.",
}


def classify_intent(user_message: str, last_assistant_message: str | None = None) -> str:
    """
    Clasifica la intención del usuario. Devuelve uno de: faq, stock_search, soporte_humano, fuera_dominio.
    Si last_assistant_message está informado, el router considera que el usuario puede estar respondiendo
    a una pregunta del bot (ej. "Si" como respuesta a "¿Ya tienes estos datos?") y clasifica como faq.
    """
    out, _, _, _ = classify_intent_with_debug(user_message, last_assistant_message=last_assistant_message)
    return out


def classify_intent_with_debug(
    user_message: str,
    last_assistant_message: str | None = None,
) -> tuple[str, int, dict, str]:
    """
    Igual que classify_intent pero retorna (intent, latency_ms, tokens_dict, explanation).
    Si last_assistant_message está informado, se incluye en el prompt para no clasificar
    respuestas cortas (sí, no, ok, dale) como fuera_dominio cuando el usuario responde al bot.
    """
    import time
    msg = (user_message or "").strip()
    if not msg:
        return "faq", 0, _usage_to_dict(None), INTENT_EXPLANATIONS["faq"]

    # Heurística local: si el mensaje claramente es una búsqueda de vehículos,
    # marcamos stock_search sin llamar a Haiku (más barato y más robusto).
    if _looks_like_stock_query(msg):
        return "stock_search", 0, _usage_to_dict(None), INTENT_EXPLANATIONS["stock_search"]

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return "faq", 0, _usage_to_dict(None), INTENT_EXPLANATIONS["faq"]

    prompt = """Eres un clasificador de intención para el chatbot de VMC Subastas (plataforma de subastas de vehículos en Perú). Clasifica el mensaje del usuario en exactamente UNA de estas categorías:

- faq: preguntas sobre registro, cuenta, SubasCoins, billetera, consignación, ofertas En Vivo o Negociable, visitas, comisiones, proceso de compra, plazos, soporte. Cualquier duda sobre cómo funciona la plataforma. También cuando el usuario responde con algo corto (sí, no, ok, claro, dale, ya tengo, etc.) a una pregunta que el asistente acaba de hacer sobre VMC: en ese caso es faq para que la conversación continúe.
- stock_search: el usuario quiere buscar, ver o listar vehículos/autos/camionetas en subasta o disponibles (ej. "tienen hilux", "qué carros hay", "busco una camioneta").
- soporte_humano: pide hablar con una persona, agente, ejecutivo, o está molesto y quiere escalar (ej. "quiero hablar con alguien", "me atiende un humano", "no me sirve esto").
- fuera_dominio: el mensaje no tiene que ver con VMC Subastas (otro tema, saludos genéricos sin pregunta, chiste, etc.). No uses fuera_dominio si el usuario está claramente respondiendo a una pregunta del asistente sobre VMC.

Responde SOLO con una palabra: faq, stock_search, soporte_humano o fuera_dominio. Nada más.
"""

    if last_assistant_message and (last_assistant_message or "").strip():
        prompt += '\nContexto: El último mensaje del asistente fue: "' + (last_assistant_message or "").strip()[:500] + '". El usuario ahora dice: "' + msg[:200] + '". Si el usuario está respondiendo a esa pregunta del asistente (respuesta corta), clasifica como faq.\n\nMensaje del usuario a clasificar: ' + msg
    else:
        prompt += "\nMensaje del usuario: " + msg

    try:
        from dotenv import load_dotenv
        load_dotenv(ROOT / ".env")
        from anthropic import Anthropic
        client = Anthropic(api_key=api_key)
        t0 = time.perf_counter()
        response = client.beta.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=20,
            messages=[{"role": "user", "content": prompt}],
            betas=["prompt-caching-2024-07-31"],
            cache_control={"type": "ephemeral"},
        )
        latency_ms = int((time.perf_counter() - t0) * 1000)
        usage = getattr(response, "usage", None)
        tokens = _usage_to_dict(usage)
        block = response.content[0] if response.content else None
        text = (block.text if block and hasattr(block, "text") else str(response.content)).strip().lower()
        for intent in INTENTS:
            if intent in text or text == intent:
                return intent, latency_ms, tokens, INTENT_EXPLANATIONS.get(intent, "")
        return "faq", latency_ms, tokens, INTENT_EXPLANATIONS["faq"]
    except Exception:
        return "faq", 0, _usage_to_dict(None), INTENT_EXPLANATIONS["faq"]
