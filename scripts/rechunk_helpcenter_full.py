"""
Rechunkea todo el Centro de Ayuda desde data/raw/text/ y data/raw/images_extracted/,
asigna temas alineados al golden (Comisión, Devolución de saldo, Visitas, etc.),
fusiona con los chunks existentes y actualiza data/processed/chunks.json.
Luego hay que ejecutar: python -m src.rag.embed (upsert a Pinecone namespace helpcenter).

Uso: python scripts/rechunk_helpcenter_full.py
"""
import re
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

TEXT_DIR = ROOT / "data" / "raw" / "text"
IMAGES_EXTRACTED_DIR = ROOT / "data" / "raw" / "images_extracted"
CHUNKS_PATH = ROOT / "data" / "processed" / "chunks.json"
MAX_CHUNK_CHARS = 1200
BASE_URL = "https://ayuda.vmcsubastas.com/es"


def _clean_markdown(md: str) -> str:
    if not md or not md.strip():
        return ""
    lines = md.split("\n")
    skip_patterns = [
        r"^\[Ir al contenido principal\]",
        r"^\[Todas las colecciones\]",
        r"^\[Centro de Ayuda Comprador\]",
        r"^\[La billetera\]",
        r"^\[La consignación\]",
        r"^\[La oferta",
        r"^\[Las visitas\]",
        r"^\[El registro\]",
        r"^\[Lo más consultado\]",
        r"^\[SubasTour\]",
        r"^Escrito por ",
        r"^Actualizado hace ",
        r"^Por Silvana",
        r"^¿Ha quedado contestada tu pregunta",
        r"^😞😐😃",
        r"^!\[\]\(https?://",
    ]
    out = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            out.append("")
            continue
        if any(re.match(p, stripped, re.I) for p in skip_patterns):
            continue
        if stripped.startswith("[") and "](http" in stripped and not stripped.startswith("#"):
            if len(stripped) <= 100:
                continue
        out.append(line)
    text = "\n".join(out)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _extract_url_and_title(md: str) -> tuple[str, str]:
    url, title = "", ""
    for line in md.split("\n")[:15]:
        if line.startswith("URL:"):
            url = line.replace("URL:", "").strip()
        if line.startswith("# ") and "Centro de Ayuda" not in line:
            title = line.lstrip("# ").strip()
            if "|" in title:
                title = title.split("|")[0].strip()
            if title:
                break
    return url, title


def _split_by_headers(md: str) -> list[tuple[str, str]]:
    lines = md.split("\n")
    content_start = 0
    for i, line in enumerate(lines):
        if line.strip() == "---" and i > 0:
            content_start = i + 1
            break
    body = "\n".join(lines[content_start:])
    body = _clean_markdown(body)
    if not body:
        return []

    sections = re.split(r"\n(?=## )", body)
    result = []
    for block in sections:
        block = block.strip()
        if not block or len(block) < 30:
            continue
        if block.startswith("## "):
            first_line, _, rest = block.partition("\n")
            section_title = first_line.replace("##", "").strip()
            content = rest.strip()
        else:
            section_title = ""
            content = block
        if not content:
            continue
        if len(content) > MAX_CHUNK_CHARS and "### " in content:
            subblocks = re.split(r"\n(?=### )", content)
            for sub in subblocks:
                sub = sub.strip()
                if len(sub) < 25:
                    continue
                if sub.startswith("### "):
                    st, _, co = sub.partition("\n")
                    result.append((st.replace("###", "").strip(), co.strip()))
                else:
                    result.append((section_title, sub))
        else:
            result.append((section_title or "Contenido", content))
    if not result and body.strip():
        result.append(("Contenido", body.strip()))
    return result


def _has_numeric_data(text: str) -> bool:
    lower = text.lower()
    if not re.search(r"\d", text):
        return False
    keywords = ["s/.", "s/ ", "comisión", "comisiones", "precio", "plazo", "porcentaje", "%", "soles", "días", "dólares"]
    return any(k in lower for k in keywords)


