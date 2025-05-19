from flask import Blueprint, request, jsonify
from config.db import db
from models.chapter import Chapter, ChapterSchema
import json
from datetime import datetime

ruta_chapter = Blueprint("route_chapter", __name__)

chapter_schema = ChapterSchema()
chapters_schema = ChapterSchema(many=True)

@ruta_chapter.route("/chapters/<string:book_id>", methods=["GET"])
def get_chapters_by_book(book_id):
    chapters = Chapter.query.filter_by(book_id=book_id).order_by(Chapter.chapter_number).all()
    return jsonify(chapters_schema.dump(chapters))

@ruta_chapter.route("/addChapter", methods=["POST"])
def add_chapter():
    data = request.json
    new_chapter = Chapter(
        id=data.get("id"),
        book_id=data.get("book_id"),
        title=data.get("title"),
        content=data.get("content"),
        upload_date=data.get("upload_date", datetime.now().isoformat()),
        publication_date=datetime.fromisoformat(data["publication_date"]) if data.get("publication_date") else None,
        chapter_number=data.get("chapter_number"),
        views=data.get("views", 0),
        rating=data.get("rating", 0.0),
        ratings_count=data.get("ratings_count", 0),
        reports=data.get("reports", 0)
    )
    db.session.add(new_chapter)
    db.session.commit()
    return chapter_schema.jsonify(new_chapter)

@ruta_chapter.route("/updateChapter", methods=["PUT"])
def update_chapter():
    data = request.json
    chapter = Chapter.query.get(data.get("id"))
    if not chapter:
        return jsonify({"error": "Capítulo no encontrado"}), 404

    chapter.title = data.get("title", chapter.title)
    chapter.content = json.dumps(data["content"]) if isinstance(data.get("content"), dict) else chapter.content
    chapter.chapter_number = data.get("chapter_number", chapter.chapter_number)
    chapter.publication_date = datetime.fromisoformat(data["publication_date"]) if data.get("publication_date") else chapter.publication_date
    db.session.commit()
    return chapter_schema.jsonify(chapter)

@ruta_chapter.route("/deleteChapter/<string:chapter_id>", methods=["DELETE"])
def delete_chapter(chapter_id):
    chapter = Chapter.query.get(chapter_id)
    if not chapter:
        return jsonify({"error": "Capítulo no encontrado"}), 404
    db.session.delete(chapter)
    db.session.commit()
    return jsonify({"message": "Capítulo eliminado"})

@ruta_chapter.route("/updateChapterViews/<string:chapter_id>", methods=["PUT"])
def update_chapter_views(chapter_id):
    db.session.query(Chapter).filter(Chapter.id == chapter_id).update({
        Chapter.views: Chapter.views + 1
    })
    db.session.commit()
    return jsonify({"message": "Vistas del capítulo actualizadas"})

@ruta_chapter.route("/rateChapter", methods=["POST"])
def rate_chapter():
    data = request.json
    chapter_id = data["chapter_id"]
    user_id = data["user_id"]
    rating = float(data["rating"])
    rating_id = f"{user_id}-{chapter_id}"

    db.session.execute(
        "INSERT INTO chapter_ratings (id, user_id, chapter_id, rating) "
        "VALUES (:id, :user_id, :chapter_id, :rating) "
        "ON DUPLICATE KEY UPDATE rating = :rating",
        {
            "id": rating_id,
            "user_id": user_id,
            "chapter_id": chapter_id,
            "rating": rating
        }
    )
    db.session.commit()

    result = db.session.execute(
        "SELECT rating FROM chapter_ratings WHERE chapter_id = :chapter_id",
        {"chapter_id": chapter_id}
    ).fetchall()

    if result:
        avg = sum([r[0] for r in result]) / len(result)
        db.session.query(Chapter).filter(Chapter.id == chapter_id).update({"rating": avg})
        db.session.commit()

    return jsonify({"message": "Puntuación registrada"})

@ruta_chapter.route("/updateChapterContent/<string:chapter_id>", methods=["PUT"])
def update_chapter_content(chapter_id):
    content = request.json.get("content", {})
    db.session.query(Chapter).filter_by(id=chapter_id).update({
        "content": json.dumps(content)
    })
    db.session.commit()
    return jsonify({"message": "Contenido actualizado"})

@ruta_chapter.route("/updateChapterPublicationDate/<string:chapter_id>", methods=["PUT"])
def update_chapter_publication_date(chapter_id):
    date_str = request.json.get("publication_date")
    pub_date = datetime.fromisoformat(date_str) if date_str else None
    db.session.query(Chapter).filter_by(id=chapter_id).update({
        "publication_date": pub_date
    })
    db.session.commit()
    return jsonify({"message": "Fecha de publicación actualizada"})

@ruta_chapter.route("/updateChapterDetails/<string:chapter_id>", methods=["PUT"])
def update_chapter_details(chapter_id):
    data = request.json
    fields = {}
    if "title" in data:
        fields["title"] = data["title"]
    if "description" in data:
        fields["description"] = data["description"]

    if fields:
        db.session.query(Chapter).filter_by(id=chapter_id).update(fields)
        db.session.commit()
        return jsonify({"message": "Detalles actualizados"})
    return jsonify({"message": "Sin cambios"})

@ruta_chapter.route("/searchChapters", methods=["GET"])
def search_chapters():
    query = request.args.get("query", "")
    chapters = Chapter.query.filter(
        Chapter.title.ilike(f"%{query}%"),
        Chapter.reports == 0  # si usas is_trashed = False, cámbialo aquí
    ).all()
    return jsonify(chapters_schema.dump(chapters))
