"""
Lee data/raw/helpcenter_crawl.json, re-scrapea cada URL con Firecrawl
y guarda el markdown completo en data/raw/text/{slug}.md.
Uso: python -m src.ingest.export_helpcenter_markdown
"""
import os
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

if not os.getenv("FIRECRAWL_API_KEY"):
    print("FIRECRAWL_API_KEY no está en .env")
    sys.exit(1)

CRAWL_JSON = ROOT / "data" / "raw" / "helpcenter_crawl.json"
OUTPUT_DIR = ROOT / "data" / "raw" / "text"


def slug_from_url(url: str) -> str:
    """Extrae un slug seguro para el nombre de archivo."""
    # Quitar dominio y quedarnos con path; reemplazar / por _
    path = url.split("/es/", 1)[-1] if "/es/" in url else url
    path = path.strip("/").replace("/", "_")
    # Solo caracteres seguros
    path = re.sub(r"[^\w\-]", "_", path)[:80]
    return path or "page"


def main():
    if not CRAWL_JSON.exists():
        print(f"No existe {CRAWL_JSON}. Ejecuta antes crawl_helpcenter.py")
        sys.exit(1)

    import json
    with open(CRAWL_JSON, encoding="utf-8") as f:
        data = json.load(f)

    urls = []
    for p in data.get("pages", []):
        u = p.get("url", "").strip()
        if u:
            urls.append((u, p.get("title", "")))

    if not urls:
        print("No hay URLs en el crawl.")
        sys.exit(1)

    try:
        from firecrawl import Firecrawl
    except ImportError:
        print("pip install firecrawl-py")
        sys.exit(1)

    firecrawl = Firecrawl(api_key=os.getenv("FIRECRAWL_API_KEY"))
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Scrapeando {len(urls)} URLs y guardando en {OUTPUT_DIR}...")
    for i, (url, title) in enumerate(urls, 1):
        slug = slug_from_url(url)
        out_path = OUTPUT_DIR / f"{slug}.md"
        if out_path.exists():
            print(f"  [{i}/{len(urls)}] Ya existe {out_path.name}, skip")
            continue
        try:
            result = firecrawl.scrape(url, formats=["markdown"])
            md = ""
            if result and hasattr(result, "markdown"):
                md = result.markdown or ""
            elif result and isinstance(result, dict):
                md = result.get("markdown", "")
            if not md and hasattr(result, "data"):
                md = getattr(result.data, "markdown", "") if result.data else ""
            if md:
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(f"# {title}\n\nURL: {url}\n\n---\n\n{md}")
                print(f"  [{i}/{len(urls)}] {out_path.name}")
            else:
                print(f"  [{i}/{len(urls)}] Sin markdown: {url[:50]}...")
        except Exception as e:
            print(f"  [{i}/{len(urls)}] Error {url[:50]}...: {e}")
        time.sleep(0.5)

    print("Listo.")


if __name__ == "__main__":
    main()
