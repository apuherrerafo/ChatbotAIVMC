"""
Pipeline: Firecrawl → descargar imágenes → Claude Vision → markdown.
Scrapea cada artículo del Centro de Ayuda, extrae imágenes (infografías),
las descarga, las envía a Claude Vision para transcripción y guarda
el resultado como markdown en data/raw/images_extracted/<slug>.md.

Uso: python -m src.ingest.extract_images [--dry-run]

⚠️  DESACTIVADO POR DEFECTO en desarrollo.
    El contenido ya está vectorizado en Pinecone como texto/markdown.
    Solo correr si hay infografías nuevas que no estén en el RAG.
    Para habilitar: setea VISION_INGESTION_ENABLED=true en .env
"""
import os
import re
import sys
import json
import time
import base64
import hashlib
import requests
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

from src.core.budget_guard import check_daily_budget, BudgetExceededError

CRAWL_JSON = ROOT / "data" / "raw" / "helpcenter_crawl.json"
IMAGES_DIR = ROOT / "data" / "raw" / "images_downloaded"
OUTPUT_DIR = ROOT / "data" / "raw" / "images_extracted"

SKIP_PATTERNS = [
    "avatars/",
    "square_128",
    "icon:",
    "favicon",
    "assets/svg/",
]

MIN_IMAGE_BYTES = 5_000  # ignorar imágenes muy pequeñas (iconos)

VISION_PROMPT = """Eres un asistente que transcribe infografías del Centro de Ayuda de VMC Subastas (plataforma de subastas de vehículos en Perú).
Transcribe TODO el contenido visible en esta imagen. Reglas:
1. Si hay texto, transcríbelo textualmente.
2. Si hay tablas, usa formato Markdown de tabla.
3. Si hay pasos numerados, úsalos como lista numerada.
4. Si hay datos numéricos (precios, porcentajes, plazos), transcríbelos EXACTAMENTE como aparecen.
5. Si hay flechas o flujos, descríbelos como pasos secuenciales.
6. No inventes nada que no esté visible en la imagen.
7. Responde en español."""


def slug_from_url(url: str) -> str:
    path = url.split("/es/", 1)[-1] if "/es/" in url else url
    path = path.strip("/").replace("/", "_")
    path = re.sub(r"[^\w\-]", "_", path)[:80]
    return path or "page"


def extract_image_urls(markdown: str) -> list[str]:
    """Extrae URLs de imágenes del markdown, filtrando iconos/avatares."""
    pattern = r"!\[.*?\]\((https?://[^\s\)]+)\)"
    urls = re.findall(pattern, markdown)
    filtered = []
    seen = set()
    for url in urls:
        if any(skip in url for skip in SKIP_PATTERNS):
            continue
        base = url.split("?")[0]
        if base in seen:
            continue
        seen.add(base)
        filtered.append(url)
    return filtered


def download_image(url: str, dest_path: Path) -> bool:
    """Descarga una imagen. Devuelve True si exitoso y tiene tamaño mínimo."""
    if dest_path.exists() and dest_path.stat().st_size >= MIN_IMAGE_BYTES:
        return True
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        if len(resp.content) < MIN_IMAGE_BYTES:
            return False
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        dest_path.write_bytes(resp.content)
        return True
    except Exception as e:
        print(f"    Error descargando: {e}")
        return False


def image_to_base64(path: Path) -> tuple[str, str]:
    """Lee imagen y devuelve (base64, media_type)."""
    data = path.read_bytes()
    b64 = base64.standard_b64encode(data).decode("utf-8")
    ext = path.suffix.lower()
    media_types = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                   ".gif": "image/gif", ".webp": "image/webp"}
    return b64, media_types.get(ext, "image/png")


def transcribe_with_claude(image_path: Path) -> str:
    """Envía imagen a Claude Vision y devuelve la transcripción."""
    from anthropic import Anthropic
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    b64, media_type = image_to_base64(image_path)
    msg = client.beta.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=900,  # reducido de 2048 → 900 (suficiente para transcribir infografías)
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": b64}},
                {"type": "text", "text": VISION_PROMPT},
            ],
        }],
        betas=["prompt-caching-2024-07-31"],
        cache_control={"type": "ephemeral"},
    )
    block = msg.content[0] if msg.content else None
    return block.text.strip() if block and hasattr(block, "text") else ""


def scrape_article_fresh(url: str) -> str | None:
    """Re-scrapea un artículo con Firecrawl para obtener URLs de imágenes frescas."""
    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        return None
    try:
        from firecrawl import Firecrawl
        fc = Firecrawl(api_key=api_key)
        result = fc.scrape(url, formats=["markdown"])
        md = ""
        if result and hasattr(result, "markdown"):
            md = result.markdown or ""
        elif result and isinstance(result, dict):
            md = result.get("markdown", "")
        if not md and hasattr(result, "data"):
            md = getattr(result.data, "markdown", "") if result.data else ""
        return md if md else None
    except Exception as e:
        print(f"    Firecrawl error: {e}")
        return None


