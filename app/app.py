from flask import Flask
from config.db import app, db  # db importado explícitamente para create_all

# Importar Blueprints
from api.book_api import ruta_book
from api.chapters_api import ruta_chapter
from api.comment_api import ruta_comment
from api.rating_api import ruta_rating
from api.user_api import ruta_user
from api.favorite_api import ruta_favorite

# Registrar Blueprints con prefijo /api
app.register_blueprint(ruta_user, url_prefix="/api")
app.register_blueprint(ruta_book, url_prefix="/api")
app.register_blueprint(ruta_chapter, url_prefix="/api")
app.register_blueprint(ruta_comment, url_prefix="/api")
app.register_blueprint(ruta_rating, url_prefix="/api")
app.register_blueprint(ruta_favorite, url_prefix="/api")

# Ruta principal
@app.route("/")
def index():
    return "✅ API de libros funcionando correctamente"

# Iniciar servidor y crear las tablas si no existen
if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Crea todas las tablas definidas en modelos
    app.run(debug=True, port=5000, host="0.0.0.0")
