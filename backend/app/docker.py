from pathlib import Path

from fastapi.staticfiles import StaticFiles

from backend.app.main import app


# Las rutas /api ya estan registradas; los demas archivos son del frontend.
frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
