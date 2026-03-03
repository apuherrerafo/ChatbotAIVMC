"""
Fuente en tiempo real: scrape de la página SubasPass para precios y planes actuales.
Se usa cuando el usuario pregunta por SubasPass; así la respuesta refleja datos al día.
"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

SUBASPASS_URL = "https://www.vmcsubastas.com/subaspass"


def fetch_subaspass_live() -> tuple[str | None, str]:
    """
    Scrapea la página SubasPass con Firecrawl en tiempo real.
    Devuelve (markdown_text, source_url) o (None, SUBASPASS_URL) si falla.
    """
    try:
        from dotenv import load_dotenv
        load_dotenv(ROOT / ".env")
        api_key = os.getenv("FIRECRAWL_API_KEY")
        if not api_key:
            return None, SUBASPASS_URL
        from firecrawl import Firecrawl
        firecrawl = Firecrawl(api_key=api_key)
        result = firecrawl.scrape(SUBASPASS_URL, formats=["markdown"])
        md = ""
        if result and hasattr(result, "markdown"):
            md = result.markdown or ""
        elif result and isinstance(result, dict):
            md = result.get("markdown", "")
        if not md and hasattr(result, "data"):
            data = getattr(result, "data", None)
            md = getattr(data, "markdown", "") if data else ""
        if md and isinstance(md, str) and md.strip():
            return md.strip(), SUBASPASS_URL
    except Exception:
        pass
    return None, SUBASPASS_URL