def slug_to_source_url(slug: str) -> str:
    """Construye la URL del Centro de Ayuda a partir del nombre de archivo (slug)."""
    if slug.startswith("articles_"):
        return f"{BASE_URL}/articles/{slug[9:]}"
    if slug.startswith("collections_"):
        return f"{BASE_URL}/collections/{slug[12:]}"
    if slug.startswith("terms_") or slug.startswith("https_"):
        return f"{BASE_URL}/"
    return f"{BASE_URL}/"


def build_chunks_from_md(path: Path, slug: str, topic: str, source_url: str, doc_title: str) -> list[dict]:
    raw = path.read_text(encoding="utf-8")
    if not doc_title:
        _, doc_title = _extract_url_and_title(raw)
    sections = _split_by_headers(raw)
    chunks = []
    for section_title, content in sections:
        if len(content) < 25:
            continue
        text = f"{doc_title}\n\n{section_title}\n\n{content}" if section_title != "Contenido" else f"{doc_title}\n\n{content}"
        chunks.append({
            "text": text,
            "topic": topic,
            "source_url": source_url,
            "source_title": doc_title,
            "section": section_title,
            "has_numeric_data": _has_numeric_data(content),
        })
    if not chunks:
        cleaned = _clean_markdown(raw)
        if len(cleaned) > 50:
            chunks.append({
                "text": f"{doc_title}\n\n{cleaned}" if doc_title else cleaned,
                "topic": topic,
                "source_url": source_url,
                "source_title": doc_title,
                "section": "Contenido",
                "has_numeric_data": _has_numeric_data(cleaned),
            })
    return chunks


def main():
    from src.ingest.taxonomy import topic_from_slug

    CHUNKS_PATH.parent.mkdir(parents=True, exist_ok=True)

    # 1) Cargar chunks existentes (para no eliminarlos)
    existing_chunks = []
    if CHUNKS_PATH.exists():
        with open(CHUNKS_PATH, encoding="utf-8") as f:
            data = json.load(f)
        existing_chunks = data.get("chunks", [])
    existing_ids = {c["id"] for c in existing_chunks}

    # 2) Rechunkear desde text/ e images_extracted/
    all_md_paths = []
    if TEXT_DIR.exists():
        all_md_paths.extend(sorted(TEXT_DIR.glob("*.md")))
    if IMAGES_EXTRACTED_DIR.exists():
        all_md_paths.extend(sorted(IMAGES_EXTRACTED_DIR.glob("*.md")))

    # Dedup por (slug, source) para no duplicar mismo artículo de text e images_extracted
    seen_slugs = set()
    new_chunk_list = []
    next_id = 1
    for path in all_md_paths:
        slug = path.stem
        if slug in seen_slugs:
            continue
        seen_slugs.add(slug)
        topic = topic_from_slug(slug)
        source_url = slug_to_source_url(slug)
        raw = path.read_text(encoding="utf-8")
        _, doc_title = _extract_url_and_title(raw)
        if not doc_title and path.name.startswith("articles_"):
            doc_title = slug.replace("articles_", "").replace("-", " ").title()
        chunk_dicts = build_chunks_from_md(path, slug, topic, source_url, doc_title or "")
        for ch in chunk_dicts:
            chunk_id = f"hc_{next_id}"
            next_id += 1
            ch["id"] = chunk_id
            new_chunk_list.append(ch)

    # 3) Fusionar: existentes + nuevos
    merged = existing_chunks + new_chunk_list
    total = len(merged)

    with open(CHUNKS_PATH, "w", encoding="utf-8") as f:
        json.dump({"chunks": merged, "total": total}, f, ensure_ascii=False, indent=2)

    topics_count = {}
    for c in merged:
        t = c.get("topic", "General")
        topics_count[t] = topics_count.get(t, 0) + 1

    print(f"Chunks existentes: {len(existing_chunks)}")
    print(f"Chunks nuevos (rechunk): {len(new_chunk_list)}")
    print(f"Total en {CHUNKS_PATH}: {total}")
    print("Por tema:", topics_count)
    print("\nSiguiente paso: python -m src.rag.embed   (upsert a Pinecone namespace helpcenter)")


if __name__ == "__main__":
    main()
