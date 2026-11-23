"""
Servicio de extracción de features acústicos.
Tier 1 (Core) + Tier 2 (Espectral) usando Librosa y Mutagen.
"""
import librosa
import numpy as np
import logging
import warnings
from pathlib import Path
import mutagen
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, ID3NoHeaderError

from app.config import AUDIO_SAMPLE_DURATION

warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)


def get_metadata_robust(filepath: str) -> dict:
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


def extract_spectral_features(y: np.ndarray, sr: int) -> dict:
    """
    Extrae features espectrales Tier 2:
    - Spectral Centroid (brillo)
    - Spectral Contrast (plenitud)
    - Spectral Rolloff (calidez)
    - Zero Crossing Rate (textura)
    - Chroma (perfil armónico)
    - Onset Rate (densidad rítmica)
    """
    features = {}

    # Spectral Centroid — "brillo" del sonido (Hz promedio ponderado)
    centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
    features["spectral_centroid"] = float(np.mean(centroid))

    # Spectral Contrast — diferencia picos/valles por banda
    contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
    features["spectral_contrast"] = np.mean(contrast, axis=1).tolist()

    # Spectral Rolloff — frecuencia bajo la cual está el 85% de la energía
    rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)
    features["spectral_rolloff"] = float(np.mean(rolloff))

    # Zero Crossing Rate — percusivo vs tonal
    zcr = librosa.feature.zero_crossing_rate(y)
    features["zero_crossing_rate"] = float(np.mean(zcr))

    # Chroma — perfil armónico (12 notas)
    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    features["chroma"] = np.mean(chroma, axis=1).tolist()

    # Onset Rate — eventos rítmicos por segundo
    onsets = librosa.onset.onset_detect(y=y, sr=sr)
    duration = len(y) / sr
    features["onset_rate"] = float(len(onsets) / duration) if duration > 0 else 0.0

    return features


# ── Helper: normalizar BPM al rango DJ ──────────────────────────────
# librosa frecuentemente detecta la octava baja (75 en vez de 150).
# Rango estándar DJ: 70-180 BPM.
def _normalize_bpm_dj(bpm: float) -> float:
    """Dobla o divide el BPM hasta llevarlo al rango 70-180."""
    if bpm <= 0:
        return bpm
    while bpm < 70:
        bpm *= 2
    while bpm > 180:
        bpm /= 2
    return bpm


# ── Helper: detectar key musical vía chroma ─────────────────────────
_KEY_NAMES_MAJOR = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']
_KEY_NAMES_MINOR = ['Cm', 'C#m', 'Dm', 'Ebm', 'Em', 'Fm', 'F#m', 'Gm', 'G#m', 'Am', 'Bbm', 'Bm']

# Krumhansl-Kessler key profiles
_MAJOR_PROFILE = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
_MINOR_PROFILE = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])

def _detect_key_chroma(y: np.ndarray, sr: int) -> str:
    """Detectar tonalidad con correlación chroma + Krumhansl-Kessler."""
    try:
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
        chroma_mean = np.mean(chroma, axis=1)
        # Normalizar
        chroma_mean = chroma_mean / (np.max(chroma_mean) + 1e-8)

        best_corr = -1
        best_key = 'C'

        for i in range(12):
            # Rotar el perfil para cada tonalidad
            major_shifted = np.roll(_MAJOR_PROFILE, i)
            minor_shifted = np.roll(_MINOR_PROFILE, i)

            corr_major = np.corrcoef(chroma_mean, major_shifted)[0, 1]
            corr_minor = np.corrcoef(chroma_mean, minor_shifted)[0, 1]

            if corr_major > best_corr:
                best_corr = corr_major
                best_key = _KEY_NAMES_MAJOR[i]
            if corr_minor > best_corr:
                best_corr = corr_minor
                best_key = _KEY_NAMES_MINOR[i]

        return best_key
    except Exception:
        return '?'


def analyze_file(filepath: str) -> dict:
    """
    Análisis completo de un archivo de audio.
    Retorna metadatos + features Tier 1 (Core) + Tier 2 (Espectral).
    """
    try:
        # 1. Metadatos ID3
        metadata = get_metadata_robust(filepath)
        logger.info(f"🔍 Procesado: {metadata['title']} | BPM: {metadata['bpm']} | Key: {metadata['key']}")

        # 2. Duración total
        duration = librosa.get_duration(path=filepath)

        # 3. Cargar segmento central (ahorro de RAM)
        offset = (duration - AUDIO_SAMPLE_DURATION) / 2 if duration > AUDIO_SAMPLE_DURATION else 0.0
        load_duration = AUDIO_SAMPLE_DURATION if duration > AUDIO_SAMPLE_DURATION else None
        y, sr = librosa.load(filepath, sr=None, offset=offset, duration=load_duration, mono=True)

        if len(y) == 0:
            raise ValueError("Archivo vacío")

        # --- TIER 1: Core Features ---

        # BPM (fallback a librosa si ID3 no tiene)
        bpm = metadata['bpm']
        if not bpm:
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            bpm = float(tempo) if np.isscalar(tempo) else float(tempo[0])

        # Normalizar BPM al rango DJ (70-180)
        # librosa detecta octava baja (75 en vez de 150) frecuentemente
        bpm = _normalize_bpm_dj(bpm)

        # Key (fallback a detección chroma si no hay tag)
        key = metadata['key']
        if not key or key == '?' or key == 'Unknown':
            key = _detect_key_chroma(y, sr)

        # Energy (RMS normalizado 0-1)
        rms = librosa.feature.rms(y=y)
        energy = float(np.mean(rms))
        # Normalizar a 0-1 (RMS típico para música está entre 0.01 y 0.3)
        energy_normalized = min(1.0, energy / 0.3)

        # MFCC (textura tímbrica — 13 coeficientes)
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        mfcc_mean = np.mean(mfcc, axis=1).tolist()

        # --- TIER 2: Spectral Features ---
        spectral = extract_spectral_features(y, sr)

        return {
            "title": metadata["title"],
            "artist": metadata["artist"],
            "genre": metadata["genre"],
            "key": key or metadata["key"],
            "bpm": round(bpm, 2),
            "energy": energy_normalized,
            "energy_raw": energy,
            "mfcc": mfcc_mean,
            "duration": duration,
            # Tier 2
            "spectral_centroid": spectral["spectral_centroid"],
            "spectral_contrast": spectral["spectral_contrast"],
            "spectral_rolloff": spectral["spectral_rolloff"],
            "zero_crossing_rate": spectral["zero_crossing_rate"],
            "chroma": spectral["chroma"],
            "onset_rate": spectral["onset_rate"],
            "status": "success"
        }

    except Exception as e:
        logger.error(f"❌ Error procesando {filepath}: {str(e)}")
        return {"error": str(e), "status": "failed", "filepath": filepath}
