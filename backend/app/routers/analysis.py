"""
Router: Análisis y generación de mapa UMAP.
"""
from fastapi import APIRouter, BackgroundTasks

from app.services.cartography_service import calculate_umap_coords

router = APIRouter(tags=["Analysis"])


@router.post("/map/generate")
async def generate_map(background_tasks: BackgroundTasks):
    """Inicia la generación del mapa 3D (UMAP) en segundo plano."""
    background_tasks.add_task(calculate_umap_coords)
    return {"status": "started", "message": "Map generation started in background"}
