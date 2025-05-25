import traceback
from flask import Blueprint, request, jsonify
from config.db import db
from models.book import Book, BookSchema
import json
from datetime import datetime

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
        result = books_schema.dump(books)
        log("[GET /books] Returning {0} books", len(result))
        return jsonify(result)
    except Exception as e:
        log("[GET /books] Error: {0}", e)
        traceback.print_exc()
        return jsonify({"error": "Internal Server Error"}), 500
    
@ruta_book.route("/alertedBooks", methods=["GET"])
def get_alerted_books():
    books = Book.query.filter(Book.status == "alert", Book.is_trashed == False).all()
    return jsonify(books_schema.dump(books)), 200

@ruta_book.route("/book/<string:book_id>", methods=["GET"])
def get_book_by_id(book_id):
    log("[GET /book/{0}] Called", book_id)
    book = Book.query.get(book_id)
    if not book:
        log("[GET /book/{0}] Not found", book_id)
        return jsonify({"message": "No encontrado"}), 404
    data = book_schema.dump(book)
    log("[GET /book/{0}] Found book: {1}", book_id, data)
    return jsonify(data), 200

@ruta_book.route("/addBook", methods=["POST"])
def add_book():
    try:
        data = request.json or {}
        log("[POST /addBook] Payload: {0}", data)
        if not data.get("author_id"):
            log("[POST /addBook] Missing author_id")
            return jsonify({"error": "El libro debe tener un authorId válido."}), 400
        book_id = data.get("id")
        if not book_id:
            log("[POST /addBook] Missing book id in payload")
            return jsonify({"error": "Falta el ID del libro."}), 400
        existing = Book.query.get(book_id)
        if existing:
            log("[POST /addBook] Conflict: book {0} already exists", book_id)
            return jsonify({"error": "Ya existe un libro con ese ID"}), 409
        new_book = Book.from_dict(data)
        db.session.add(new_book)
        db.session.commit()
        log("[POST /addBook] Book saved: {0}", book_id)
        return jsonify({"message": "Libro guardado correctamente", "id": new_book.id}), 201
    except Exception as e:
        log("[POST /addBook] Error: {0}", e)
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
    db.session.delete(book)
    db.session.commit()
    log("[DELETE /deleteBook/{0}] Deleted", book_id)
    return jsonify({"message": "Libro eliminado"})

@ruta_book.route("/trashBook/<string:book_id>", methods=["PUT"])
def trash_book(book_id):
    log("[PUT /trashBook/{0}] Called", book_id)
    updated = db.session.query(Book).filter(Book.id == book_id).update({"is_trashed": True})
    db.session.commit()
    log("[PUT /trashBook/{0}] Rows updated: {1}", book_id, updated)
    return jsonify({"message": "Libro enviado a papelera"})

@ruta_book.route("/restoreBook/<string:book_id>", methods=["PUT"])
def restore_book(book_id):
    log("[PUT /restoreBook/{0}] Called", book_id)
    updated = db.session.query(Book).filter(Book.id == book_id).update({"is_trashed": False})
    db.session.commit()
    log("[PUT /restoreBook/{0}] Rows updated: {1}", book_id, updated)
    return jsonify({"message": "Libro restaurado"})

@ruta_book.route("/updateBookDetails/<string:book_id>", methods=["PUT"])
def update_book_details(book_id):
    data = request.json or {}
    log("[PUT /updateBookDetails/{0}] Payload: {1}", book_id, data)
    fields = {}
    if "title" in data:
        fields["title"] = data["title"]
    if "description" in data:
        fields["description"] = data["description"]
    if "additional_genres" in data:
        fields["additional_genres"] = json.dumps(data["additional_genres"])
    if "genre" in data:
        fields["genre"] = data["genre"]
    if "content_type" in data:
        fields["content_type"] = data["content_type"]
    if fields:
        updated = db.session.query(Book).filter(Book.id == book_id).update(fields)
        db.session.commit()
        log("[PUT /updateBookDetails/{0}] Fields updated: {1}, rows: {2}", book_id, fields, updated)
    else:
        log("[PUT /updateBookDetails/{0}] No fields to update", book_id)
    return jsonify({"message": "Detalles actualizados"})

@ruta_book.route("/updateBookContent/<string:book_id>", methods=["PUT"])
def update_book_content(book_id):
    content = request.json.get("content", {})
    log("[PUT /updateBookContent/{0}] Content update request", book_id)
    db.session.query(Book).filter(Book.id == book_id).update({"content": json.dumps(content)})
    db.session.commit()
    log("[PUT /updateBookContent/{0}] Content updated", book_id)
    return jsonify({"message": "Contenido actualizado"})

@ruta_book.route("/updatePublicationDate/<string:book_id>", methods=["PUT"])
def update_publication_date(book_id):
    date_str = request.json.get("publication_date")
    pub_date = datetime.fromisoformat(date_str) if date_str else None
    log("[PUT /updatePublicationDate/{0}] Fecha: {1}", book_id, pub_date)
    db.session.query(Book).filter(Book.id == book_id).update({"publication_date": pub_date})
    db.session.commit()
    log("[PUT /updatePublicationDate/{0}] Fecha actualizada", book_id)
    return jsonify({"message": "Fecha de publicación actualizada"})

@ruta_book.route("/searchBooks", methods=["GET"])
def search_books():
    query = request.args.get("query", "")
    log("[GET /searchBooks] Query: {0}", query)
    books = Book.query.filter(
        Book.title.ilike(f"%{query}%"),
        Book.is_trashed == False,
        Book.status != "alert"
    ).all()
    result = books_schema.dump(books)
    log("[GET /searchBooks] Found {0} books", len(result))
    return jsonify(result)

@ruta_book.route("/booksByAuthor/<string:author_id>", methods=["GET"])
def get_books_by_author(author_id):
    log("[GET /booksByAuthor/{0}] Called", author_id)
    books = Book.query.filter(Book.author_id == author_id, Book.is_trashed == False).all()
    result = books_schema.dump(books)
    log("[GET /booksByAuthor/{0}] Found {1} books", author_id, len(result))
    return jsonify(result)

@ruta_book.route("/topRatedBooks", methods=["GET"])
def get_top_rated_books():
    log("[GET /topRatedBooks] Called")
    books = Book.query.filter(Book.is_trashed == False, Book.status != "alert").order_by(Book.rating.desc()).limit(10).all()
    result = books_schema.dump(books)
    log("[GET /topRatedBooks] Found {0} books", len(result))
    return jsonify(result)

@ruta_book.route("/mostViewedBooks", methods=["GET"])
def get_most_viewed_books():
    log("[GET /mostViewedBooks] Called")
    books = Book.query.filter(Book.is_trashed == False, Book.status != "alert").order_by(Book.views.desc()).limit(10).all()
    result = books_schema.dump(books)
    log("[GET /mostViewedBooks] Found {0} books", len(result))
    return jsonify(result)
