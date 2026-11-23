"""
Configuración centralizada del sistema ID.
Todas las constantes y rutas se definen aquí.
"""
from pathlib import Path

# --- MongoDB ---
MONGO_URI = "mongodb://admin:password123@127.0.0.1:27018/?authSource=admin&directConnection=true"
MONGO_DB_NAME = "id_audio_core"

import os

# --- Rutas de archivos ---
BASE_DIR = Path(__file__).resolve().parent.parent
LIBRARY_PATH = Path(os.getenv("LIBRARY_PATH", "/home/juand2g/Música/music"))

# --- Audio Processing ---
AUDIO_EXTENSIONS = ["*.mp3", "*.wav", "*.flac", "*.aac", "*.ogg", "*.m4a"]
AUDIO_SAMPLE_DURATION = 30.0  # Segundos a analizar del centro del track

# --- UMAP ---
UMAP_N_COMPONENTS = 3
UMAP_N_NEIGHBORS = 15
UMAP_MIN_DIST = 0.1
UMAP_RANDOM_STATE = 42
