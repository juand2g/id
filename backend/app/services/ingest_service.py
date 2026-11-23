"""
Servicio de ingesta: recibe tracks desde el Set Identifier (El Puente).
Copia el archivo a la librería musical, lo analiza y guarda en MongoDB.
"""
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path

from fastapi.concurrency import run_in_threadpool

from app.config import LIBRARY_PATH
from app.database import get_collection
from app.services.feature_service import analyze_file
from app.services.cartography_service import calculate_umap_coords

logger = logging.getLogger(__name__)

# Carpeta de destino para tracks ingestados
INGEST_DIR = LIBRARY_PATH / "SetIdentifier"


async def ingest_track(
    file_bytes: bytes,
    filename: str,
    artist: str | None = None,
    title: str | None = None,
    album: str | None = None,
    source_url: str | None = None,
    source_set: str | None = None,
) -> dict:
    """
    Ingesta un track desde el Set Identifier al ID System.

    1. Guarda el archivo en ~/Música/music/SetIdentifier/
    2. Verifica si ya existe en MongoDB (evita duplicados)
    3. Analiza features acústicos con librosa
    4. Guarda el documento en MongoDB
    5. Dispara recálculo UMAP en background

    Args:
        file_bytes: Contenido binario del archivo de audio
        filename: Nombre del archivo (ej: "01 - Artist - Title.mp3")
        artist: Artista del track (metadata del Set Identifier)
        title: Título del track
        album: Álbum (opcional)
        source_url: URL original del set/playlist
        source_set: Nombre del set/playlist de origen

    Returns:
        dict con status y detalle de la operación
    """
    collection = get_collection("tracks")

    # 1. Crear directorio de destino si no existe
    INGEST_DIR.mkdir(parents=True, exist_ok=True)

    dest_path = INGEST_DIR / filename

    # 2. Verificar duplicados por filename
    existing = collection.find_one({
        "$or": [
            {"filepath": str(dest_path)},
            {"filename": filename},
        ]
    })

    if existing:
        logger.info(f"⏭️ Track ya existe en el Cerebro: {filename}")
        return {
            "status": "skipped",
            "reason": "already_exists",
            "filename": filename,
        }

    # 3. Guardar archivo en la librería
    try:
        dest_path.write_bytes(file_bytes)
        logger.info(f"💾 Archivo guardado: {dest_path}")
    except Exception as e:
        logger.error(f"❌ Error guardando archivo {filename}: {e}")
        return {"status": "error", "reason": f"file_save_failed: {e}"}

    # 4. Analizar features acústicos
    try:
        analysis_result = await run_in_threadpool(analyze_file, str(dest_path))

        if analysis_result.get("status") == "failed":
            logger.warning(f"⚠️ Análisis falló para: {filename}")
            return {
                "status": "error",
                "reason": f"analysis_failed: {analysis_result.get('error', 'unknown')}",
                "filename": filename,
            }
    except Exception as e:
        logger.error(f"❌ Error analizando {filename}: {e}")
        return {"status": "error", "reason": f"analysis_error: {e}"}

    # 5. Enriquecer con metadata del Set Identifier (si librosa no lo detectó)
    if artist and analysis_result.get("artist") == "Unknown":
        analysis_result["artist"] = artist
    if title and analysis_result.get("title") == "Unknown":
        analysis_result["title"] = title

    # 6. Guardar en MongoDB
    track_doc = {
        "filepath": str(dest_path),
        "filename": filename,
        "analysis": analysis_result,
        "scanned_at": datetime.now(timezone.utc),
        "source": {
            "system": "set-identifier",
            "url": source_url,
            "set_name": source_set,
            "ingested_at": datetime.now(timezone.utc),
        },
    }

    collection.insert_one(track_doc)
    logger.info(
        f"✅ Track ingestado al Cerebro: "
        f"{analysis_result.get('artist', '?')} - {analysis_result.get('title', '?')} "
        f"(BPM: {analysis_result.get('bpm')}, Key: {analysis_result.get('key')})"
    )

    return {
        "status": "ingested",
        "filename": filename,
        "artist": analysis_result.get("artist"),
        "title": analysis_result.get("title"),
        "bpm": analysis_result.get("bpm"),
        "key": analysis_result.get("key"),
        "energy": analysis_result.get("energy"),
    }


async def ingest_batch(
    tracks_data: list[dict],
    recalculate_map: bool = True,
) -> dict:
    """
    Ingesta un lote de tracks y opcionalmente recalcula el mapa UMAP.

    Args:
        tracks_data: Lista de dicts con file_bytes, filename, artist, title, etc.
        recalculate_map: Si True, recalcula UMAP tras la ingesta

    Returns:
        dict con resumen de la operación
    """
    results = []
    ingested = 0

    for track_data in tracks_data:
        result = await ingest_track(**track_data)
        results.append(result)
        if result["status"] == "ingested":
            ingested += 1

    # Recalcular mapa UMAP si se ingresaron nuevos tracks
    if recalculate_map and ingested > 0:
        logger.info(f"🗺️ Recalculando mapa UMAP ({ingested} nuevos tracks)...")
        try:
            await run_in_threadpool(calculate_umap_coords)
            logger.info("✅ Mapa UMAP actualizado tras ingesta")
        except Exception as e:
            logger.error(f"⚠️ Error recalculando UMAP: {e}")

    return {
        "total": len(tracks_data),
        "ingested": ingested,
        "skipped": sum(1 for r in results if r["status"] == "skipped"),
        "errors": sum(1 for r in results if r["status"] == "error"),
        "results": results,
    }
