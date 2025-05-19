from flask import Blueprint, request, jsonify
from config.db import db
from models.rating import BookRating
from models.book import Book
from models.user import User
from datetime import datetime
import uuid

ruta_rating = Blueprint("route_rating", __name__)


# 📌 Upsert (crear o actualizar rating de usuario)
@ruta_rating.route("/rateBook", methods=["POST"])
def upsert_rating():
    data = request.json
    user_id = data["user_id"]
    book_id = data["book_id"]
    rating = float(data["rating"])
    timestamp = data.get("timestamp", datetime.now().isoformat())
    rating_id = f"{user_id}-{book_id}"

    existing = BookRating.query.get(rating_id)
    if existing:
        existing.rating = rating
        existing.timestamp = timestamp
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
    recalculate_book_rating(book_id)
    return jsonify({"message": "Rating actualizado correctamente"})


# 📌 Obtener rating del usuario
@ruta_rating.route("/getUserRating", methods=["GET"])
def get_user_rating():
    user_id = request.args.get("user_id")
    book_id = request.args.get("book_id")
    rating = BookRating.query.filter_by(user_id=user_id, book_id=book_id).first()

    return jsonify({"rating": rating.rating if rating else None})


# 📌 Obtener promedio global y cantidad
@ruta_rating.route("/getGlobalAverage/<string:book_id>", methods=["GET"])
def get_global_average(book_id):
    from sqlalchemy import func

    avg, count = db.session.query(
        func.avg(BookRating.rating), func.count(BookRating.id)
    ).filter_by(book_id=book_id).first()

    return jsonify({
        "average": float(avg) if avg else 0.0,
        "count": int(count) if count else 0
    })


# 📌 Obtener distribución de ratings (1 a 5)
@ruta_rating.route("/getRatingDistribution/<string:book_id>", methods=["GET"])
def get_distribution(book_id):
    from sqlalchemy import func

    distribution = db.session.query(
        func.round(BookRating.rating).label("bucket"),
        func.count().label("cnt")
    ).filter_by(book_id=book_id).group_by("bucket").all()

    dist = {i: 0 for i in range(1, 6)}
    for bucket, count in distribution:
        dist[int(bucket)] = count

    return jsonify(dist)


# 📌 Eliminar rating del usuario
@ruta_rating.route("/deleteRating", methods=["DELETE"])
def delete_rating():
    data = request.json
    user_id = data["user_id"]
    book_id = data["book_id"]

    BookRating.query.filter_by(user_id=user_id, book_id=book_id).delete()
    db.session.commit()

    recalculate_book_rating(book_id)
    return jsonify({"message": "Rating eliminado"})


# 📌 Obtener calificaciones de usuarios para un libro (paginado)
@ruta_rating.route("/getBookRatings/<string:book_id>", methods=["GET"])
def get_book_ratings(book_id):
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


# 📌 Actualiza el promedio y cantidad en la tabla `books`
def recalculate_book_rating(book_id):
    from sqlalchemy import func

    avg, count = db.session.query(
        func.avg(BookRating.rating), func.count(BookRating.id)
    ).filter_by(book_id=book_id).first()

    book = Book.query.get(book_id)
    if book:
        book.rating = float(avg) if avg else 0.0
        book.ratings_count = int(count) if count else 0
        db.session.commit()
