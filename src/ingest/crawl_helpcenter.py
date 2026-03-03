"""
Crawl del Centro de Ayuda (ayuda.vmcsubastas.com) con Firecrawl.
Guarda resultado en data/raw/helpcenter_crawl.json y clasifica cada URL.
Uso: python -m src.ingest.crawl_helpcenter [--limit N]
"""
import os
import sys
import json
from pathlib import Path

# Cargar .env desde la raíz del proyecto (vmc-bot)
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

FIRECRAWL_KEY = os.getenv("FIRECRAWL_API_KEY")
if not FIRECRAWL_KEY:
    print("ERROR: FIRECRAWL_API_KEY no está en .env")
    sys.exit(1)

HELPCENTER_URL = "https://ayuda.vmcsubastas.com"
OUTPUT_PATH = ROOT / "data" / "raw" / "helpcenter_crawl.json"


def clasificar_pagina(doc) -> str:
    """Clasifica si la página tiene texto útil, solo imágenes, o mixto."""
    markdown = (doc.markdown or "") if hasattr(doc, "markdown") else ""
    meta = (doc.metadata or {}) if hasattr(doc, "metadata") else {}
    # Si hay poco texto en markdown, asumimos que es imagen/infografía
    texto_len = len(markdown.strip())
    if texto_len < 80:
        return "solo_imagenes"
    if texto_len < 300:
        return "mixto"
    return "tiene_texto"


def main():
    limit = 30
    if "--limit" in sys.argv:
        i = sys.argv.index("--limit")
        if i + 1 < len(sys.argv):
            limit = int(sys.argv[i + 1])

    try:
        from firecrawl import Firecrawl
        from firecrawl.types import ScrapeOptions
    except ImportError:
        print("Instala firecrawl-py: pip install firecrawl-py")
        sys.exit(1)

    firecrawl = Firecrawl(api_key=FIRECRAWL_KEY)
    print(f"Crawleando {HELPCENTER_URL} (limit={limit})... Puede tardar unos minutos.")
    result = firecrawl.crawl(
        HELPCENTER_URL,
        limit=limit,
        scrape_options=ScrapeOptions(formats=["markdown"]),
        poll_interval=15,
    )

    if not result or not getattr(result, "data", None):
        print("No se obtuvieron datos. Status:", getattr(result, "status", result))
        sys.exit(1)

    def _get(obj, key, default=""):
        if obj is None:
            return default
        if hasattr(obj, "get"):
            return obj.get(key, default)
        return getattr(obj, key, default) or getattr(obj, key.replace("sourceURL", "source_url"), default)

    pages = []
    for doc in result.data:
        meta = getattr(doc, "metadata", None)
        markdown = getattr(doc, "markdown", None) or ""
        url = _get(meta, "sourceURL") or _get(meta, "source_url") or _get(meta, "url") or ""
        title = _get(meta, "title") or ""
        tipo = clasificar_pagina(doc)
        pages.append({
            "url": url,
            "title": title,
            "tipo": tipo,
            "markdown_length": len(markdown),
            "markdown_preview": markdown[:500] + "..." if len(markdown) > 500 else markdown,
        })

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    out = {
        "source": HELPCENTER_URL,
        "limit": limit,
        "status": getattr(result, "status", "unknown"),
        "completed": getattr(result, "completed", 0),
        "total": getattr(result, "total", 0),
        "pages": pages,
    }
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"Listo. {len(pages)} páginas guardadas en {OUTPUT_PATH}")
    tipos = {}
    for p in pages:
        tipos[p["tipo"]] = tipos.get(p["tipo"], 0) + 1
    print("Clasificación:", tipos)


if __name__ == "__main__":
    main()
