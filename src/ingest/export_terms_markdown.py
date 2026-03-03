"""
Scrapea la página de Condiciones y Términos de VMC Subastas y guarda el markdown
en data/raw/text/terms_condiciones_y_terminos.md para que entre al pipeline de
chunks (src.rag.chunks) igual que los artículos del Centro de Ayuda.

Uso (desde la raíz del proyecto vmc-bot):
  python -m src.ingest.export_terms_markdown
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

OUTPUT_DIR = ROOT / "data" / "raw" / "text"
TERMS_URL = "https://www.vmcsubastas.com/condiciones-y-terminos"
TERMS_TITLE = "Condiciones y Términos de Uso | VMC Subastas"


def main() -> None:
    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        print("FIRECRAWL_API_KEY no está en .env")
        sys.exit(1)

    try:
        from firecrawl import Firecrawl
    except ImportError:
        print("Instala firecrawl-py: pip install firecrawl-py")
        sys.exit(1)

    client = Firecrawl(api_key=api_key)
    print(f"Scrapeando Condiciones y Términos desde {TERMS_URL} ...")

    result = client.scrape(TERMS_URL, formats=["markdown"])
    md = ""
    if result and hasattr(result, "markdown"):
        md = result.markdown or ""
    elif result and isinstance(result, dict):
        md = result.get("markdown", "")
    if not md and hasattr(result, "data"):
        data = getattr(result, "data", None)
        md = getattr(data, "markdown", "") if data else ""

    if not md or not isinstance(md, str) or not md.strip():
        print("No se obtuvo markdown de Condiciones y Términos.")
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / "terms_condiciones_y_terminos.md"
    with out_path.open("w", encoding="utf-8") as f:
        f.write(f"# {TERMS_TITLE}\n\nURL: {TERMS_URL}\n\n---\n\n{md.strip()}\n")

    print(f"Listo. Condiciones y Términos guardados en {out_path}")


if __name__ == "__main__":
    main()

