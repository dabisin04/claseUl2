from flask import Blueprint, request, jsonify
from config.db import db
from models.favorite import Favorite, FavoriteSchema
from models.user import User
from models.book import Book
import uuid

ruta_favorite = Blueprint("route_favorite", __name__)
favorite_schema = FavoriteSchema()
favorites_schema = FavoriteSchema(many=True)

# 🔹 Añadir libro a favoritos
@ruta_favorite.route("/addFavorite", methods=["POST"])
def add_favorite():
    data = request.json
    user_id = data["user_id"]
    book_id = data["book_id"]

    # Verificar que el usuario existe
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404

    # Verificar que el libro existe
    book = Book.query.get(book_id)
    if not book:
        return jsonify({"error": "Libro no encontrado"}), 404

    existing = Favorite.query.filter_by(user_id=user_id, book_id=book_id).first()
    if existing:
        return favorite_schema.jsonify(existing)

    new_fav = Favorite(user_id=user_id, book_id=book_id)
    db.session.add(new_fav)
    db.session.commit()
    return favorite_schema.jsonify(new_fav)

# 🔹 Eliminar libro de favoritos
@ruta_favorite.route("/removeFavorite", methods=["DELETE"])
def remove_favorite():
    data = request.json
    user_id = data["user_id"]
    book_id = data["book_id"]

    # Verificar que el usuario existe
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404

    # Verificar que el libro existe
    book = Book.query.get(book_id)
    if not book:
        return jsonify({"error": "Libro no encontrado"}), 404

    fav = Favorite.query.filter_by(user_id=user_id, book_id=book_id).first()
    if not fav:
        return jsonify({"error": "No encontrado"}), 404

    db.session.delete(fav)
    db.session.commit()
    return favorite_schema.jsonify(fav)

# 🔹 Obtener IDs de libros favoritos por usuario
@ruta_favorite.route("/favoriteBookIds/<string:user_id>", methods=["GET"])
def get_favorite_book_ids(user_id):
    # Verificar que el usuario existe
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404

    favorites = Favorite.query.filter_by(user_id=user_id).all()
    return favorites_schema.jsonify(favorites)

# 🔹 Verificar si un libro está en favoritos
@ruta_favorite.route("/isFavorite", methods=["GET"])
def is_favorite():
    user_id = request.args.get("user_id")
    book_id = request.args.get("book_id")

    # Verificar que el usuario existe
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404

    # Verificar que el libro existe
    book = Book.query.get(book_id)
    if not book:
        return jsonify({"error": "Libro no encontrado"}), 404

    fav = Favorite.query.filter_by(user_id=user_id, book_id=book_id).first()
    if fav:
        return favorite_schema.jsonify(fav)
    return jsonify({"error": "No encontrado"}), 404