def process_article(url: str, title: str, dry_run: bool = False) -> dict:
    """Procesa un artículo: scrape → imágenes → Claude Vision → markdown."""
    slug = slug_from_url(url)
    out_path = OUTPUT_DIR / f"{slug}.md"

    if out_path.exists() and out_path.stat().st_size > 100:
        print(f"  Ya procesado: {slug}")
        return {"url": url, "slug": slug, "status": "skipped", "images": 0}

    print(f"  Scrapeando {url[:60]}...")
    md = scrape_article_fresh(url)
    if not md:
        print(f"    Sin markdown, saltando")
        return {"url": url, "slug": slug, "status": "no_markdown", "images": 0}

    img_urls = extract_image_urls(md)
    if not img_urls:
        print(f"    Sin infografías relevantes")
        return {"url": url, "slug": slug, "status": "no_images", "images": 0}

    print(f"    {len(img_urls)} imagen(es) encontrada(s)")
    if dry_run:
        return {"url": url, "slug": slug, "status": "dry_run", "images": len(img_urls)}

    transcriptions = []
    for i, img_url in enumerate(img_urls, 1):
        img_hash = hashlib.md5(img_url.split("?")[0].encode()).hexdigest()[:12]
        ext = ".png"
        for e in [".jpg", ".jpeg", ".gif", ".webp"]:
            if e in img_url.lower():
                ext = e
                break
        img_path = IMAGES_DIR / slug / f"img_{i:02d}_{img_hash}{ext}"

        print(f"    [{i}/{len(img_urls)}] Descargando...")
        if not download_image(img_url, img_path):
            print(f"    [{i}/{len(img_urls)}] Imagen muy pequeña o error, saltando")
            continue

        print(f"    [{i}/{len(img_urls)}] Transcribiendo con Claude Vision...")
        try:
            text = transcribe_with_claude(img_path)
            if text:
                transcriptions.append({"index": i, "text": text, "source_image": img_url.split("?")[0]})
                print(f"    [{i}/{len(img_urls)}] OK ({len(text)} chars)")
            else:
                print(f"    [{i}/{len(img_urls)}] Sin texto extraído")
        except Exception as e:
            print(f"    [{i}/{len(img_urls)}] Error Claude: {e}")
        time.sleep(1)

    if transcriptions:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        parts = [f"# {title}\n", f"URL: {url}\n", f"Fuente: Infografías extraídas con Claude Vision\n", "---\n"]
        for t in transcriptions:
            parts.append(f"## Imagen {t['index']}\n")
            parts.append(t["text"])
            parts.append("\n\n---\n")
        out_path.write_text("\n".join(parts), encoding="utf-8")
        print(f"  Guardado: {out_path.name} ({len(transcriptions)} imagen(es))")

    return {"url": url, "slug": slug, "status": "done", "images": len(transcriptions)}


def get_article_urls() -> list[tuple[str, str]]:
    """Obtiene URLs de artículos (no colecciones) del crawl."""
    if not CRAWL_JSON.exists():
        print(f"No existe {CRAWL_JSON}. Ejecuta crawl_helpcenter.py primero.")
        sys.exit(1)
    with open(CRAWL_JSON, encoding="utf-8") as f:
        data = json.load(f)
    urls = []
    for p in data.get("pages", []):
        url = p.get("url", "").strip()
        title = p.get("title", "").strip()
        if not url:
            continue
        if "/articles/" in url:
            urls.append((url, title))
    return urls


def main():
    dry_run = "--dry-run" in sys.argv

    # BLOQUEO POR DEFECTO: Vision solo corre si está explícitamente habilitado.
    # El contenido ya está vectorizado en Pinecone como texto/markdown.
    # Para habilitar: VISION_INGESTION_ENABLED=true en .env
    if os.getenv("VISION_INGESTION_ENABLED", "false").lower() != "true":
        print("[BLOCKED] extract_images.py desactivado.")
        print("  El contenido del Centro de Ayuda ya está en Pinecone como texto.")
        print("  Solo correr si hay infografías NUEVAS que no estén en el RAG.")
        print("  Para habilitar: agrega VISION_INGESTION_ENABLED=true en .env")
        sys.exit(0)

    # Guard de presupuesto diario — Vision es la llamada más cara del proyecto.
    try:
        check_daily_budget(limit_usd=3.0)
    except BudgetExceededError as e:
        print(f"[BUDGET] {e}")
        sys.exit(1)

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Falta ANTHROPIC_API_KEY en .env (necesario para Claude Vision)")
        sys.exit(1)

    if not os.getenv("FIRECRAWL_API_KEY"):
        print("Falta FIRECRAWL_API_KEY en .env (necesario para re-scrapear con URLs frescas)")
        sys.exit(1)

    articles = get_article_urls()
    print(f"\n{'[DRY RUN] ' if dry_run else ''}Procesando {len(articles)} artículos del Centro de Ayuda\n")

    results = []
    for i, (url, title) in enumerate(articles, 1):
        print(f"\n[{i}/{len(articles)}] {title[:60]}")
        r = process_article(url, title, dry_run=dry_run)
        results.append(r)
        if not dry_run and r["status"] == "done":
            time.sleep(2)

    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    done    = [r for r in results if r["status"] == "done"]
    skipped = [r for r in results if r["status"] == "skipped"]
    no_img  = [r for r in results if r["status"] in ("no_images", "no_markdown")]
    total_imgs = sum(r["images"] for r in results)
    print(f"  Procesados:  {len(done)}")
    print(f"  Ya existían: {len(skipped)}")
    print(f"  Sin imágenes: {len(no_img)}")
    print(f"  Total imágenes transcritas: {total_imgs}")
    if done:
        print(f"  Resultados en: {OUTPUT_DIR}")

    log_path = ROOT / "data" / "raw" / "images_extraction_log.json"
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(results, ensure_ascii=False, indent=2, fp=f)
    print(f"  Log: {log_path}")


if __name__ == "__main__":
    main()