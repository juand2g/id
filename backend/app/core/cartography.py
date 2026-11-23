import numpy as np
from pymongo import MongoClient
import logging
import random
try:
    import umap
except ImportError:
    umap = None

logger = logging.getLogger(__name__)

# Configuración de Mongo (Debería coincidir con main.py)
MONGO_URI = "mongodb://admin:password123@127.0.0.1:27018/?authSource=admin&directConnection=true"

def calculate_umap_coords():
    """
    Calcula coodenadas 3D (UMAP) para todas las canciones con MFCC.
    Actualiza el campo 'umap_coords' en cada documento.
    """
    client = MongoClient(MONGO_URI)
    db = client["id_audio_core"]
    collection = db["tracks"]
    
    try:
        # 1. Obtener datos
        tracks = list(collection.find(
            {"analysis.mfcc": {"$exists": True, "$ne": None}},
            {"_id": 1, "analysis.mfcc": 1}
        ))
        
        count = len(tracks)
        logger.info(f"Calculando mapa para {count} tracks...")
        
        if count == 0:
            return
            
        # 2. Preparar matriz de datos
        data = np.array([t["analysis"]["mfcc"] for t in tracks])
        
        # 3. Calcular Embeddings
        embeddings = []
        
        # Estrategia según cantidad de datos
        if count < 5 or umap is None:
            if umap is None and count >= 5:
                logger.warning("UMAP no instalado. Usando random fallback.")
            else:
                logger.info("Pocos datos (<5). Usando random fallback.")
                
            # Generar coordenadas aleatorias en rango similar a UMAP (-10 a 10 aprox)
            embeddings = np.random.uniform(-10, 10, size=(count, 3))
            
        else:
            logger.info("Ejecutando UMAP n_components=3...")
            reducer = umap.UMAP(
                n_components=3, 
                random_state=42, 
                n_neighbors=min(15, count - 1), # Ajuste para datasets pequeños
                min_dist=0.1
            )
            embeddings = reducer.fit_transform(data)
            
        # 4. Actualizar Base de Datos
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
                
        logger.info(f"Mapa actualizado. Tracks procesados: {updates}/{count}")
        
    except Exception as e:
        logger.error(f"Error en calculate_umap_coords: {e}")
    finally:
        client.close()
