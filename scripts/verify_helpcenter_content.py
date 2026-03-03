"""
Verifica con Firecrawl que el contenido clave del Centro de Ayuda sigue en la web.
Scrapea las URLs críticas y comprueba que ciertos textos esperados estén presentes
(orden de pasos, nombres de botones, etc.). Sirve para detectar cambios en la web
que romperían las respuestas del bot.

Uso (desde la raíz del proyecto vmc-bot):
  python scripts/verify_helpcenter_content.py
  python scripts/verify_helpcenter_content.py --url "https://ayuda.vmcsubastas.com/es/articles/5816072-registrarte-es-facil-y-rapido"
"""
import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

# URLs críticas y qué debe aparecer en cada una (para no dar información errónea al bot).
CONTENT_CHECKS = [
    {
        "name": "Registro (Ingresa → Regístrate)",
        "url": "https://ayuda.vmcsubastas.com/es/articles/5816072-registrarte-es-facil-y-rapido",
        "required_substrings": ["Ingresa", "Regístrate", "registro", "Sigamos"],
        "order_matters": True,  # "Ingresa" debe aparecer antes que "Regístrate" en el flujo
        "substring_order": ["Ingresa", "Regístrate"],
    },
    {
        "name": "SubasCoins / Billetera",
        "url": "https://ayuda.vmcsubastas.com/es/articles/5820348-subascoins-que-son-para-que-sirven-y-como-se-adquieren",
        "required_substrings": ["SubasCoins", "billetera", "adquirir"],
    },
    {
        "name": "Consignación",
        "url": "https://ayuda.vmcsubastas.com/es/articles/5820340-consignar-es-necesario-para-participar",
        "required_substrings": ["consignación", "consignar", "participar"],
    },
    {
        "name": "Oferta En Vivo",
        "url": "https://ayuda.vmcsubastas.com/es/articles/5823600-la-oferta-en-vivo-aqui-esta-la-informacion-que-buscabas",
        "required_substrings": ["En Vivo", "subasta", "participar"],
    },
    {
        "name": "Oferta Negociable",
        "url": "https://ayuda.vmcsubastas.com/es/articles/5823664-la-oferta-negociable-como-funciona",
        "required_substrings": ["Negociable", "negociación", "proponer"],
    },
]


def scrape_url(firecrawl, url: str) -> str:
    """Scrapea una URL con Firecrawl y devuelve el markdown."""
    try:
        result = firecrawl.scrape(url, formats=["markdown"])
        md = ""
        if result and hasattr(result, "markdown"):
            md = result.markdown or ""
        elif result and isinstance(result, dict):
            md = result.get("markdown", "")
        if not md and hasattr(result, "data"):
            md = getattr(result.data, "markdown", "") if result.data else ""
        return (md or "").strip()
    except Exception as e:
        return f"[ERROR: {e}]"


def run_check(firecrawl, check: dict) -> tuple[bool, str]:
    """Ejecuta una comprobación. Devuelve (ok, mensaje)."""
    name = check["name"]
    url = check["url"]
    required = check.get("required_substrings", [])
    suborder = check.get("substring_order", [])
    order_matters = check.get("order_matters", False) and suborder

    content = scrape_url(firecrawl, url)
    if content.startswith("[ERROR:"):
        return False, f"{name}: no se pudo scrapear — {content}"

    content_lower = content.lower()
    missing = [s for s in required if s.lower() not in content_lower]
    if missing:
        return False, f"{name}: faltan en la página: {missing}"

    if order_matters:
        pos_ingresa = content_lower.find(suborder[0].lower())
        pos_registrate = content_lower.find(suborder[1].lower())
        if pos_ingresa == -1 or pos_registrate == -1:
            return False, f"{name}: no se encontró orden (Ingresa/Regístrate)"
        if pos_ingresa > pos_registrate:
            return False, f"{name}: en la web 'Regístrate' aparece antes que 'Ingresa'; el flujo correcto es Ingresa → luego Regístrate."

    return True, f"{name}: OK"


def main():
    parser = argparse.ArgumentParser(description="Verificar contenido del Centro de Ayuda con Firecrawl")
    parser.add_argument("--url", type=str, default=None, help="Verificar solo esta URL (usa required_substrings del primer check)")
    args = parser.parse_args()

    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        print("ERROR: FIRECRAWL_API_KEY no está en .env")
        sys.exit(1)

    try:
        from firecrawl import Firecrawl
    except ImportError:
        print("Instala firecrawl-py: pip install firecrawl-py")
        sys.exit(1)

    firecrawl = Firecrawl(api_key=api_key)

    if args.url:
        checks = [{**CONTENT_CHECKS[0], "url": args.url}]
    else:
        checks = CONTENT_CHECKS

    print("Verificando contenido en ayuda.vmcsubastas.com con Firecrawl...\n")
    failed = []
    for check in checks:
        ok, msg = run_check(firecrawl, check)
        status = "OK" if ok else "FAIL"
        print(f"  [{status}] {msg}")
        if not ok:
            failed.append(msg)

    print()
    if failed:
        print(f"Resumen: {len(failed)} de {len(checks)} comprobaciones fallaron.")
        sys.exit(1)
    print(f"Resumen: las {len(checks)} comprobaciones pasaron.")
    sys.exit(0)


if __name__ == "__main__":
    main()
