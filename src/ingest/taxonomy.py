"""
Taxonomía de temas del Centro de Ayuda VMC.
Mapeo de slug/filename -> tema para metadata de chunks.
"""
from pathlib import Path

# Palabras clave en el nombre de archivo (slug) -> tema
# Incluye temas del golden dataset que deben tener chunks dedicados (Comisión, Devolución de saldo, etc.)
TAXONOMY_KEYWORDS = [
    ("registro", "Registro y cuenta"),
    ("registrarte", "Registro y cuenta"),
    ("billetera", "SubasCoins y billetera"),
    ("subascoins", "SubasCoins y billetera"),
    ("subaswallet", "SubasCoins y billetera"),
    ("recarga", "Recarga"),
    ("devolucion", "Devolución de saldo"),
    ("transferencia", "SubasCoins y billetera"),
    ("consignacion", "Consignación"),
    ("consignar", "Consignación"),
    ("oferta-en-vivo", "Oferta En Vivo"),
    ("en-vivo", "Oferta En Vivo"),
    ("oferta-negociable", "Oferta Negociable"),
    ("negociable", "Oferta Negociable"),
    ("visitas", "Visitas"),
    ("inspecciones", "Visitas"),
    ("comision", "Comisión"),
    ("habilitado", "Ganador habilitado"),
    ("habilitacion", "Ganador habilitado"),
    ("ganadores-habilitados", "Ganador habilitado"),
    ("proceso-de-compra-venta", "Ganador habilitado"),
    ("financiamiento", "Oferta con financiamiento"),
    ("pacifico", "Pago y Pacífico"),
    ("codigo-de-pago", "Pago y Pacífico"),
    ("sanciones", "Sanciones"),
    ("responsabilidades-de-los-participantes", "Sanciones"),
    ("responsabilidades-de-los-ganadores", "Sanciones"),
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
