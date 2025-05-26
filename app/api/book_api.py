import traceback
from flask import Blueprint, request, jsonify
from config.db import db
from models.book import Book, BookSchema
from models.user import User
from models.chapter import Chapter
from datetime import datetime
import uuid
import json

# Configurar logger de nivel debug
def log(msg, *args):
    print(msg.format(*args))

ruta_book = Blueprint("route_book", __name__)

book_schema = BookSchema()
books_schema = BookSchema(many=True)

@ruta_book.route("/books", methods=["GET"])
def get_all_books():
    try:
        trashed = request.args.get("trashed", "false").lower() == "true"
        log("[GET /books] Query trashed={0}", trashed)
        books = Book.query.filter_by(is_trashed=trashed).filter(Book.status != "alert").all()
        return books_schema.jsonify(books)
    except Exception as e:
        log("[GET /books] Error: {0}", e)
        traceback.print_exc()
        return jsonify({"error": "Internal Server Error"}), 500
    
@ruta_book.route("/alertedBooks", methods=["GET"])
def get_alerted_books():
    books = Book.query.filter(Book.status == "alert", Book.is_trashed == False).all()
    return books_schema.jsonify(books)

@ruta_book.route("/book/<string:book_id>", methods=["GET"])
def get_book_by_id(book_id):
    log("[GET /book/{0}] Called", book_id)
    book = Book.query.get(book_id)
    if not book:
        log("[GET /book/{0}] Not found", book_id)
        return jsonify({"error": "Libro no encontrado"}), 404
    return book_schema.jsonify(book)

@ruta_book.route("/addBook", methods=["POST"])
def add_book():
    try:
        data = request.json or {}
        log("[POST /addBook] 🔍 DATOS COMPLETOS DEL REQUEST:")
        log("[POST /addBook] 📦 Payload JSON: {0}", json.dumps(data, indent=2))
        log("[POST /addBook] 📦 Headers: {0}", json.dumps(dict(request.headers), indent=2))
        log("[POST /addBook] 📦 Método: {0}", request.method)
        log("[POST /addBook] 📦 URL: {0}", request.url)
        log("[POST /addBook] 📦 Content-Type: {0}", request.content_type)
        log("[POST /addBook] 📦 Content-Length: {0}", request.content_length)
        
        # Verificar que el usuario existe
        user = User.query.get(data.get("author_id"))
        if not user:
            log("[POST /addBook] ❌ User not found")
            return jsonify({"error": "El usuario no existe"}), 404

        book_id = data.get("id") or str(uuid.uuid4())
        existing = Book.query.get(book_id)
        if existing:
            log("[POST /addBook] ❌ Conflict: book {0} already exists", book_id)
            return jsonify({"error": "Ya existe un libro con ese ID"}), 409

        log("[POST /addBook] 📦 DATOS DEL LIBRO A CREAR:")
        log("[POST /addBook] 📦 ID: {0}", book_id)
        log("[POST /addBook] 📦 Título: {0}", data.get("title"))
        log("[POST /addBook] 📦 Autor: {0}", data.get("author_id"))
        log("[POST /addBook] 📦 Género: {0}", data.get("genre"))
        log("[POST /addBook] 📦 Géneros adicionales: {0}", data.get("additional_genres"))
        log("[POST /addBook] 📦 Descripción: {0}", data.get("description"))
        log("[POST /addBook] 📦 Status: {0}", data.get("status"))
        log("[POST /addBook] 📦 Tipo de contenido: {0}", data.get("content_type"))
        log("[POST /addBook] 📦 Fecha publicación: {0}", data.get("publication_date"))
        log("[POST /addBook] 📦 Vistas: {0}", data.get("views"))
        log("[POST /addBook] 📦 Rating: {0}", data.get("rating"))
        log("[POST /addBook] 📦 Conteo de ratings: {0}", data.get("ratings_count"))
        log("[POST /addBook] 📦 Reportes: {0}", data.get("reports"))
        log("[POST /addBook] 📦 En papelera: {0}", data.get("is_trashed"))
        log("[POST /addBook] 📦 Tiene capítulos: {0}", data.get("has_chapters"))
        log("[POST /addBook] 📦 Contenido: {0}", json.dumps(data.get("content"), indent=2) if data.get("content") else "Sin contenido")

        new_book = Book(
            id=book_id,
            author_id=data.get("author_id"),
            title=data.get("title", "Sin título"),
            description=data.get("description"),
            genre=data.get("genre", "Sin género"),
            additional_genres=data.get("additional_genres", []),
            upload_date=datetime.now().isoformat(),
            publication_date=datetime.fromisoformat(data["publication_date"]) if data.get("publication_date") else None,
            views=data.get("views", 0),
            rating=data.get("rating", 0.0),
            ratings_count=data.get("ratings_count", 0),
            reports=data.get("reports", 0),
            content=data.get("content"),
            is_trashed=data.get("is_trashed", False),
            has_chapters=data.get("has_chapters", False),
            status=data.get("status", "pending"),
            content_type=data.get("content_type", "book")
        )
        db.session.add(new_book)
        db.session.commit()
        log("[POST /addBook] ✅ Book saved: {0}", book_id)
        return book_schema.jsonify(new_book), 201
    except Exception as e:
        log("[POST /addBook] ❌ Error: {0}", e)
        traceback.print_exc()
        db.session.rollback()
        return jsonify({"error": "Error interno del servidor"}), 500

