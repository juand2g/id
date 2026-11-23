"""
ID System — Audio Core API
Punto de entrada principal. Solo bootstrap: CORS, lifespan y registro de routers.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app import database
from app.routers import scan, tracks, analysis, ingest

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / Shutdown del servidor."""
    # Startup
    database.ping()
    yield
    # Shutdown
    database.close()


app = FastAPI(
    title="ID System — Audio Core API",
    version="2.0.0",
    description="Plataforma de Inteligencia Musical y Cartografía de Audio 3D",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(scan.router)
app.include_router(tracks.router)
app.include_router(analysis.router)
app.include_router(ingest.router)



@app.get("/")
def root():
    return {
        "system": "ID System — Audio Core",
        "version": "2.0.0",
        "status": "online"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
