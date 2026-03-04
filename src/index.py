"""
Entrypoint para Vercel: expone la app FastAPI.
Vercel busca `app` en src/index.py por defecto.
"""
from src.server.app import app

__all__ = ["app"]
