"""
Servicio de cartografía: generación de coordenadas 3D con UMAP.
"""
import numpy as np
import logging

try:
    import umap
except ImportError:
    umap = None

from app.config import UMAP_N_COMPONENTS, UMAP_N_NEIGHBORS, UMAP_MIN_DIST, UMAP_RANDOM_STATE
from app.database import get_collection

logger = logging.getLogger(__name__)


def calculate_umap_coords():
    """
    Calcula coordenadas 3D (UMAP) para todos los tracks con MFCC.
    Utiliza features Tier 1 + Tier 2 concatenados para un mapeo más rico.
    Actualiza el campo 'umap_coords' en cada documento.
    """
    collection = get_collection("tracks")

    try:
        # 1. Obtener tracks con al menos MFCC
        tracks = list(collection.find(
            {"analysis.mfcc": {"$exists": True, "$ne": None}},
            {
                "_id": 1,
                "analysis.mfcc": 1,
                "analysis.energy": 1,
                "analysis.bpm": 1,
                "analysis.spectral_centroid": 1,
                "analysis.spectral_rolloff": 1,
                "analysis.zero_crossing_rate": 1,
                "analysis.onset_rate": 1,
            }
        ))

        count = len(tracks)
        logger.info(f"🗺️ Calculando mapa para {count} tracks...")

        if count == 0:
            logger.warning("No hay tracks con features para mapear.")
            return

        # 2. Construir vector de features por track
        feature_vectors = []
        for t in tracks:
            a = t["analysis"]
            # Concatenar: MFCC (13) + escalares normalizados
            vec = list(a["mfcc"])
            vec.append(a.get("energy", 0))
            vec.append((a.get("bpm", 120) - 60) / 140)  # Normalizar BPM 60-200 → 0-1
            vec.append(a.get("spectral_centroid", 0) / 8000)  # Normalizar Hz
            vec.append(a.get("spectral_rolloff", 0) / 16000)
            vec.append(a.get("zero_crossing_rate", 0))
            vec.append(a.get("onset_rate", 0) / 20)  # Normalizar
            feature_vectors.append(vec)

        data = np.array(feature_vectors, dtype=np.float64)

        # 3. Calcular embeddings
        if count < 5 or umap is None:
            if umap is None and count >= 5:
                logger.warning("⚠️ UMAP no instalado. Usando random fallback.")
            else:
                logger.info("Pocos datos (<5). Usando random fallback.")
            embeddings = np.random.uniform(-10, 10, size=(count, 3))
        else:
            logger.info(f"🧠 Ejecutando UMAP (n_components={UMAP_N_COMPONENTS})...")
            reducer = umap.UMAP(
                n_components=UMAP_N_COMPONENTS,
                random_state=UMAP_RANDOM_STATE,
                n_neighbors=min(UMAP_N_NEIGHBORS, count - 1),
                min_dist=UMAP_MIN_DIST,
            )
            embeddings = reducer.fit_transform(data)

        # 4. Guardar coordenadas en BD
        updates = 0
        for track, coords in zip(tracks, embeddings):
            result = collection.update_one(
                {"_id": track["_id"]},
                {"$set": {
                    "umap_coords": {
                        "x": float(coords[0]),
                        "y": float(coords[1]),
                        "z": float(coords[2])
                    }
                }}
            )
            if result.modified_count > 0:
                updates += 1

        logger.info(f"✅ Mapa actualizado. Tracks procesados: {updates}/{count}")

    except Exception as e:
        logger.error(f"❌ Error en calculate_umap_coords: {e}")
