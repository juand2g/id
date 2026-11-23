"""
Router: Consulta y streaming de tracks.
"""
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from app.database import get_collection

router = APIRouter(tags=["Tracks"])


@router.get("/tracks")
def get_tracks(limit: int = Query(50, ge=1, le=50000), skip: int = Query(0, ge=0)):
    """Devuelve lista paginada de tracks analizados."""
    collection = get_collection("tracks")
    tracks = list(collection.find({}, {"_id": 0}).skip(skip).limit(limit))
    return tracks


@router.get("/tracks/{filename}")
def get_track_by_filename(filename: str):
    """Devuelve un track específico por su filename."""
    collection = get_collection("tracks")
    track = collection.find_one({"filename": filename}, {"_id": 0})
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    return track


@router.get("/stream/{filename}")
def stream_track(filename: str):
    """
    Sirve el archivo de audio para reproducción en el frontend.
    Retorna el archivo MP3/WAV como FileResponse con headers de streaming.
    """
    collection = get_collection("tracks")
    track = collection.find_one({"filename": filename}, {"filepath": 1})

    if not track:
        raise HTTPException(status_code=404, detail="Track not found")

    filepath = Path(track["filepath"])
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Audio file not found on disk")

    # Determinar media type
    suffix = filepath.suffix.lower()
    media_types = {
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
        ".flac": "audio/flac",
        ".ogg": "audio/ogg",
        ".m4a": "audio/mp4",
        ".aac": "audio/aac",
    }
    media_type = media_types.get(suffix, "application/octet-stream")

    return FileResponse(
        path=str(filepath),
        media_type=media_type,
        filename=filename,
    )
