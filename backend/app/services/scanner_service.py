"""
Servicio de escaneo de librería musical.
Escanea recursivamente la carpeta de música, analiza cada archivo y guarda en MongoDB.
"""
from pathlib import Path
from datetime import datetime, timezone
from fastapi.concurrency import run_in_threadpool
import logging

from app.config import LIBRARY_PATH, AUDIO_EXTENSIONS
from app.database import get_collection
from app.services.feature_service import analyze_file, get_metadata_robust

logger = logging.getLogger(__name__)


async def scan_library_task():
    """
    Tarea en segundo plano que escanea la librería musical.
    Busca archivos de audio recursivamente, evita duplicados y guarda análisis en BD.
    """
    collection = get_collection("tracks")
    logger.info(f"🎵 Iniciando escaneo: {LIBRARY_PATH}")

    if not LIBRARY_PATH.exists():
        logger.error(f"❌ Ruta no encontrada: {LIBRARY_PATH}")
        return

    # Recolectar archivos de audio
    files_to_process = []
    for ext in AUDIO_EXTENSIONS:
        files_to_process.extend(LIBRARY_PATH.rglob(ext))

    logger.info(f"📂 Archivos encontrados: {len(files_to_process)}")

    processed = 0
    skipped = 0

    for file_path in files_to_process:
        str_path = str(file_path.absolute())

        # Verificar duplicados por filename
        existing = collection.find_one({
            "$or": [
                {"filepath": str_path},
                {"filename": file_path.name}
            ]
        })

        if existing:
            # Si existe pero con path diferente, actualizar la ruta
            if existing["filepath"] != str_path:
                collection.update_one(
                    {"_id": existing["_id"]},
                    {"$set": {"filepath": str_path, "scanned_at": datetime.now(timezone.utc)}}
                )
                logger.info(f"🔄 Ruta migrada: {file_path.name}")
            skipped += 1
            continue

        try:
            # Análisis pesado en threadpool (no bloquea el event loop)
            analysis_result = await run_in_threadpool(analyze_file, str_path)

            if analysis_result.get("status") == "failed":
                logger.warning(f"⚠️ Fallo al analizar: {file_path.name}")
                continue

            track_doc = {
                "filepath": str_path,
                "filename": file_path.name,
                "analysis": analysis_result,
                "scanned_at": datetime.now(timezone.utc),
            }

            collection.insert_one(track_doc)
            processed += 1
            logger.info(f"✅ [{processed}] Guardado: {file_path.name}")

        except Exception as e:
            logger.error(f"❌ Error procesando {file_path.name}: {e}")

    logger.info(f"🏁 Escaneo finalizado. Nuevos: {processed}, Existentes: {skipped}")


async def rescan_metadata_task():
    """
    Re-lee metadatos de tracks con title/artist 'Unknown'.
    Solo actualiza metadata (título, artista, género, key, bpm), no re-analiza features.
    """
    collection = get_collection("tracks")
    logger.info("🔄 Iniciando re-escaneo de metadatos para tracks 'Unknown'...")

    # Buscar tracks con title o artist como Unknown
    query = {"$or": [
        {"analysis.title": "Unknown"},
        {"analysis.artist": "Unknown"},
    ]}
    unknown_tracks = list(collection.find(query))
    logger.info(f"📋 Tracks con metadatos Unknown: {len(unknown_tracks)}")

    updated = 0
    for track in unknown_tracks:
        filepath = track.get("filepath", "")
        if not filepath or not Path(filepath).exists():
            logger.warning(f"⚠️ Archivo no encontrado: {filepath}")
            continue

        try:
            metadata = await run_in_threadpool(get_metadata_robust, filepath)

            # Solo actualizar si obtuvimos datos mejores
            update_fields = {}
            if metadata["title"] != "Unknown":
                update_fields["analysis.title"] = metadata["title"]
            if metadata["artist"] != "Unknown":
                update_fields["analysis.artist"] = metadata["artist"]
            if metadata["genre"] != "Unknown":
                update_fields["analysis.genre"] = metadata["genre"]
            if metadata["key"]:
                update_fields["analysis.key"] = metadata["key"]
            if metadata["bpm"] and not track.get("analysis", {}).get("bpm"):
                update_fields["analysis.bpm"] = metadata["bpm"]

            if update_fields:
                update_fields["scanned_at"] = datetime.now(timezone.utc)
                collection.update_one(
                    {"_id": track["_id"]},
                    {"$set": update_fields}
                )
                updated += 1
                logger.info(f"✅ Actualizado: {Path(filepath).name} → {metadata['artist']} - {metadata['title']}")
            else:
                logger.info(f"⏭️ Sin mejora: {Path(filepath).name}")

        except Exception as e:
            logger.error(f"❌ Error re-leyendo {filepath}: {e}")

    logger.info(f"🏁 Re-escaneo finalizado. Actualizados: {updated}/{len(unknown_tracks)}")


async def rescan_bpm_key_task():
    """
    Re-escanea BPM y key de TODOS los tracks:
    - Normaliza BPM al rango DJ (70-180) — fix half-time
    - Detecta key con chroma si no tiene o tiene '?'/'Unknown'
    - Solo recarga audio para tracks sin key válida
    """
    from app.services.feature_service import _normalize_bpm_dj, _detect_key_chroma
    import librosa

    collection = get_collection("tracks")
    all_tracks = list(collection.find({}))
    logger.info(f"🔄 Re-escaneo BPM+key: {len(all_tracks)} tracks")

    updated = 0
    for track in all_tracks:
        update_fields = {}
        analysis = track.get("analysis", {})

        # 1. Normalizar BPM
        bpm = analysis.get("bpm")
        if bpm and bpm > 0:
            normalized = _normalize_bpm_dj(bpm)
            if abs(normalized - bpm) > 0.5:
                update_fields["analysis.bpm"] = round(normalized, 2)

        # 2. Detectar key si falta
        key = analysis.get("key")
        if not key or key in ('?', 'Unknown', None):
            filepath = track.get("filepath", "")
            if filepath and Path(filepath).exists():
                try:
                    duration = librosa.get_duration(path=filepath)
                    offset = max(0, (duration - 30) / 2)
                    y, sr = await run_in_threadpool(
                        librosa.load, filepath, sr=None, offset=offset, duration=30, mono=True
                    )
                    detected_key = _detect_key_chroma(y, sr)
                    if detected_key and detected_key != '?':
                        update_fields["analysis.key"] = detected_key
                except Exception as e:
                    logger.warning(f"⚠️ Error key-detect {Path(filepath).name}: {e}")

        if update_fields:
            update_fields["scanned_at"] = datetime.now(timezone.utc)
            collection.update_one({"_id": track["_id"]}, {"$set": update_fields})
            updated += 1
            name = Path(track.get("filepath", "")).name
            logger.info(f"✅ [{updated}] {name}: {update_fields}")

    logger.info(f"🏁 Re-escaneo BPM+key finalizado. Actualizados: {updated}/{len(all_tracks)}")
