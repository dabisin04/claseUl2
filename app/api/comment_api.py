from flask import Blueprint, request, jsonify
from config.db import db
from models.comment import Comment, CommentSchema
from sqlalchemy import text
from datetime import datetime
import uuid

ruta_comment = Blueprint("route_comment", __name__)
comment_schema = CommentSchema()
comments_schema = CommentSchema(many=True)

# 🔹 Agregar comentario (principal o respuesta)
@ruta_comment.route("/addComment", methods=["POST"])
def add_comment():
    try:
        data = request.json
        print("📥 Comentario recibido:", data)

        comment_id = data.get("id") or str(uuid.uuid4())
        user_id = data["user_id"]
        book_id = data["book_id"]
        content = data["content"]
        timestamp = data.get("timestamp", datetime.now().isoformat())
        parent_comment_id = data.get("parent_comment_id")

        # Determinar root_comment_id si es respuesta
        root_comment_id = None
        if parent_comment_id:
            result = db.session.execute(
                text("SELECT root_comment_id FROM comments WHERE id = :id"),
                {"id": parent_comment_id}
            ).fetchone()
            if result:
                root_comment_id = result[0] or parent_comment_id
            else:
                root_comment_id = parent_comment_id

        new_comment = Comment(
            id=comment_id,
            user_id=user_id,
            book_id=book_id,
            content=content,
            timestamp=timestamp,
            parent_comment_id=parent_comment_id,
            root_comment_id=root_comment_id,
            reports=0
        )
        db.session.add(new_comment)
        db.session.commit()
        return comment_schema.jsonify(new_comment), 200

    except KeyError as e:
        return jsonify({"error": f"Falta el campo obligatorio: {str(e)}"}), 400
    except Exception as e:
        print("❌ Error al agregar comentario:", str(e))
        return jsonify({"error": "Ocurrió un error al agregar el comentario"}), 500

# 🔹 Eliminar comentario (solo si es del usuario actual)
@ruta_comment.route("/deleteComment/<string:comment_id>", methods=["DELETE"])
def delete_comment(comment_id):
    current_user_id = request.headers.get("X-User-Id")
    print(f"🔐 Header X-User-Id recibido: {current_user_id}")
    if not current_user_id:
        return jsonify({"error": "Usuario no autenticado"}), 403

    comment = Comment.query.get(comment_id)
    if not comment:
        return jsonify({"error": "Comentario no encontrado"}), 404
    if comment.user_id != current_user_id:
        return jsonify({"error": "No tienes permiso para eliminar este comentario"}), 403

    db.session.delete(comment)
    db.session.commit()
    return jsonify({"message": "Comentario eliminado"}), 200

# 🔹 Comentarios de un libro
@ruta_comment.route("/commentsByBook/<string:book_id>", methods=["GET"])
def fetch_comments_by_book(book_id):
    comments = Comment.query.filter_by(book_id=book_id).all()
    return jsonify(comments_schema.dump(comments)), 200

# 🔹 Respuestas de un comentario
@ruta_comment.route("/replies/<string:comment_id>", methods=["GET"])
def fetch_replies(comment_id):
    replies = Comment.query.filter_by(parent_comment_id=comment_id).all()
    return jsonify(comments_schema.dump(replies)), 200

# 🔹 Editar comentario (autorizado)
@ruta_comment.route("/updateComment/<string:comment_id>", methods=["PUT"])
def update_comment(comment_id):
    current_user_id = request.headers.get("X-User-Id")
    print(f"🔐 Header X-User-Id recibido: {current_user_id}")
    if not current_user_id:
        return jsonify({"error": "Usuario no autenticado"}), 403

    comment = Comment.query.get(comment_id)
    if not comment:
        return jsonify({"error": "Comentario no encontrado"}), 404
    if comment.user_id != current_user_id:
        return jsonify({"error": "No tienes permiso para editar este comentario"}), 403

    new_content = request.json.get("content", "")
    comment.content = new_content
    db.session.commit()
    return jsonify({"message": "Comentario actualizado"}), 200
