"""
Limpieza de markdown del Centro de Ayuda y chunking semántico por tema/sección.
Lee data/raw/text/*.md, limpia, trocea por ## (y ### si hace falta) y guarda chunks.json.
Uso: python -m src.rag.chunks
"""
import re
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

TEXT_DIR = ROOT / "data" / "raw" / "text"
OUTPUT_PATH = ROOT / "data" / "processed" / "chunks.json"
MAX_CHUNK_CHARS = 1200  # Si una sección supera esto, dividir por ###


def _clean_markdown(md: str) -> str:
    """Quita navegación, autor, imágenes sueltas y pie de página."""
    if not md or not md.strip():
        return ""
    lines = md.split("\n")
    out = []
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
        r"^!\[\]\(https?://",  # imagen markdown sola en una línea
    ]
    for line in lines:
        stripped = line.strip()
        if not stripped:
            out.append("")
            continue
        skip = False
        for pat in skip_patterns:
            if re.match(pat, stripped, re.I):
                skip = True
                break
        if skip:
            continue
        # Líneas que son solo un enlace [texto](url) de navegación (sin # delante)
        if stripped.startswith("[") and "](http" in stripped and not stripped.startswith("#"):
            # Mantener enlaces que parecen contenido (ej. enlaces a artículos relacionados con texto largo)
            if len(stripped) > 100:
                out.append(line)
            continue
        out.append(line)
    # Unir y quitar bloques de múltiples líneas vacías
    text = "\n".join(out)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _extract_url_and_title(md: str) -> tuple[str, str]:
    """Extrae URL y título del header del archivo (primeras líneas)."""
    url = ""
    title = ""
    for line in md.split("\n")[:10]:
        if line.startswith("URL:"):
            url = line.replace("URL:", "").strip()
        if line.startswith("# ") and not line.startswith("# SubasCoins") and "Centro de Ayuda" not in line:
            title = line.lstrip("# ").strip()
            if "|" in title:
                title = title.split("|")[0].strip()
    return url, title


def _split_by_headers(md: str) -> list[tuple[str, str]]:
    """Divide el markdown por ## y opcionalmente ###. Devuelve lista de (titulo_seccion, contenido)."""
    # Quitar el primer bloque (título del doc y URL)
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

    # Dividir por ##
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
            # Subdividir por ###
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
    """Heurística: el chunk menciona precios, comisiones o plazos (guardrail financiero)."""
    lower = text.lower()
    if not re.search(r"\d", text):
        return False
    keywords = ["s/.", "s/ ", "comisión", "comisiones", "precio", "plazo", "porcentaje", "%", "soles"]
    return any(k in lower for k in keywords)


def main():
    from src.ingest.taxonomy import topic_from_slug

    TEXT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    chunks = []
    chunk_id = 0
    for path in sorted(TEXT_DIR.glob("*.md")):
        slug = path.stem
        topic = topic_from_slug(slug)
        raw = path.read_text(encoding="utf-8")
        url, doc_title = _extract_url_and_title(raw)
        sections = _split_by_headers(raw)
        if not sections:
            # Un solo chunk con todo el contenido limpio
            cleaned = _clean_markdown(raw)
            if len(cleaned) > 50:
                chunk_id += 1
                chunks.append({
                    "id": f"c{chunk_id}",
                    "text": cleaned,
                    "topic": topic,
                    "source_url": url,
                    "source_title": doc_title,
                    "has_numeric_data": _has_numeric_data(cleaned),
                })
            continue
        for section_title, content in sections:
            if len(content) < 25:
                continue
            chunk_id += 1
            # Incluir título del doc y sección en el texto para contexto
            text = f"{doc_title}\n\n{section_title}\n\n{content}" if section_title != "Contenido" else f"{doc_title}\n\n{content}"
            chunks.append({
                "id": f"c{chunk_id}",
                "text": text,
                "topic": topic,
                "source_url": url,
                "source_title": doc_title,
                "section": section_title,
                "has_numeric_data": _has_numeric_data(content),
            })

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump({"chunks": chunks, "total": len(chunks)}, f, ensure_ascii=False, indent=2)

    print(f"Listo. {len(chunks)} chunks guardados en {OUTPUT_PATH}")
    topics = {}
    for c in chunks:
        topics[c["topic"]] = topics.get(c["topic"], 0) + 1
    print("Por tema:", topics)
    numeric = sum(1 for c in chunks if c.get("has_numeric_data"))
    print(f"Chunks con datos numéricos (guardrail): {numeric}")


if __name__ == "__main__":
    main()
