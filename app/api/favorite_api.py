from flask import Blueprint, request, jsonify
from config.db import db
from models.favorite import Favorite, FavoriteSchema
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

    existing = Favorite.query.filter_by(user_id=user_id, book_id=book_id).first()
    if existing:
        return jsonify({"message": "Ya está en favoritos"}), 200

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

    fav = Favorite.query.filter_by(user_id=user_id, book_id=book_id).first()
    if not fav:
        return jsonify({"error": "No encontrado"}), 404

    db.session.delete(fav)
    db.session.commit()
    return jsonify({"message": "Eliminado de favoritos"})

# 🔹 Obtener IDs de libros favoritos por usuario
@ruta_favorite.route("/favoriteBookIds/<string:user_id>", methods=["GET"])
def get_favorite_book_ids(user_id):
    favorites = Favorite.query.filter_by(user_id=user_id).all()
    book_ids = [fav.book_id for fav in favorites]
    return jsonify(book_ids)

# 🔹 Verificar si un libro está en favoritos
@ruta_favorite.route("/isFavorite", methods=["GET"])
def is_favorite():
    user_id = request.args.get("user_id")
    book_id = request.args.get("book_id")
    fav = Favorite.query.filter_by(user_id=user_id, book_id=book_id).first()
    return jsonify({"is_favorite": bool(fav)})
