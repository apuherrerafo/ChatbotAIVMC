"""
src/core/firecrawl_client.py
----------------------------
Cliente seguro para Firecrawl con manejo de errores.

Resuelve:
  - PaymentRequiredError (sin créditos) que hoy rompe los pipelines de ingest
  - Pérdida de contenido en Pinecone cuando el scraping falla a medias
  - Fallos silenciosos sin registro ni aviso claro

Estrategia:
  - Detecta el error ANTES de que cause daño
  - Mantiene el último contenido válido (no borra Pinecone)
  - Registra todo en el sistema de logging
  - Avisa claramente qué pasó y qué hacer
"""

import os
import json
from pathlib import Path
from datetime import datetime, timezone

from src.core.logger import log_error, log_event

# ---------------------------------------------------------------------------
# 1. Ruta del archivo de estado
#    Guarda cuándo fue el último scrape exitoso y qué URL se scrapeó.
#    Así siempre sabemos si el contenido está fresco o es viejo.
# ---------------------------------------------------------------------------
_STATE_FILE = Path(__file__).resolve().parents[2] / "logs" / "firecrawl_state.json"


def _load_state() -> dict:
    """Carga el estado del último scrape exitoso."""
    try:
        if _STATE_FILE.exists():
            with open(_STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _save_state(url: str, paginas: int) -> None:
    """Guarda el estado después de un scrape exitoso."""
    state = {
        "ultimo_scrape_exitoso": datetime.now(timezone.utc).isoformat(),
        "url": url,
        "paginas_scrapeadas": paginas,
    }
    with open(_STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# 2. Verificación de créditos antes de scraping
#    Intenta una página de prueba antes de lanzar un crawl grande.
#    Si falla por créditos, avisa inmediatamente sin gastar nada.
# ---------------------------------------------------------------------------
def verificar_creditos(firecrawl_app) -> bool:
    """
    Verifica si hay créditos disponibles haciendo una llamada mínima.
    
    Returns:
        True si hay créditos disponibles.
        False si no hay créditos o hay algún error.
    """
    try:
        # Intenta scrapear una página muy ligera como prueba
        firecrawl_app.scrape_url(
            "https://www.vmcsubastas.com",
            params={"formats": ["markdown"]}
        )
        log_event("firecrawl_creditos_ok")
        return True

    except Exception as e:
        error_str = str(e).lower()
        if "payment" in error_str or "credits" in error_str or "402" in error_str:
            log_error(
                "firecrawl_sin_creditos",
                message="No hay créditos disponibles en Firecrawl.",
                accion_requerida="Recargar créditos en firecrawl.dev",
            )
            print(
                "\n⚠️  FIRECRAWL SIN CRÉDITOS\n"
                "   No se puede hacer scraping en este momento.\n"
                "   → Ve a firecrawl.dev y recarga créditos.\n"
                "   → El contenido anterior en Pinecone NO fue modificado.\n"
            )
            return False
        
        # Otro tipo de error (red, timeout, etc.)
        log_error("firecrawl_error_verificacion", message=str(e))
        return False


# ---------------------------------------------------------------------------
# 3. Scrape seguro de una URL individual
#    Envuelve firecrawl_app.scrape_url() con manejo de errores completo.
# ---------------------------------------------------------------------------
def scrape_seguro(firecrawl_app, url: str, params: dict = None) -> str | None:
    """
    Scrapea una URL de forma segura.

    Args:
        firecrawl_app: Instancia de FirecrawlApp ya inicializada.
        url:           URL a scrapear.
        params:        Parámetros adicionales para Firecrawl.

    Returns:
        Texto en markdown si el scrape fue exitoso.
        None si falló (el caller decide qué hacer con None).
    """
    if params is None:
        params = {"formats": ["markdown"]}

    try:
        log_event("firecrawl_scrape_inicio", url=url)

        # Compatibilidad con distintas versiones del SDK:
        # - firecrawl_app.scrape_url(url, params={...}) (versiones nuevas / FirecrawlApp)
        # - firecrawl_app.scrape(url, formats=[...])    (versiones antiguas / Firecrawl)
        if hasattr(firecrawl_app, "scrape_url"):
            resultado = firecrawl_app.scrape_url(url, params=params)
            contenido = resultado.get("markdown", "")
        else:
            # Fallback: usar .scrape() si existe
            if hasattr(firecrawl_app, "scrape"):
                scrape_kwargs = {}
                fmts = params.get("formats") if isinstance(params, dict) else None
                if fmts:
                    scrape_kwargs["formats"] = fmts
                resultado = firecrawl_app.scrape(url, **scrape_kwargs)
            else:
                raise RuntimeError("firecrawl_app no tiene ni scrape_url ni scrape")

            contenido = ""
            if resultado is None:
                contenido = ""
            elif isinstance(resultado, dict):
                contenido = resultado.get("markdown", "") or ""
            elif hasattr(resultado, "markdown"):
                contenido = getattr(resultado, "markdown") or ""
            elif hasattr(resultado, "data"):
                data = getattr(resultado, "data", None)
                contenido = getattr(data, "markdown", "") if data else ""

        if not contenido:
            log_error("firecrawl_contenido_vacio", message="Scrape exitoso pero sin contenido.", url=url)
            return None

        log_event("firecrawl_scrape_exito", url=url, chars=len(contenido))
        return contenido

    except Exception as e:
        error_str = str(e).lower()

        if "payment" in error_str or "credits" in error_str or "402" in error_str:
            log_error(
                "firecrawl_sin_creditos",
                message="Sin créditos durante scrape.",
                url=url,
                accion_requerida="Recargar créditos en firecrawl.dev",
            )
            print(f"\n⚠️  Sin créditos al scrapear {url}. Pinecone NO fue modificado.\n")
            return None

        log_error("firecrawl_scrape_error", message=str(e), url=url)
        return None


# ---------------------------------------------------------------------------
# 4. Crawl seguro de un sitio completo
#    Para cuando necesitas scrapear múltiples páginas (ej: Centro de Ayuda).
#    Verifica créditos ANTES de empezar para no quedar a medias.
# ---------------------------------------------------------------------------
def crawl_seguro(firecrawl_app, url_base: str, limite: int = 30) -> list[dict] | None:
    """
    Crawlea un sitio completo de forma segura.

    Args:
        firecrawl_app: Instancia de FirecrawlApp ya inicializada.
        url_base:      URL raíz desde donde empieza el crawl.
        limite:        Máximo de páginas a crawlear.

    Returns:
        Lista de dicts con {url, markdown} si fue exitoso.
        None si falló antes de empezar (sin créditos u otro error).
    """
    # Verificar créditos ANTES de empezar el crawl grande
    if not verificar_creditos(firecrawl_app):
        estado = _load_state()
        if estado:
            print(
                f"   → Último scrape exitoso: {estado.get('ultimo_scrape_exitoso', 'desconocido')}\n"
                f"   → Páginas scrapeadas entonces: {estado.get('paginas_scrapeadas', '?')}\n"
                f"   → El contenido en Pinecone sigue siendo ese.\n"
            )
        return None

    try:
        log_event("firecrawl_crawl_inicio", url_base=url_base, limite=limite)

        # Compatibilidad con distintas versiones del SDK:
        # - firecrawl_app.crawl_url(url, params={...})
        # - firecrawl_app.crawl(url, limit=..., scrape_options=...)
        if hasattr(firecrawl_app, "crawl_url"):
            resultado = firecrawl_app.crawl_url(
                url_base,
                params={"limit": limite, "scrapeOptions": {"formats": ["markdown"]}}
            )
            paginas = resultado.get("data", [])
        else:
            if not hasattr(firecrawl_app, "crawl"):
                raise RuntimeError("firecrawl_app no tiene ni crawl_url ni crawl")
            from firecrawl.types import ScrapeOptions  # type: ignore
            resultado = firecrawl_app.crawl(
                url_base,
                limit=limite,
                scrape_options=ScrapeOptions(formats=["markdown"]),
            )
            paginas = getattr(resultado, "data", None) or []
        if not paginas:
            log_error("firecrawl_crawl_vacio", message="Crawl exitoso pero sin páginas.", url_base=url_base)
            return None

        # Guardar estado del scrape exitoso
        _save_state(url=url_base, paginas=len(paginas))
        log_event("firecrawl_crawl_exito", url_base=url_base, paginas=len(paginas))
        print(f"\n✓ Crawl exitoso: {len(paginas)} páginas desde {url_base}\n")
        return paginas

    except Exception as e:
        log_error("firecrawl_crawl_error", message=str(e), url_base=url_base)
        print(f"\n⚠️  Error en crawl de {url_base}: {e}\n")
        return None