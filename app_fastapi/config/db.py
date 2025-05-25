from pymongo import MongoClient
import os

# Configuración de MongoDB
MONGO_URL = os.getenv("MONGO_URL", "mongodb://mongodb_container:27017")
MONGO_DB = os.getenv("MONGO_DB", "the_library")

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
