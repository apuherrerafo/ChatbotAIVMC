"""
Rate limit por cliente: 6 mensajes/minuto y 20 mensajes/5 minutos.
Clave por IP; función pura de uso para API de prueba y futura API WhatsApp.
"""
import time
from collections import defaultdict

# Límites por ventana
MAX_REQUESTS_PER_MINUTE = 6
MAX_REQUESTS_PER_5MIN = 20
WINDOW_1MIN_SEC = 60
WINDOW_5MIN_SEC = 300

# Por cliente: lista de timestamps de los últimos requests
_timestamps: dict[str, list[float]] = defaultdict(list)


def check_rate_limit(client_key: str) -> tuple[bool, float | None]:
    """
    Devuelve (permitido, retry_after_sec).
    retry_after_sec es None si está permitido; si no, segundos hasta que se libere una ventana.
    Aplica ambas ventanas: 1 min y 5 min.
    """
    now = time.monotonic()
    times = _timestamps[client_key]
    # Eliminar timestamps fuera de la ventana de 5 min
    times[:] = [t for t in times if now - t < WINDOW_5MIN_SEC]

    in_1min = [t for t in times if now - t < WINDOW_1MIN_SEC]
    in_5min = times

    allowed_1min = len(in_1min) < MAX_REQUESTS_PER_MINUTE
    allowed_5min = len(in_5min) < MAX_REQUESTS_PER_5MIN

    if allowed_1min and allowed_5min:
        times.append(now)
        return True, None

    # Calcular cuánto esperar para que se libere al menos un hueco en cada ventana que lo necesite
    wait_1min = 0.0
    wait_5min = 0.0
    if not allowed_1min and in_1min:
        oldest = min(in_1min)
        wait_1min = max(0.0, WINDOW_1MIN_SEC - (now - oldest))
    if not allowed_5min and in_5min:
        oldest = min(in_5min)
        wait_5min = max(0.0, WINDOW_5MIN_SEC - (now - oldest))

    retry_after = max(wait_1min, wait_5min)
    return False, round(retry_after, 1)
