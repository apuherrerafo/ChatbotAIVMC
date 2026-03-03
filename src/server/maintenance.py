"""
Tareas de mantenimiento automático del RAG / calidad de contenido.

La idea es que el servidor (el "bot") ejecute periódicamente:
- Verificación de contenido crítico (Firecrawl)
- Refresh del RAG desde el Centro de Ayuda
- Evaluación con golden dataset + auditoría de contenido

Se controla por variables de entorno:
- AUTO_MAINTENANCE=true         → habilita el loop en segundo plano
- MAINT_VERIFY_INTERVAL_HOURS   → cada cuántas horas correr verify_helpcenter_content (default: 24)
- MAINT_REFRESH_INTERVAL_HOURS  → cada cuántas horas correr refresh + eval + audit (default: 168 = 7 días)

Importante: estas tareas se ejecutan en un hilo separado para no bloquear el manejo de requests.
"""
from __future__ import annotations

import os
import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "maintenance.log"


def _log(msg: str) -> None:
    ts = datetime.now(timezone.utc).isoformat()
    line = f"[{ts}] {msg}"
    try:
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        # No romper si el log falla
        pass


def _run(cmd: list[str], desc: str) -> None:
    _log(f"START {desc}: {cmd}")
    try:
        result = subprocess.run(cmd, cwd=ROOT, shell=False)
        _log(f"END {desc}: returncode={result.returncode}")
    except Exception as e:
        _log(f"ERROR {desc}: {e}")


def _maintenance_loop() -> None:
    # Por defecto, el mantenimiento automático está ACTIVADO.
    # Solo se desactiva explícitamente con AUTO_MAINTENANCE=false.
    auto_disabled = os.getenv("AUTO_MAINTENANCE", "").strip().lower() == "false"
    if auto_disabled:
        _log("AUTO_MAINTENANCE=false; no se ejecutarán tareas automáticas.")
        return

    verify_interval_hours = int(os.getenv("MAINT_VERIFY_INTERVAL_HOURS", "24"))
    refresh_interval_hours = int(os.getenv("MAINT_REFRESH_INTERVAL_HOURS", "168"))  # 7 días
    inventory_interval_hours = int(os.getenv("MAINT_INVENTORY_INTERVAL_HOURS", "12"))
    verify_interval = max(1, verify_interval_hours) * 3600
    refresh_interval = max(1, refresh_interval_hours) * 3600
    inventory_interval = max(1, inventory_interval_hours) * 3600

    last_verify = 0.0
    last_refresh = 0.0
    last_inventory = 0.0

    _log(
        f"Loop de mantenimiento iniciado "
        f"(verify cada {verify_interval_hours}h, refresh+eval+audit cada {refresh_interval_hours}h, "
        f"inventory cada {inventory_interval_hours}h)."
    )

    while True:
        now = time.time()

        # Verificación ligera (Firecrawl)
        if now - last_verify >= verify_interval:
            _run(
                [os.getenv("PYTHON_BIN", "python"), "scripts/verify_helpcenter_content.py"],
                "verify_helpcenter_content",
            )
            last_verify = now

        # Refresh completo + evaluación + auditoría
        if now - last_refresh >= refresh_interval:
            _run(
                [
                    os.getenv("PYTHON_BIN", "python"),
                    "scripts/refresh_rag_from_helpcenter.py",
                    "--verify",
                ],
                "refresh_rag_from_helpcenter --verify",
            )
            _run(
                [os.getenv("PYTHON_BIN", "python"), "scripts/eval_golden.py"],
                "eval_golden",
            )
            _run(
                [os.getenv("PYTHON_BIN", "python"), "scripts/audit_rag_content.py"],
                "audit_rag_content",
            )
            last_refresh = now

        # Scraping de inventario (siempre, usando INVENTORY_URL o la raíz por defecto)
        if now - last_inventory >= inventory_interval:
            _run(
                [
                    os.getenv("PYTHON_BIN", "python"),
                    "-m",
                    "src.ingest.crawl_inventory",
                ],
                "crawl_inventory",
            )
            _run(
                [
                    os.getenv("PYTHON_BIN", "python"),
                    "-m",
                    "src.ingest.parse_inventory",
                ],
                "parse_inventory",
            )
            last_inventory = now

        # Dormir un rato antes de volver a chequear (10 minutos)
        time.sleep(600)


def start_background_maintenance() -> None:
    """
    Lanza el hilo de mantenimiento en segundo plano.
    Por defecto está ACTIVADO; se puede desactivar con AUTO_MAINTENANCE=false.
    """
    if os.getenv("AUTO_MAINTENANCE", "").strip().lower() == "false":
        _log("AUTO_MAINTENANCE=false, no se iniciará hilo de mantenimiento.")
        return

    t = threading.Thread(target=_maintenance_loop, name="vmc-maintenance", daemon=True)
    t.start()
    _log("Hilo de mantenimiento lanzado en segundo plano.")

