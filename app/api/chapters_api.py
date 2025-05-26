from flask import Blueprint, request, jsonify
from config.db import db
from models.chapter import Chapter, ChapterSchema
from models.book import Book
from models.user import User
from datetime import datetime
import uuid
import json

ruta_chapter = Blueprint("route_chapter", __name__)

chapter_schema = ChapterSchema()
chapters_schema = ChapterSchema(many=True)

@ruta_chapter.route("/chapters/<string:book_id>", methods=["GET"])
def get_chapters_by_book(book_id):
    # Verificar que el libro existe
    book = Book.query.get(book_id)
    if not book:
        return jsonify({"error": "Libro no encontrado"}), 404

    chapters = Chapter.query.filter_by(book_id=book_id).order_by(Chapter.chapter_number).all()
    return chapters_schema.jsonify(chapters)

@ruta_chapter.route("/addChapter", methods=["POST"])
def add_chapter():
    data = request.json
    book_id = data.get("book_id")
    user_id = data.get("user_id")

    # Verificar que el libro existe
    book = Book.query.get(book_id)
    if not book:
        return jsonify({"error": "Libro no encontrado"}), 404

    # Verificar que el usuario existe
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404

    # Verificar que el usuario es el autor del libro
    if book.user_id != user_id:
        return jsonify({"error": "No tienes permiso para crear capítulos en este libro"}), 403

    new_chapter = Chapter(
        id=data.get("id") or str(uuid.uuid4()),
        book_id=book_id,
        title=data.get("title", ""),
        content=data.get("content", ""),
        chapter_number=data.get("chapter_number", 0),
        views=data.get("views", 0),
        rating=data.get("rating", 0.0),
        ratings_count=data.get("ratings_count", 0),
        reports=data.get("reports", 0),
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat()
    )
    db.session.add(new_chapter)
    db.session.commit()
    return chapter_schema.jsonify(new_chapter), 201

@ruta_chapter.route("/updateChapter/<string:chapter_id>", methods=["PUT"])
def update_chapter(chapter_id):
    data = request.json
    user_id = data.get("user_id")

    # Verificar que el usuario existe
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404

    chapter = Chapter.query.get(chapter_id)
    if not chapter:
        return jsonify({"error": "Capítulo no encontrado"}), 404

    # Verificar que el usuario es el autor del libro
    book = Book.query.get(chapter.book_id)
    if book.user_id != user_id:
        return jsonify({"error": "No tienes permiso para editar este capítulo"}), 403

    chapter.title = data.get("title", chapter.title)
    chapter.content = json.dumps(data["content"]) if isinstance(data.get("content"), dict) else chapter.content
    chapter.chapter_number = data.get("chapter_number", chapter.chapter_number)
    chapter.updated_at = datetime.now().isoformat()
    
    db.session.commit()
    return chapter_schema.jsonify(chapter)

@ruta_chapter.route("/deleteChapter/<string:chapter_id>", methods=["DELETE"])
def delete_chapter(chapter_id):
    data = request.json
    user_id = data.get("user_id")

    # Verificar que el usuario existe
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404

    chapter = Chapter.query.get(chapter_id)
    if not chapter:
        return jsonify({"error": "Capítulo no encontrado"}), 404

    # Verificar que el usuario es el autor del libro
    book = Book.query.get(chapter.book_id)
    if book.user_id != user_id:
        return jsonify({"error": "No tienes permiso para eliminar este capítulo"}), 403

    db.session.delete(chapter)
    db.session.commit()
    return chapter_schema.jsonify(chapter)

@ruta_chapter.route("/updateChapterViews/<string:chapter_id>", methods=["PUT"])
def update_chapter_views(chapter_id):
    chapter = Chapter.query.get(chapter_id)
    if not chapter:
        return jsonify({"error": "Capítulo no encontrado"}), 404

    chapter.views += 1
    chapter.updated_at = datetime.now().isoformat()
    db.session.commit()
    return chapter_schema.jsonify(chapter)

@ruta_chapter.route("/updateChapterContent/<string:chapter_id>", methods=["PUT"])
def update_chapter_content(chapter_id):
    data = request.json
    user_id = data.get("user_id")
    content = data.get("content", {})

    # Verificar que el usuario existe
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404

    chapter = Chapter.query.get(chapter_id)
    if not chapter:
        return jsonify({"error": "Capítulo no encontrado"}), 404

    # Verificar que el usuario es el autor del libro
    book = Book.query.get(chapter.book_id)
    if book.user_id != user_id:
        return jsonify({"error": "No tienes permiso para editar este capítulo"}), 403

    chapter.content = json.dumps(content)
    chapter.updated_at = datetime.now().isoformat()
    db.session.commit()
    return chapter_schema.jsonify(chapter)

@ruta_chapter.route("/updateChapterPublicationDate/<string:chapter_id>", methods=["PUT"])
def update_chapter_publication_date(chapter_id):
    data = request.json
    user_id = data.get("user_id")
    date_str = data.get("publication_date")

    # Verificar que el usuario existe
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404

    chapter = Chapter.query.get(chapter_id)
    if not chapter:
        return jsonify({"error": "Capítulo no encontrado"}), 404

    # Verificar que el usuario es el autor del libro
    book = Book.query.get(chapter.book_id)
    if book.user_id != user_id:
        return jsonify({"error": "No tienes permiso para editar este capítulo"}), 403

    chapter.publication_date = datetime.fromisoformat(date_str) if date_str else None
    chapter.updated_at = datetime.now().isoformat()
    db.session.commit()
    return chapter_schema.jsonify(chapter)

@ruta_chapter.route("/updateChapterDetails/<string:chapter_id>", methods=["PUT"])
def update_chapter_details(chapter_id):
    data = request.json
    user_id = data.get("user_id")

    # Verificar que el usuario existe
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404

    chapter = Chapter.query.get(chapter_id)
    if not chapter:
        return jsonify({"error": "Capítulo no encontrado"}), 404

    # Verificar que el usuario es el autor del libro
    book = Book.query.get(chapter.book_id)
    if book.user_id != user_id:
        return jsonify({"error": "No tienes permiso para editar este capítulo"}), 403

    if "title" in data:
        chapter.title = data["title"]
    if "description" in data:
        chapter.description = data["description"]

    chapter.updated_at = datetime.now().isoformat()
    db.session.commit()
    return chapter_schema.jsonify(chapter)

@ruta_chapter.route("/searchChapters", methods=["GET"])
def search_chapters():
    query = request.args.get("query", "")
    chapters = Chapter.query.filter(
        Chapter.title.ilike(f"%{query}%"),
        Chapter.reports == 0
    ).all()
    return chapters_schema.jsonify(chapters)
