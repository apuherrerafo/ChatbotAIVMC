"""
Taxonomía de temas del Centro de Ayuda VMC.
Mapeo de slug/filename -> tema para metadata de chunks.
"""
from pathlib import Path

# Palabras clave en el nombre de archivo (slug) -> tema
TAXONOMY_KEYWORDS = [
    ("registro", "Registro y cuenta"),
    ("registrarte", "Registro y cuenta"),
    ("billetera", "SubasCoins y billetera"),
    ("subascoins", "SubasCoins y billetera"),
    ("subaswallet", "SubasCoins y billetera"),
    ("recarga", "SubasCoins y billetera"),
    ("devolucion", "SubasCoins y billetera"),
    ("transferencia", "SubasCoins y billetera"),
    ("consignacion", "Consignación"),
    ("consignar", "Consignación"),
    ("oferta-en-vivo", "Oferta En Vivo"),
    ("en-vivo", "Oferta En Vivo"),
    ("oferta-negociable", "Oferta Negociable"),
    ("negociable", "Oferta Negociable"),
    ("visitas", "Visitas e inspección"),
    ("inspecciones", "Visitas e inspección"),
    ("subastour", "SubasTour"),
    ("lo-mas-consultado", "Lo más consultado"),
    ("videotutoriales", "Videotutoriales"),
    ("centro-de-ayuda-comprador", "General"),
]


def topic_from_slug(slug: str) -> str:
    """Devuelve el tema asignado al slug del archivo."""
    slug_lower = slug.lower()
    for keyword, topic in TAXONOMY_KEYWORDS:
        if keyword in slug_lower:
            return topic
    return "General"
