"""
Crawl del inventario público de vehículos con Firecrawl.

Punto de entrada por defecto: https://www.vmcsubastas.com
Se siguen enlaces internos y más adelante el parser se queda solo con las URLs
que contienen "/oferta/" (páginas de oferta individual).

Opcionalmente se puede sobreescribir la URL inicial con la variable de entorno
INVENTORY_URL (por ejemplo una página de listado de ofertas).

Este script:
- Scrapea la URL indicada (o el sitio principal por defecto) con Firecrawl.
- Guarda el resultado bruto en data/raw/inventory_raw.json para que otras partes
  del sistema (ej. un parser más específico o buscar_vehiculo) lo puedan procesar.

Uso (desde la raíz del proyecto vmc-bot):
  python -m src.ingest.crawl_inventory
"""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

OUTPUT_PATH = ROOT / "data" / "raw" / "inventory_raw.json"


def main() -> None:
    # Punto de entrada: INVENTORY_URL si existe, si no, el sitio principal.
    url = os.getenv("INVENTORY_URL", "").strip() or "https://www.vmcsubastas.com"

    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        print("ERROR: FIRECRAWL_API_KEY no está en .env")
        sys.exit(1)

    try:
        from firecrawl import Firecrawl
        from firecrawl.types import ScrapeOptions
    except ImportError:
        print("Instala firecrawl-py: pip install firecrawl-py")
        sys.exit(1)

    client = Firecrawl(api_key=api_key)
    print(f"Scrapeando inventario desde {url} ...")

    # Para inventario usamos crawl (por si hay varias páginas o enlaces relacionados)
    result = client.crawl(
        url,
        limit=100,  # límite más alto para cubrir más ofertas
        scrape_options=ScrapeOptions(formats=["markdown", "html", "links"]),
        poll_interval=15,
    )

    if not result or not getattr(result, "data", None):
        print("No se obtuvieron datos de inventario.")
        sys.exit(1)

    # Por ahora guardamos la salida "tal cual" como base para un parser posterior.
    # Un paso siguiente será definir un extractor específico de vehículos según la
    # estructura real de vmcsubastas.com.
    pages = []
    for doc in result.data:
        meta = getattr(doc, "metadata", None) or {}
        markdown = getattr(doc, "markdown", None) or ""
        html = getattr(doc, "html", None) or ""
        url_doc = (
            getattr(meta, "get", lambda k, d=None: None)("sourceURL", None)
            if hasattr(meta, "get")
            else getattr(meta, "sourceURL", None)
        )
        if not url_doc and isinstance(meta, dict):
            url_doc = meta.get("sourceURL") or meta.get("url")
        pages.append(
            {
                "url": url_doc,
                "markdown": markdown,
                "html": html,
            }
        )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "source": url,
                "pages": pages,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(f"Listo. Inventario bruto guardado en {OUTPUT_PATH}")


if __name__ == "__main__":
    main()

