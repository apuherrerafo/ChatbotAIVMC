"""
Carga chunks desde data/processed/chunks.json y los sube a Pinecone.
Requiere PINECONE_API_KEY y PINECONE_INDEX_NAME en .env.

Si el índice se creó con inferencia integrada (modelo multilingual-e5-large),
solo hay que enviar el campo "text"; Pinecone genera los embeddings.
Si el índice es clásico (solo dimensión), habría que generar embeddings aparte (ver comentarios).
"""
import os
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

CHUNKS_PATH = ROOT / "data" / "processed" / "chunks.json"
NAMESPACE = "helpcenter"


def main():
    api_key = os.getenv("PINECONE_API_KEY")
    index_name = os.getenv("PINECONE_INDEX_NAME", "vmc-bot-rag")
    if not api_key:
        print("Falta PINECONE_API_KEY en .env. Ver docs/PINECONE_CHECKLIST.md")
        sys.exit(1)
    if not CHUNKS_PATH.exists():
        print(f"No existe {CHUNKS_PATH}. Ejecuta antes: python -m src.rag.chunks")
        sys.exit(1)

    with open(CHUNKS_PATH, encoding="utf-8") as f:
        data = json.load(f)
    chunks = data.get("chunks", [])
    if not chunks:
        print("No hay chunks para subir.")
        sys.exit(1)

    try:
        from pinecone import Pinecone
    except ImportError:
        print("Instala: pip install pinecone")
        sys.exit(1)

    pc = Pinecone(api_key=api_key)

    # Crear índice con embedding integrado si no existe
    if not pc.has_index(index_name):
        print(f"Creando índice '{index_name}' con modelo de embedding...")
        pc.create_index_for_model(
            name=index_name,
            cloud="aws",
            region="us-east-1",
            embed={
                "model": "multilingual-e5-large",
                "field_map": {"text": "text"},
            },
        )
        print("Esperando a que el índice esté listo (unos segundos)...")
        import time
        time.sleep(10)
    index = pc.Index(index_name)

    # Registros para índice con inferencia integrada (field_map: text -> embedding).
    # Cada registro: id + campo "text" (nombre según field_map del índice) + campos extra como metadata.
    records = []
    for c in chunks:
        rid = c.get("id", f"c{len(records)+1}")
        text = c.get("text", "").strip()
        if not text:
            continue
        records.append({
            "id": rid,
            "text": text[:30_000],  # límite por documento
            "topic": c.get("topic", ""),
            "source_url": c.get("source_url", ""),
            "has_numeric_data": c.get("has_numeric_data", False),
        })

    # upsert_records para índices con integrated embedding (Pinecone convierte text -> vector).
    batch_size = 96  # límite Pinecone Inference para este índice
    for i in range(0, len(records), batch_size):
        batch = records[i : i + batch_size]
        index.upsert_records(namespace=NAMESPACE, records=batch)
        print(f"Subidos {min(i + batch_size, len(records))}/{len(records)}")

    print(f"Listo. {len(records)} chunks en índice '{index_name}', namespace '{NAMESPACE}'.")


if __name__ == "__main__":
    main()
