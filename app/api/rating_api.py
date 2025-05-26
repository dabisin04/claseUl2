from flask import Blueprint, request, jsonify
from config.db import db
from models.rating import BookRating, BookRatingSchema
from models.book import Book
from models.user import User
from datetime import datetime
from sqlalchemy import func
import uuid

ruta_rating = Blueprint("route_rating", __name__)
rating_schema = BookRatingSchema()
ratings_schema = BookRatingSchema(many=True)

# Utilidad para obtener por ID seguro (UUID como string)
def get_by_id(model, obj_id):
    return model.query.filter_by(id=obj_id).first()

# 📌 Upsert (crear o actualizar rating de usuario)
@ruta_rating.route("/rateBook", methods=["POST"])
def upsert_rating():
    data = request.json
    user_id = data["user_id"]
    book_id = data["book_id"]
    rating = float(data["rating"])
    timestamp = data.get("timestamp", datetime.now().isoformat())
    rating_id = f"{user_id}-{book_id}"

    # Verificar existencia
    user = get_by_id(User, user_id)
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404
    book = get_by_id(Book, book_id)
    if not book:
        return jsonify({"error": "Libro no encontrado"}), 404

    existing = BookRating.query.get(rating_id)
    if existing:
        existing.rating = rating
        existing.timestamp = timestamp
        db.session.commit()
        return rating_schema.jsonify(existing)
    else:
        new_rating = BookRating(
            id=rating_id,
            user_id=user_id,
            book_id=book_id,
            rating=rating,
            timestamp=timestamp,
        )
        db.session.add(new_rating)
        db.session.commit()
        return rating_schema.jsonify(new_rating)

# 📌 Obtener rating del usuario
@ruta_rating.route("/getUserRating", methods=["GET"])
def get_user_rating():
    user_id = request.args.get("user_id")
    book_id = request.args.get("book_id")

    user = get_by_id(User, user_id)
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404
    book = get_by_id(Book, book_id)
    if not book:
        return jsonify({"error": "Libro no encontrado"}), 404

    rating = BookRating.query.filter_by(user_id=user_id, book_id=book_id).first()
    if rating:
        return rating_schema.jsonify(rating)
    return jsonify({"error": "Rating no encontrado"}), 404

# 📌 Obtener promedio global y cantidad
@ruta_rating.route("/getGlobalAverage/<string:book_id>", methods=["GET"])
def get_global_average(book_id):
    book = get_by_id(Book, book_id)
    if not book:
        return jsonify({"error": "Libro no encontrado"}), 404

    avg, count = db.session.query(
        func.avg(BookRating.rating), func.count(BookRating.id)
    ).filter_by(book_id=book_id).first()

    return jsonify({
        "average": float(avg) if avg else 0.0,
        "count": int(count) if count else 0,
        "book_id": book_id
    })

# 📌 Obtener distribución de ratings (1 a 5)
@ruta_rating.route("/getRatingDistribution/<string:book_id>", methods=["GET"])
def get_distribution(book_id):
    book = get_by_id(Book, book_id)
    if not book:
        return jsonify({"error": "Libro no encontrado"}), 404

    distribution = db.session.query(
        func.round(BookRating.rating).label("bucket"),
        func.count().label("cnt")
    ).filter_by(book_id=book_id).group_by("bucket").all()

    dist = {i: 0 for i in range(1, 6)}
    for bucket, count in distribution:
        dist[int(bucket)] = count

    return jsonify({
        "distribution": dist,
        "book_id": book_id
    })

# 📌 Eliminar rating del usuario
@ruta_rating.route("/deleteRating", methods=["DELETE"])
def delete_rating():
    data = request.json
    user_id = data["user_id"]
    book_id = data["book_id"]

    user = get_by_id(User, user_id)
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404
    book = get_by_id(Book, book_id)
    if not book:
        return jsonify({"error": "Libro no encontrado"}), 404

    rating = BookRating.query.filter_by(user_id=user_id, book_id=book_id).first()
    if not rating:
        return jsonify({"error": "Rating no encontrado"}), 404

    db.session.delete(rating)
    db.session.commit()
    return rating_schema.jsonify(rating)

# 📌 Obtener calificaciones de usuarios para un libro (paginado)
@ruta_rating.route("/getBookRatings/<string:book_id>", methods=["GET"])
def get_book_ratings(book_id):
    book = get_by_id(Book, book_id)
    if not book:
        return jsonify({"error": "Libro no encontrado"}), 404

    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 10))

    ratings = (
        db.session.query(BookRating, User.username)
        .join(User, BookRating.user_id == User.id)
        .filter(BookRating.book_id == book_id)
        .order_by(BookRating.timestamp.desc())
        .limit(limit)
        .offset((page - 1) * limit)
        .all()
    )

    result = []
    for rating, username in ratings:
        result.append({
            "id": rating.id,
            "user_id": rating.user_id,
            "book_id": rating.book_id,
            "rating": float(rating.rating),
            "timestamp": rating.timestamp,
            "username": username,
        })

    return jsonify(result)

# 📌 Actualizar promedio y cantidad del libro
def recalculate_book_rating(book_id):
    avg, count = db.session.query(
        func.avg(BookRating.rating), func.count(BookRating.id)
    ).filter_by(book_id=book_id).first()

    book = get_by_id(Book, book_id)
    if book:
        book.rating = float(avg) if avg else 0.0
        book.ratings_count = int(count) if count else 0
        db.session.commit()
