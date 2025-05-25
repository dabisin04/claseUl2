from flask import Flask
from config.db import app, db  # db importado explícitamente para create_all
import argparse

# Importar Blueprints
from api.book_api import ruta_book
from api.chapters_api import ruta_chapter
from api.comment_api import ruta_comment
from api.rating_api import ruta_rating
from api.user_api import ruta_user
from api.favorite_api import ruta_favorite
from api.reports_api import ruta_reportes  # ✅ Nuevo blueprint

# Registrar Blueprints con prefijo /api
app.register_blueprint(ruta_user, url_prefix="/api")
app.register_blueprint(ruta_book, url_prefix="/api")
app.register_blueprint(ruta_chapter, url_prefix="/api")
app.register_blueprint(ruta_comment, url_prefix="/api")
app.register_blueprint(ruta_rating, url_prefix="/api")
app.register_blueprint(ruta_favorite, url_prefix="/api")
app.register_blueprint(ruta_reportes, url_prefix="/api")  # ✅ Registro nuevo

# Ruta principal
@app.route("/")
def index():
    return "✅ API de libros funcionando correctamente"

# Iniciar servidor y crear las tablas si no existen
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=5001)
    args = parser.parse_args()
    
    with app.app_context():
        db.create_all()  # Crea todas las tablas definidas en modelos
    app.run(debug=True, port=args.port, host="0.0.0.0")
