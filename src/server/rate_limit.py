"""
Rate limit por cliente: máximo 3 mensajes por minuto (regla WhatsApp / monitor costos).
Clave por IP; función pura de uso para API de prueba y futura API WhatsApp.
"""
import time
from collections import defaultdict

# Ventana en segundos y máximo de mensajes
WINDOW_SEC = 60
MAX_REQUESTS = 3

# Por IP: lista de timestamps de los últimos requests (se limpian los > WINDOW_SEC)
_timestamps: dict[str, list[float]] = defaultdict(list)


def check_rate_limit(client_key: str) -> tuple[bool, float | None]:
    """
    Devuelve (permitido, retry_after_sec).
    retry_after_sec es None si está permitido; si no, segundos hasta que expire la ventana.
    """
    now = time.monotonic()
    times = _timestamps[client_key]
    # Eliminar timestamps fuera de la ventana
    times[:] = [t for t in times if now - t < WINDOW_SEC]
    if len(times) >= MAX_REQUESTS:
        oldest = min(times)
        retry_after = max(0.0, WINDOW_SEC - (now - oldest))
        return False, round(retry_after, 1)
    times.append(now)
    return True, None
