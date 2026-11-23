"""
Router: Escaneo de librería musical.
"""
from fastapi import APIRouter, BackgroundTasks
from app.services.scanner_service import scan_library_task, rescan_metadata_task, rescan_bpm_key_task

router = APIRouter(tags=["Scan"])


@router.post("/scan")
async def scan_library(background_tasks: BackgroundTasks):
    """Inicia el escaneo recursivo de la librería en segundo plano."""
    background_tasks.add_task(scan_library_task)
    return {"status": "started", "message": "Background scan initiated"}


@router.post("/rescan-metadata")
async def rescan_metadata(background_tasks: BackgroundTasks):
    """Re-lee metadatos de tracks con title/artist 'Unknown' usando lectura universal."""
    background_tasks.add_task(rescan_metadata_task)
    return {"status": "started", "message": "Metadata rescan initiated for Unknown tracks"}


@router.post("/rescan-bpm-key")
async def rescan_bpm_key(background_tasks: BackgroundTasks):
    """Normaliza BPM al rango DJ (70-180) y detecta key con chroma para todos los tracks."""
    background_tasks.add_task(rescan_bpm_key_task)
    return {"status": "started", "message": "BPM+key rescan initiated for all tracks"}
