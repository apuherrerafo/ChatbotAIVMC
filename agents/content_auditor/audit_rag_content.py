"""
agents/content_auditor/audit_rag_content.py
--------------------------------------------
Auditor de cobertura de contenido para VMC-Bot.

Se conecta a Pinecone y verifica cuántos chunks hay por categoría.
Detecta gaps críticos y genera un reporte priorizado de qué ingestar primero.

Uso:
  python agents/content_auditor/audit_rag_content.py
"""

import os
import json
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv
from pinecone import Pinecone

from src.core.logger import log_event, log_error

load_dotenv()

# ---------------------------------------------------------------------------
# 1. Configuración
# ---------------------------------------------------------------------------
_ROOT       = Path(__file__).resolve().parents[2]
_DOCS_DIR   = _ROOT / "docs"
_DOCS_DIR.mkdir(parents=True, exist_ok=True)

# Cobertura mínima por categoría (chunks en Pinecone)
# Si una categoría tiene menos chunks que este mínimo → gap detectado
COBERTURA_MINIMA = {
    "registro":          5,
    "subascoin":         5,
    "comisiones":        5,
    "proceso_subasta":   5,
    "visitas":           3,
    "consignaciones":    3,
    "pagos":             3,
    "subaspass":         3,
    "documentos":        3,
    "general":           2,
}

# Prioridad de cada categoría para el negocio VMC
PRIORIDAD_CATEGORIA = {
    "registro":          "CRITICA",
    "subascoin":         "CRITICA",
    "comisiones":        "CRITICA",
    "proceso_subasta":   "CRITICA",
    "visitas":           "ALTA",
    "consignaciones":    "ALTA",
    "pagos":             "ALTA",
    "subaspass":         "ALTA",
    "documentos":        "MEDIA",
    "general":           "MEDIA",
}

# Acción recomendada por categoría cuando hay gap
ACCION_POR_CATEGORIA = {
    "registro":        "Extraer infografia de registro paso a paso del Centro de Ayuda",
    "subascoin":       "Extraer infografia de SubasCoins y proceso de compra",
    "comisiones":      "Verificar tabla de comisiones en RAG + agregar FAQ de comisiones",
    "proceso_subasta": "Extraer infografias del proceso de subasta en vivo",
    "visitas":         "Extraer contenido de visitas e inspecciones del Centro de Ayuda",
    "consignaciones":  "Extraer infografia de consignaciones del Centro de Ayuda",
    "pagos":           "Agregar contenido sobre plazos y metodos de pago",
    "subaspass":       "Verificar scraping en vivo de vmcsubastas.com/subaspass",
    "documentos":      "Agregar contenido sobre documentacion requerida",
    "general":         "Revisar FAQs generales en Pinecone",
}


# ---------------------------------------------------------------------------
# 2. Conexión a Pinecone y conteo de chunks por categoría
# ---------------------------------------------------------------------------
def conectar_pinecone():
    """Inicializa el cliente de Pinecone."""
    api_key    = os.getenv("PINECONE_API_KEY")
    index_name = os.getenv("PINECONE_INDEX_NAME", "vmc-bot-rag")

    if not api_key:
        print("ERROR: PINECONE_API_KEY no encontrada en .env")
        return None, None

    try:
        pc    = Pinecone(api_key=api_key)
        index = pc.Index(index_name)
        log_event("auditor_pinecone_conectado", index=index_name)
        return pc, index
    except Exception as e:
        log_error("auditor_pinecone_error", message=str(e))
        print(f"ERROR conectando a Pinecone: {e}")
        return None, None


def contar_chunks_por_categoria(index) -> dict:
    """
    Consulta Pinecone para contar cuántos chunks hay por categoría.
    Usa queries vacías por categoría para obtener el conteo aproximado.

    Returns:
        Dict {categoria: cantidad_chunks}
    """
    conteos = {}

    for categoria in COBERTURA_MINIMA.keys():
        try:
            # Buscar chunks de esta categoría con un vector vacío
            # top_k=100 para tener una estimación del volumen
            resultado = index.query(
                vector=[0.0] * 1024,
                top_k=100,
                filter={"category": {"$eq": categoria}},
                include_metadata=True,
                namespace="helpcenter"
            )
            conteos[categoria] = len(resultado.get("matches", []))
            log_event("auditor_conteo", categoria=categoria, chunks=conteos[categoria])

        except Exception as e:
            log_error("auditor_conteo_error", message=str(e), categoria=categoria)
            conteos[categoria] = -1  # -1 indica error en la consulta

    return conteos


# ---------------------------------------------------------------------------
# 3. Análisis de gaps
# ---------------------------------------------------------------------------
def analizar_gaps(conteos: dict) -> dict:
    """
    Compara los conteos reales contra la cobertura mínima requerida.

    Returns:
        Dict con gaps clasificados por nivel de prioridad.
    """
    gaps = {
        "CRITICA": [],
        "ALTA":    [],
        "MEDIA":   [],
    }
    categorias_ok = []

    for categoria, minimo in COBERTURA_MINIMA.items():
        real      = conteos.get(categoria, 0)
        prioridad = PRIORIDAD_CATEGORIA.get(categoria, "MEDIA")
        accion    = ACCION_POR_CATEGORIA.get(categoria, "Revisar contenido")

        if real == -1:
            # Error en la consulta
            gaps[prioridad].append({
                "categoria": categoria,
                "chunks_reales": "ERROR",
                "chunks_minimo": minimo,
                "accion": f"Error consultando Pinecone para {categoria}. Verificar conexion.",
            })
        elif real < minimo:
            gaps[prioridad].append({
                "categoria":     categoria,
                "chunks_reales": real,
                "chunks_minimo": minimo,
                "faltantes":     minimo - real,
                "accion":        accion,
            })
        else:
            categorias_ok.append({
                "categoria": categoria,
                "chunks":    real,
            })

    return {"gaps": gaps, "ok": categorias_ok}


