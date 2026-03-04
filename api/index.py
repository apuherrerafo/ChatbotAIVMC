"""
Entrypoint para Vercel: función serverless que sirve la app FastAPI.
Todas las rutas (/, /api/ask, etc.) se enrutan aquí vía vercel.json.
"""
from src.server.app import app
