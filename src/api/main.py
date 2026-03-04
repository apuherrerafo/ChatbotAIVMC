"""
Entrypoint para Vercel: expone la app FastAPI.
Todas las rutas (/, /api/ask, etc.) se enrutan aquí vía vercel.json.
"""
from src.server.app import app

__all__ = ["app"]
