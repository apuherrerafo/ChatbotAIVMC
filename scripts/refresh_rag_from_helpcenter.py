"""
Refresca el RAG desde el Centro de Ayuda en vivo: crawl → export markdown → chunks → embed.
Usa Firecrawl para obtener el contenido actual de ayuda.vmcsubastas.com y actualiza
Pinecone. Ejecutar periódicamente (cron/scheduler) para que el bot no dé información
desactualizada.

Uso (desde la raíz del proyecto vmc-bot):
  python scripts/refresh_rag_from_helpcenter.py
  python scripts/refresh_rag_from_helpcenter.py --limit 20
  python scripts/refresh_rag_from_helpcenter.py --verify   # al final ejecuta verify_helpcenter_content
"""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Añadir ROOT al path para poder importar src.*
sys.path.insert(0, str(ROOT))

from src.core.budget_guard import check_daily_budget, BudgetExceededError  # PROTECCIÓN BATCH


def run(cmd: list[str], desc: str) -> bool:
    """Ejecuta un comando; devuelve True si salió con 0."""
    print(f"\n--- {desc} ---")
    result = subprocess.run(cmd, cwd=ROOT, shell=False)
    if result.returncode != 0:
        print(f"ERROR: {desc} falló con código {result.returncode}")
        return False
    return True


def main():
    parser = argparse.ArgumentParser(description="Refrescar RAG desde ayuda.vmcsubastas.com")
    parser.add_argument("--limit", type=int, default=0, help="Límite de páginas en el crawl (0 = default del crawl)")
    parser.add_argument("--verify", action="store_true", help="Ejecutar verificación de contenido al final")
    args = parser.parse_args()

    # Guard de presupuesto diario — protege contra refreshes automáticos inesperados.
    # El refresh en sí no llama a LLMs, pero sí puede desencadenar eval_golden desde
    # maintenance.py justo después. $3 cubre un refresh + una corrida de eval.
    try:
        check_daily_budget(limit_usd=3.0)
    except BudgetExceededError as e:
        print(f"[BUDGET] {e}")
        sys.exit(1)

    crawl_cmd = [sys.executable, "-m", "src.ingest.crawl_helpcenter"]
    if args.limit > 0:
        crawl_cmd.extend(["--limit", str(args.limit)])

    steps = [
        ("Crawl Centro de Ayuda (Firecrawl)", crawl_cmd),
        ("Exportar markdown por URL", [sys.executable, "-m", "src.ingest.export_helpcenter_markdown"]),
        ("Exportar Condiciones y Términos", [sys.executable, "-m", "src.ingest.export_terms_markdown"]),
        ("Generar chunks", [sys.executable, "-m", "src.rag.chunks"]),
        ("Subir chunks a Pinecone", [sys.executable, "-m", "src.rag.embed"]),
    ]

    for desc, cmd in steps:
        if not run(cmd, desc):
            sys.exit(1)

    if args.verify:
        verify_script = ROOT / "scripts" / "verify_helpcenter_content.py"
        if not run([sys.executable, str(verify_script)], "Verificar contenido clave"):
            sys.exit(1)

    print("\n--- RAG refrescado correctamente ---")


if __name__ == "__main__":
    main()