# ---------------------------------------------------------------------------
# 4. Generación del reporte
# ---------------------------------------------------------------------------
def generar_reporte(conteos: dict, analisis: dict) -> str:
    """Genera el texto del reporte de auditoría."""
    ahora   = datetime.now(timezone.utc)
    gaps    = analisis["gaps"]
    ok      = analisis["ok"]
    total_gaps = sum(len(v) for v in gaps.values())
    total_ok   = len(ok)
    total_cats = total_gaps + total_ok

    lineas = [
        f"",
        f"=== AUDITORIA DE CONTENIDO VMC-Bot — {ahora.strftime('%Y-%m-%d %H:%M')} UTC ===",
        f"",
        f"COBERTURA GENERAL: {total_ok}/{total_cats} categorias cubiertas",
        f"Gaps detectados:   {total_gaps}",
        f"",
    ]

    # Gaps críticos
    if gaps["CRITICA"]:
        lineas.append(f"GAPS CRITICOS (bloquean respuestas clave del bot):")
        for g in gaps["CRITICA"]:
            chunks_str = str(g['chunks_reales']) if g['chunks_reales'] != "ERROR" else "ERROR"
            lineas.append(f"  [{g['categoria'].upper()}]")
            lineas.append(f"    Chunks en Pinecone: {chunks_str} / {g.get('chunks_minimo','?')} minimo")
            lineas.append(f"    Accion: {g['accion']}")
            lineas.append("")
    else:
        lineas.append("GAPS CRITICOS: Ninguno")
        lineas.append("")

    # Gaps altos
    if gaps["ALTA"]:
        lineas.append(f"GAPS ALTOS (mejoran significativamente la calidad):")
        for g in gaps["ALTA"]:
            chunks_str = str(g['chunks_reales']) if g['chunks_reales'] != "ERROR" else "ERROR"
            lineas.append(f"  [{g['categoria'].upper()}]")
            lineas.append(f"    Chunks en Pinecone: {chunks_str} / {g.get('chunks_minimo','?')} minimo")
            lineas.append(f"    Accion: {g['accion']}")
            lineas.append("")
    else:
        lineas.append("GAPS ALTOS: Ninguno")
        lineas.append("")

    # Gaps medios
    if gaps["MEDIA"]:
        lineas.append(f"GAPS MEDIOS (mejoras opcionales):")
        for g in gaps["MEDIA"]:
            chunks_str = str(g['chunks_reales']) if g['chunks_reales'] != "ERROR" else "ERROR"
            lineas.append(f"  [{g['categoria'].upper()}] {chunks_str}/{g.get('chunks_minimo','?')} chunks — {g['accion']}")
        lineas.append("")

    # Categorías OK
    if ok:
        lineas.append(f"CATEGORIAS CON COBERTURA SUFICIENTE:")
        for cat in ok:
            lineas.append(f"  [{cat['categoria'].upper()}] {cat['chunks']} chunks — OK")
        lineas.append("")

    # Próximas acciones priorizadas
    todas_las_acciones = (
        [(g, "CRITICA") for g in gaps["CRITICA"]] +
        [(g, "ALTA")    for g in gaps["ALTA"]]    +
        [(g, "MEDIA")   for g in gaps["MEDIA"]]
    )

    if todas_las_acciones:
        lineas.append(f"PROXIMAS ACCIONES (en orden de prioridad):")
        for i, (g, nivel) in enumerate(todas_las_acciones[:5], 1):
            lineas.append(f"  {i}. [{nivel}] {g['accion']}")
        lineas.append("")

    return "\n".join(lineas)


# ---------------------------------------------------------------------------
# 5. Entry point
# ---------------------------------------------------------------------------
def main():
    print("\nConectando a Pinecone...")
    pc, index = conectar_pinecone()
    if not index:
        return

    print("Contando chunks por categoria...")
    conteos = contar_chunks_por_categoria(index)

    print("Analizando gaps...")
    analisis = analizar_gaps(conteos)

    reporte_texto = generar_reporte(conteos, analisis)
    print(reporte_texto)

    # Guardar reporte en docs/
    fecha_str    = datetime.now(timezone.utc).strftime("%Y%m%d")
    reporte_path = _DOCS_DIR / f"auditoria_contenido_{fecha_str}.md"
    reporte_path.write_text(reporte_texto, encoding="utf-8")
    print(f"Reporte guardado en: {reporte_path}")

    # Guardar JSON con datos crudos para otros scripts
    json_path = _DOCS_DIR / f"auditoria_contenido_{fecha_str}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "fecha":    datetime.now(timezone.utc).isoformat(),
            "conteos":  conteos,
            "analisis": analisis,
        }, f, ensure_ascii=False, indent=2)

    log_event("auditoria_completada",
              total_gaps=sum(len(v) for v in analisis["gaps"].values()),
              categorias_ok=len(analisis["ok"]))


if __name__ == "__main__":
    main()