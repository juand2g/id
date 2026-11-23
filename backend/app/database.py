"""
Conexión MongoDB compartida.
Todos los servicios importan `db` y `get_collection()` desde aquí.
"""
from pymongo import MongoClient
from app.config import MONGO_URI, MONGO_DB_NAME
import logging

logger = logging.getLogger(__name__)

client: MongoClient = MongoClient(MONGO_URI)
db = client[MONGO_DB_NAME]


def get_collection(name: str):
    """Obtiene una colección de la BD."""
    return db[name]


def ping():
    """Verifica la conexión a MongoDB."""
    try:
        client.admin.command("ping")
        logger.info("✅ Conectado exitosamente a MongoDB")
        return True
    except Exception as e:
        logger.error(f"❌ Error conectando a MongoDB: {e}")
        return False


def close():
    """Cierra la conexión a MongoDB."""
    client.close()
