from pymongo import MongoClient
import os
import logging
import json

# Configuración del logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración de MongoDB
MONGO_URL = os.getenv("MONGO_URL", "mongodb://mongodb_container:27017")
MONGO_DB = os.getenv("MONGO_DB", "books_db_nosql")

# Cliente de MongoDB
client = MongoClient(MONGO_URL)
db = client[MONGO_DB]

# Colecciones
users = db.users
books = db.books
chapters = db.chapters
comments = db.comments
ratings = db.ratings
favorites = db.favorites
reports = db.reports
report_alerts = db.report_alerts
user_strikes = db.user_strikes

# Función auxiliar para obtener usuario por _id
def get_user_by_id(user_id: str) -> dict | None:
    try:
        query = {"_id": user_id}
        user = users.find_one(query)
        logger.debug(f"🔎 Búsqueda de usuario por _id: {json.dumps(query)} -> {user}")
        return user
    except Exception as e:
        logger.error(f"❌ Error al buscar usuario con ID {user_id}: {str(e)}")
        return None

# Log de conexión
try:
    client.server_info()  # fuerza conexión

    query = {"_id": "1ddba770-c206-4bbd-8df5-242df95b2a08"}
    user = users.find_one(query)
    logger.info("db.users.find_one(%s): %s", query, user)

    logger.info(f"✅ Conectado a MongoDB en: {MONGO_URL}")
    logger.info(f"📂 Base de datos seleccionada: {MONGO_DB}")
    logger.info(f"📄 Total de usuarios encontrados: {users.count_documents({})}")
    logger.info(f"📚 Total de libros encontrados: {books.count_documents({})}")
except Exception as e:
    logger.error(f"❌ Error conectando a MongoDB: {str(e)}", exc_info=True)
