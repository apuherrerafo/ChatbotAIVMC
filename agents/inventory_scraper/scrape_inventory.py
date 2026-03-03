"""
agents/inventory_scraper/scrape_inventory.py
---------------------------------------------
Script ejecutable para actualizar el inventario de vehículos VMC.

Usa src/core/scraper.py con fallback en cascada:
  1. Playwright (gratis)
  2. Firecrawl (con créditos)
  3. Último JSON guardado
  4. Mensaje amigable si todo falla

Output: data/raw/inventory.json

Uso:
  python agents/inventory_scraper/scrape_inventory.py
"""

import json
from pathlib import Path
from datetime import datetime, timezone

from src.core.scraper import scrape_inventario, respuesta_sin_inventario
from src.core.logger import log_event, log_error

# ---------------------------------------------------------------------------
# 1. Rutas
# ---------------------------------------------------------------------------
_ROOT           = Path(__file__).resolve().parents[2]
_INVENTORY_FILE = _ROOT / "data" / "raw" / "inventory.json"
_INVENTORY_FILE.parent.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# 2. Estructurar vehículos
#    Normaliza los datos crudos al schema definido en AGENTS.md
# ---------------------------------------------------------------------------
def estructurar_vehiculos(vehiculos_raw: list[dict], fuente: str) -> list[dict]:
    """
    Normaliza los datos crudos al schema estándar de inventario.

    Args:
        vehiculos_raw: Lista cruda del scraper.
        fuente:        Herramienta que produjo los datos.

    Returns:
        Lista de vehículos con schema normalizado.
    """
    ahora      = datetime.now(timezone.utc).isoformat()
    resultado  = []

    for i, v in enumerate(vehiculos_raw):
        vehiculo = {
            "id":          v.get("id", f"vmc_{i+1:04d}"),
            "marca":       v.get("marca", ""),
            "modelo":      v.get("modelo", ""),
            "año":         v.get("año", 0),
            "precio_base": v.get("precio_base", 0.0),
            "estado":      v.get("estado", "disponible"),
            "tipo":        v.get("tipo", ""),
            "url":         v.get("url", ""),
            "imagen_url":  v.get("imagen_url", ""),
            "ubicacion":   v.get("ubicacion", ""),
            "titulo":      v.get("titulo", ""),
            "precio_raw":  v.get("precio", ""),
            "scraped_at":  ahora,
            "fuente":      fuente,
        }
        resultado.append(vehiculo)

    return resultado


# ---------------------------------------------------------------------------
# 3. Guardar inventario
# ---------------------------------------------------------------------------
def guardar_inventario(vehiculos: list[dict], fuente: str) -> None:
    """
    Guarda el inventario estructurado en data/raw/inventory.json.
    Incluye metadata del scraping para trazabilidad.
    """
    data = {
        "metadata": {
            "scraped_at":       datetime.now(timezone.utc).isoformat(),
            "fuente":           fuente,
            "total_vehiculos":  len(vehiculos),
            "aviso":            "Información actualizada al momento del scraping. "
                                "La disponibilidad puede cambiar. "
                                "Verifica en vmcsubastas.com.",
        },
        "vehiculos": vehiculos,
    }

    with open(_INVENTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    log_event(
        "inventario_guardado",
        fuente=fuente,
        total=len(vehiculos),
        path=str(_INVENTORY_FILE),
    )


# ---------------------------------------------------------------------------
# 4. Reporte de resultado
# ---------------------------------------------------------------------------
def imprimir_resultado(vehiculos: list[dict] | None, fuente: str) -> None:
    """Imprime el resultado del scraping en consola."""
    print(f"\n=== SCRAPER DE INVENTARIO VMC ===")
    print(f"Fecha: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC\n")

    if vehiculos is None:
        print(f"RESULTADO: Sin datos disponibles")
        print(f"MENSAJE AL USUARIO:")
        print(f"  {respuesta_sin_inventario()}")
    else:
        iconos = {
            "playwright": "Playwright (gratis)",
            "firecrawl":  "Firecrawl (creditos)",
            "fallback":   "Ultimo JSON guardado",
        }
        print(f"RESULTADO: {len(vehiculos)} vehiculos encontrados")
        print(f"FUENTE:    {iconos.get(fuente, fuente)}")
        print(f"GUARDADO:  {_INVENTORY_FILE}")

        if fuente == "fallback":
            print(f"\nAVISO: Se uso el ultimo inventario guardado.")
            print(f"El inventario puede no estar completamente actualizado.")

    print(f"\n{'='*35}\n")


# ---------------------------------------------------------------------------
# 5. Entry point
# ---------------------------------------------------------------------------
def main():
    print("\nIniciando scraper de inventario VMC...")
    log_event("inventario_scraper_inicio")

    # Ejecutar cascada de scraping
    vehiculos_raw, fuente = scrape_inventario()

    if vehiculos_raw is None:
        # Todo falló — loguear y mostrar mensaje
        log_error(
            "inventario_sin_datos",
            message="Todos los métodos de scraping fallaron.",
        )
        imprimir_resultado(None, fuente)
        return

    # Estructurar y guardar
    vehiculos = estructurar_vehiculos(vehiculos_raw, fuente)
    guardar_inventario(vehiculos, fuente)
    imprimir_resultado(vehiculos, fuente)


if __name__ == "__main__":
    main()