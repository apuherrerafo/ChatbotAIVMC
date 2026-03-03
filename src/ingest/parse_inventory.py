"""
Parser de inventario: convierte data/raw/inventory_raw.json en un JSON normalizado
data/processed/inventory.json que luego se usa para búsquedas de vehículos.

Como la estructura HTML real de vmcsubastas.com puede cambiar, este parser se
limita inicialmente a:
- Recorrer las páginas scrapeadas por crawl_inventory.
- Para cada página, crear una "entrada de inventario" con:
  - id (secuencial)
  - url
  - title (primer heading o una línea inicial)
  - snippet (primeros caracteres de markdown)
  - raw_markdown (texto completo)

Luego, la búsqueda de vehículos aplicará filtros de texto sobre estos campos.
Más adelante se puede especializar este parser cuando se conozca mejor el HTML.

Uso (desde raíz vmc-bot):
  python -m src.ingest.parse_inventory
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

RAW_PATH = ROOT / "data" / "raw" / "inventory_raw.json"
OUTPUT_PATH = ROOT / "data" / "processed" / "inventory.json"


def _extract_title(markdown: str, html: str) -> str:
    """
    Intenta obtener un título representativo:
    - Primero un heading del markdown (#, ##, ###)
    - Luego el <title> del HTML
    - Finalmente, una línea no vacía del markdown o del HTML plano.
    """
    if markdown:
        for line in markdown.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("#"):
                return stripped.lstrip("#").strip()
    # Intentar <title> del HTML
    if html:
        m = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
        if m:
            return re.sub(r"\s+", " ", m.group(1)).strip()
    # Fallback: primera línea de markdown con contenido
    if markdown:
        for line in markdown.splitlines():
            stripped = line.strip()
            if len(stripped) > 10:
                return stripped[:120]
    # Fallback: algo de texto plano del HTML
    if html:
        text = _html_to_text(html)
        if text:
            return text[:120]
    return ""


def _html_to_text(html: str) -> str:
    """Convierte HTML a texto plano muy simple (quita etiquetas)."""
    if not html:
        return ""
    # Quitar scripts y estilos
    html = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.DOTALL | re.IGNORECASE)
    # Quitar etiquetas
    text = re.sub(r"<[^>]+>", " ", html)
    # Colapsar espacios
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _extract_schema_vehicle(html: str) -> dict:
    """
    Intenta extraer un objeto de schema.org (JSON-LD) del HTML que describa
    el vehículo/oferta. Busca <script type="application/ld+json"> y devuelve
    el primer objeto con "@type" Product/Vehicle o similar.
    """
    if not html:
        return {}
    scripts = re.findall(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    for raw in scripts:
        try:
            data = json.loads(raw.strip())
        except Exception:
            continue
        candidates = []
        if isinstance(data, list):
            candidates = data
        else:
            candidates = [data]
        for obj in candidates:
            if not isinstance(obj, dict):
                continue
            t = obj.get("@type") or obj.get("type")
            if not t:
                continue
            t_lower = str(t).lower()
            if "vehicle" in t_lower or "product" in t_lower or "offer" in t_lower:
                return obj
    return {}


def main() -> None:
    if not RAW_PATH.exists():
        print(f"No existe {RAW_PATH}. Ejecuta antes crawl_inventory.py")
        sys.exit(1)

    with RAW_PATH.open(encoding="utf-8") as f:
        data = json.load(f)

    pages = data.get("pages", []) or []
    inventory = []
    vid = 0
    for doc in pages:
        url = (doc.get("url") or "").strip()
        markdown = (doc.get("markdown") or "").strip()
        html = (doc.get("html") or "").strip()
        if not (url or markdown or html):
            continue
        # Solo considerar URLs que parezcan ser ofertas individuales
        if "/oferta/" not in url:
            continue
        schema = _extract_schema_vehicle(html)
        brand = ""
        model = ""
        year = ""
        # Campos típicos de schema.org para vehículos/productos
        if schema:
            b = schema.get("brand")
            if isinstance(b, dict):
                brand = b.get("name") or ""
            elif isinstance(b, str):
                brand = b
            model = schema.get("model") or schema.get("name") or ""
            year = str(schema.get("vehicleModelDate") or schema.get("modelDate") or "")

        vid += 1
        title = _extract_title(markdown, html) or model or url
        snippet = markdown[:400] if markdown else _html_to_text(html)[:400]
        search_text = " ".join(
            [
                title.lower(),
                brand.lower(),
                model.lower(),
                year.lower(),
                (snippet or "").lower(),
                (markdown or "").lower(),
                _html_to_text(html).lower(),
            ]
        )
        inventory.append(
            {
                "id": f"v{vid}",
                "url": url,
                "title": title,
                "snippet": snippet,
                "raw_markdown": markdown,
                "search_text": search_text,
                "brand": brand,
                "model": model,
                "year": year,
            }
        )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "source": data.get("source", ""),
                "total": len(inventory),
                "vehicles": inventory,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(f"Listo. {len(inventory)} entradas de inventario guardadas en {OUTPUT_PATH}")


if __name__ == "__main__":
    main()

