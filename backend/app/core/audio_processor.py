import librosa
import numpy as np
import logging
import warnings
from pathlib import Path
import mutagen
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, ID3NoHeaderError

warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)

def get_metadata_robust(filepath: str):
    """
    Estrategia de lectura universal de metadatos:
    1. mutagen.File() — autodetecta formato (MP3, FLAC, M4A, OGG, WAV, etc.)
    2. ID3 crudo — para TBPM/TKEY de Rekordbox en MP3s.
    3. Fallback a nombre de archivo — 'Artista - Titulo.ext' → artist, title.
    """
    meta = {"bpm": None, "key": None, "artist": "Unknown", "title": "Unknown", "genre": "Unknown"}

    # --- Capa 0: Parsear nombre de archivo como fallback base ---
    fname = Path(filepath).stem
    if " - " in fname:
        parts = fname.split(" - ", 1)
        meta["artist"] = parts[0].strip()
        meta["title"] = parts[1].strip()
    else:
        meta["title"] = fname.strip()

    try:
        # --- Capa 1: mutagen.File() universal ---
        audio = mutagen.File(filepath, easy=True)
        if audio is not None and audio.tags:
            tags = audio.tags
            if 'title' in tags: meta['title'] = str(tags['title'][0])
            if 'artist' in tags: meta['artist'] = str(tags['artist'][0])
            if 'genre' in tags: meta['genre'] = str(tags['genre'][0])
            if 'bpm' in tags:
                try: meta['bpm'] = float(tags['bpm'][0])
                except (ValueError, IndexError): pass
            # Key: puede estar como 'initialkey' (EasyID3) o 'key'
            for key_tag in ['initialkey', 'key']:
                if key_tag in tags:
                    meta['key'] = str(tags[key_tag][0])
                    break

        # --- Capa 2: ID3 crudo (TKEY, TBPM específicos de Rekordbox) ---
        if filepath.lower().endswith('.mp3'):
            try:
                audio_raw = ID3(filepath)
                if not meta['key'] and 'TKEY' in audio_raw:
                    meta['key'] = str(audio_raw['TKEY'].text[0])
                if not meta['bpm'] and 'TBPM' in audio_raw:
                    try:
                        meta['bpm'] = float(str(audio_raw['TBPM'].text[0]))
                    except (ValueError, IndexError):
                        pass
            except (ID3NoHeaderError, Exception):
                pass

    except Exception as e:
        logger.warning(f"Error leyendo metadatos de {filepath}: {e}")

    return meta

def analyze_file(filepath: str) -> dict:
    try:
        # 1. Leer Metadatos (Rápido)
        metadata = get_metadata_robust(filepath)
        
        # LOG DE VERIFICACIÓN SOLICITADO
        logger.info(f"🔍 Procesado: {metadata['title']} | BPM: {metadata['bpm']} | Key: {metadata['key']}")
        
        # 2. Cargar Audio (Necesario para Energía y Mapa 3D)
        # Solo cargamos metadatos básicos con librosa si se necesita duración exacta, 
        # pero get_duration es rápido
        duration = librosa.get_duration(path=filepath)
        target_duration = 30.0
        
        # Cargar solo el centro (Ahorro de RAM)
        offset = (duration - target_duration) / 2 if duration > target_duration else 0.0
        load_duration = target_duration if duration > target_duration else None

        y, sr = librosa.load(filepath, sr=None, offset=offset, duration=load_duration, mono=True)
        
        if len(y) == 0: raise ValueError("Archivo vacío")

        # 3. Completar datos faltantes
        bpm = metadata['bpm']
        if not bpm:
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            bpm = float(tempo) if np.isscalar(tempo) else float(tempo[0])

        # Energía y MFCC (Siempre calculados)
        rms_frame = librosa.feature.rms(y=y)
        avg_energy = float(np.mean(rms_frame))

        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        mfcc_mean = np.mean(mfcc, axis=1).tolist()

        return {
            "title": metadata["title"],
            "artist": metadata["artist"],
            "genre": metadata["genre"],
            "key": metadata["key"],
            "bpm": round(bpm, 2),
            "energy": avg_energy,
            "mfcc": mfcc_mean,
            "duration": duration,
            "status": "success"
        }

    except Exception as e:
        logger.error(f"Error procesando {filepath}: {str(e)}")
        return {"error": str(e), "status": "failed", "filepath": filepath}