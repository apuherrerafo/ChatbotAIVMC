"""
Validación de respuestas para WhatsApp (subagente Validador WhatsApp).
Comprueba largo, formato compatible y emite issues para log/deploy.
"""


def validate_length(response: str) -> dict:
    """Largo del mensaje: ideal ≤500, aceptable ≤1000, >1000 dividir."""
    char_count = len(response)
    word_count = len(response.split())
    status = "ok" if char_count <= 1000 else "too_long"
    suggestion = "Dividir en múltiples mensajes" if char_count > 1000 else None
    if char_count < 20 and char_count > 0:
        status = "too_short"
        suggestion = "Demasiado corto (excepto confirmaciones)"
    return {
        "chars": char_count,
        "words": word_count,
        "status": status,
        "suggestion": suggestion,
    }


def validate_format(response: str) -> list[str]:
    """Formato compatible con WhatsApp: sin ##, ```, tablas markdown, muchos \\n."""
    issues = []
    if "##" in response or "###" in response:
        issues.append("Headers markdown (## ###) no se renderizan en WhatsApp")
    if "```" in response:
        issues.append("Bloques de código no se renderizan en WhatsApp")
    if "|" in response and "---" in response:
        issues.append("Tablas markdown no se renderizan en WhatsApp")
    if response.count("\n") > 8:
        issues.append("Demasiados saltos de línea, se ve espaciado raro")
    return issues


def validate_response(response: str) -> dict:
    """Ejecuta validación de largo y formato. Para log y reportes."""
    length_result = validate_length(response)
    format_issues = validate_format(response)
    return {
        "length": length_result,
        "format_issues": format_issues,
        "ok": length_result["status"] == "ok" and len(format_issues) == 0,
    }