@ruta_book.route("/deleteBook/<string:book_id>", methods=["DELETE"])
def delete_book(book_id):
    log("[DELETE /deleteBook/{0}] Called", book_id)
    book = Book.query.get(book_id)
    if not book:
        log("[DELETE /deleteBook/{0}] Not found", book_id)
        return jsonify({"error": "Libro no encontrado"}), 404

    # Eliminar capítulos asociados
    Chapter.query.filter_by(book_id=book_id).delete()
    
    db.session.delete(book)
    db.session.commit()
    log("[DELETE /deleteBook/{0}] Deleted", book_id)
    return book_schema.jsonify(book)

@ruta_book.route("/trashBook/<string:book_id>", methods=["PUT"])
def trash_book(book_id):
    log("[PUT /trashBook/{0}] Called", book_id)
    book = Book.query.get(book_id)
    if not book:
        return jsonify({"error": "Libro no encontrado"}), 404

    book.is_trashed = True
    book.updated_at = datetime.now().isoformat()
    db.session.commit()
    log("[PUT /trashBook/{0}] Book trashed", book_id)
    return book_schema.jsonify(book)

@ruta_book.route("/restoreBook/<string:book_id>", methods=["PUT"])
def restore_book(book_id):
    log("[PUT /restoreBook/{0}] Called", book_id)
    book = Book.query.get(book_id)
    if not book:
        return jsonify({"error": "Libro no encontrado"}), 404

    book.is_trashed = False
    book.updated_at = datetime.now().isoformat()
    db.session.commit()
    log("[PUT /restoreBook/{0}] Book restored", book_id)
    return book_schema.jsonify(book)

@ruta_book.route("/updateBookDetails/<string:book_id>", methods=["PUT"])
def update_book_details(book_id):
    data = request.json or {}
    log("[PUT /updateBookDetails/{0}] Payload: {1}", book_id, data)
    
    book = Book.query.get(book_id)
    if not book:
        return jsonify({"error": "Libro no encontrado"}), 404

    if "title" in data:
        book.title = data["title"]
    if "description" in data:
        book.description = data["description"]
    if "additional_genres" in data:
        book.additional_genres = json.dumps(data["additional_genres"])
    if "genre" in data:
        book.genre = data["genre"]
    if "content_type" in data:
        book.content_type = data["content_type"]
    
    book.updated_at = datetime.now().isoformat()
    db.session.commit()
    log("[PUT /updateBookDetails/{0}] Book updated", book_id)
    return book_schema.jsonify(book)

@ruta_book.route("/updateBookContent/<string:book_id>", methods=["PUT"])
def update_book_content(book_id):
    content = request.json.get("content", {})
    log("[PUT /updateBookContent/{0}] Content update request", book_id)
    
    book = Book.query.get(book_id)
    if not book:
        return jsonify({"error": "Libro no encontrado"}), 404

    book.content = json.dumps(content)
    book.updated_at = datetime.now().isoformat()
    db.session.commit()
    log("[PUT /updateBookContent/{0}] Content updated", book_id)
    return book_schema.jsonify(book)

@ruta_book.route("/updatePublicationDate/<string:book_id>", methods=["PUT"])
def update_publication_date(book_id):
    date_str = request.json.get("publication_date")
    log("[PUT /updatePublicationDate/{0}] Fecha: {1}", book_id, date_str)
    
    book = Book.query.get(book_id)
    if not book:
        return jsonify({"error": "Libro no encontrado"}), 404

    book.publication_date = datetime.fromisoformat(date_str) if date_str else None
    book.updated_at = datetime.now().isoformat()
    db.session.commit()
    log("[PUT /updatePublicationDate/{0}] Date updated", book_id)
    return book_schema.jsonify(book)

@ruta_book.route("/updateViews/<string:book_id>", methods=["PUT"])
def update_book_views(book_id):
    log("[PUT /updateViews/{0}] Called", book_id)
    book = Book.query.get(book_id)
    if not book:
        log("[PUT /updateViews/{0}] Not found", book_id)
        return jsonify({"error": "Libro no encontrado"}), 404

    book.views = (book.views or 0) + 1
    book.updated_at = datetime.now().isoformat()
    db.session.commit()
    log("[PUT /updateViews/{0}] Views incremented", book_id)
    return book_schema.jsonify(book)

@ruta_book.route("/searchBooks", methods=["GET"])
def search_books():
    query = request.args.get("query", "")
    log("[GET /searchBooks] Query: {0}", query)
    books = Book.query.filter(
        Book.title.ilike(f"%{query}%"),
        Book.is_trashed == False,
        Book.status != "alert"
    ).all()
    return books_schema.jsonify(books)

@ruta_book.route("/booksByAuthor/<author_id>", methods=["GET"])
def get_books_by_author(author_id):
    try:
        log("[GET /booksByAuthor/{0}]", author_id)
        books = Book.query.filter(Book.author_id == author_id, Book.is_trashed == False).all()
        return jsonify([book.to_dict() for book in books]), 200
    except Exception as e:
        log("[GET /booksByAuthor/{0}] Error: {1}", author_id, e)
        traceback.print_exc()
        return jsonify({"error": "Error interno del servidor"}), 500

@ruta_book.route("/topRatedBooks", methods=["GET"])
def get_top_rated_books():
    log("[GET /topRatedBooks] Called")
    books = Book.query.filter(
        Book.is_trashed == False, 
        Book.status != "alert"
    ).order_by(Book.rating.desc()).limit(10).all()
    return books_schema.jsonify(books)

@ruta_book.route("/mostViewedBooks", methods=["GET"])
def get_most_viewed_books():
    log("[GET /mostViewedBooks] Called")
    books = Book.query.filter(
        Book.is_trashed == False, 
        Book.status != "alert"
    ).order_by(Book.views.desc()).limit(10).all()
    return books_schema.jsonify(books)