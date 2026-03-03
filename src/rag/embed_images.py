"""
Lee los markdowns transcritos de infografías (data/raw/images_extracted/*.md),
los chunkea por imagen/sección y los sube a Pinecone en el mismo índice y namespace.
Así el RAG puede responder con información que estaba en infografías.

Uso: python -m src.rag.embed_images
"""
import os
import re
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

IMAGES_DIR = ROOT / "data" / "raw" / "images_extracted"
NAMESPACE = "helpcenter"


def chunk_image_markdown(md_path: Path) -> list[dict]:
    """Chunkea un markdown de infografía extraída. Cada ## Imagen N es un chunk."""
    text = md_path.read_text(encoding="utf-8")
    lines = text.split("\n")

    url = ""
    title = ""
    for line in lines:
        if line.startswith("URL:"):
            url = line.replace("URL:", "").strip()
        if line.startswith("# ") and not title:
            title = line.replace("# ", "").strip()

    sections = re.split(r"(?=^## Imagen \d+)", text, flags=re.MULTILINE)
    chunks = []
    for sec in sections:
        sec = sec.strip()
        if not sec or not sec.startswith("## Imagen"):
            continue
        # Limpiar separadores
        clean = sec.replace("---", "").strip()
        if len(clean) < 30:
            continue
        slug = md_path.stem
        img_num = re.search(r"Imagen (\d+)", sec)
        img_id = img_num.group(1) if img_num else "0"
        chunk_id = f"img-{slug}-{img_id}"

        has_numeric = bool(re.search(r"S/\.?\s?\d|%|\d+\s*días|\d+\s*horas", clean))

        chunks.append({
            "id": chunk_id,
            "text": clean[:30_000],
            "topic": f"infografía: {title}" if title else "infografía",
            "source_url": url,
            "has_numeric_data": has_numeric,
            "content_type": "image_transcription",
        })
    return chunks


def main():
    api_key = os.getenv("PINECONE_API_KEY")
    index_name = os.getenv("PINECONE_INDEX_NAME", "vmc-bot-rag")
    if not api_key:
        print("Falta PINECONE_API_KEY en .env")
        sys.exit(1)
    if not IMAGES_DIR.exists():
        print(f"No existe {IMAGES_DIR}. Ejecuta antes: python -m src.ingest.extract_images")
        sys.exit(1)

    md_files = sorted(IMAGES_DIR.glob("*.md"))
    if not md_files:
        print("No hay markdowns de infografías para procesar.")
        sys.exit(1)

    all_chunks = []
    for md_path in md_files:
        chunks = chunk_image_markdown(md_path)
        all_chunks.extend(chunks)
        print(f"  {md_path.name}: {len(chunks)} chunk(s)")

    if not all_chunks:
        print("No se generaron chunks.")
        sys.exit(1)

    # Guardar chunks para referencia
    out_json = ROOT / "data" / "processed" / "image_chunks.json"
    out_json.parent.mkdir(parents=True, exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump({"source": "images_extracted", "total": len(all_chunks), "chunks": all_chunks},
                  ensure_ascii=False, indent=2, fp=f)
    print(f"\n{len(all_chunks)} chunks guardados en {out_json}")

    # Subir a Pinecone
    try:
        from pinecone import Pinecone
    except ImportError:
        print("Instala: pip install pinecone")
        sys.exit(1)

    pc = Pinecone(api_key=api_key)
    index = pc.Index(index_name)

    records = []
    for c in all_chunks:
        records.append({
            "id": c["id"],
            "text": c["text"],
            "topic": c["topic"],
            "source_url": c["source_url"],
            "has_numeric_data": c.get("has_numeric_data", False),
        })

    batch_size = 90
    for i in range(0, len(records), batch_size):
        batch = records[i : i + batch_size]
        index.upsert_records(namespace=NAMESPACE, records=batch)
        print(f"Subidos {min(i + batch_size, len(records))}/{len(records)}")

    print(f"\nListo. {len(records)} chunks de infografías en Pinecone ('{index_name}', namespace '{NAMESPACE}').")


if __name__ == "__main__":
    main()
