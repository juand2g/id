"""
Router: Ingesta de tracks desde el Set Identifier (El Puente).
Endpoint que recibe archivos MP3 + metadata y los integra al Cerebro.
"""
import logging
from fastapi import APIRouter, BackgroundTasks, File, Form, UploadFile
from fastapi.concurrency import run_in_threadpool

from app.services.ingest_service import ingest_track
from app.services.cartography_service import calculate_umap_coords

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Ingest"])


@router.post("/ingest")
async def ingest_track_endpoint(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Archivo de audio MP3/WAV/FLAC"),
    artist: str = Form(default=None, description="Artista del track"),
    title: str = Form(default=None, description="Título del track"),
    album: str = Form(default=None, description="Álbum (opcional)"),
    source_url: str = Form(default=None, description="URL original del set/playlist"),
    source_set: str = Form(default=None, description="Nombre del set/playlist"),
    recalculate_map: bool = Form(default=True, description="Recalcular UMAP tras ingesta"),
):
    """
    Recibe un track desde el Set Identifier y lo integra al Cerebro (ID System).

    El archivo se guarda en ~/Música/music/SetIdentifier/, se analizan sus features
    acústicos con librosa, y se inserta como nuevo nodo en MongoDB.

    Si recalculate_map=True (default), se recalculan las coordenadas UMAP
    en background para que la Sonic Galaxy 3D se actualice con el nuevo track.
    """
    # Leer bytes del archivo
    file_bytes = await file.read()

    if not file_bytes:
        return {"status": "error", "reason": "empty_file"}

    filename = file.filename or "unknown_track.mp3"

    # Ingestar el track
    result = await ingest_track(
        file_bytes=file_bytes,
        filename=filename,
        artist=artist,
        title=title,
        album=album,
        source_url=source_url,
        source_set=source_set,
    )

    # Recalcular mapa UMAP en background si se ingresó un nuevo track
    if recalculate_map and result.get("status") == "ingested":
        background_tasks.add_task(calculate_umap_coords)
        result["umap_recalculation"] = "scheduled"

    return result


@router.post("/ingest/batch")
async def ingest_batch_endpoint(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(..., description="Archivos de audio"),
    source_url: str = Form(default=None),
    source_set: str = Form(default=None),
):
    """
    Ingesta un lote de tracks. Útil para playlists completas.
    Recalcula UMAP una sola vez al final.
    """
    results = []
    ingested = 0

    for file in files:
        file_bytes = await file.read()
        if not file_bytes:
            results.append({"status": "error", "reason": "empty_file", "filename": file.filename})
            continue

        result = await ingest_track(
            file_bytes=file_bytes,
            filename=file.filename or "unknown.mp3",
            source_url=source_url,
            source_set=source_set,
        )
        results.append(result)
        if result.get("status") == "ingested":
            ingested += 1

    # Recalcular mapa una sola vez al final
    if ingested > 0:
        background_tasks.add_task(calculate_umap_coords)

    return {
        "total": len(files),
        "ingested": ingested,
        "skipped": sum(1 for r in results if r.get("status") == "skipped"),
        "errors": sum(1 for r in results if r.get("status") == "error"),
        "umap_recalculation": "scheduled" if ingested > 0 else "not_needed",
        "results": results,
    }
