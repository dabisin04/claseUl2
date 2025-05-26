from flask import Blueprint, request, jsonify
from config.db import db
from models.user import User, UserSchema
from sqlalchemy import or_
from datetime import datetime
import uuid
import hashlib
import os
import base64
from functools import wraps

# Seguridad con API Key
API_KEY = os.environ.get("API_KEY")

ruta_user = Blueprint("route_user", __name__)
user_schema = UserSchema()
users_schema = UserSchema(many=True)

# =================== 🔐 Auth Helpers ===================

def generate_salt():
    return base64.urlsafe_b64encode(os.urandom(16)).decode()

def hash_password(password, salt):
    return hashlib.sha1((password + salt).encode()).hexdigest()

def require_api_key():
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            key = request.headers.get("X-API-KEY")
            if key != API_KEY:
                return jsonify({"error": "No autorizado"}), 401
            return f(*args, **kwargs)
        return wrapper
    return decorator

# =================== 🧾 API Endpoints ===================

@ruta_user.route("/register", methods=["POST"])
@require_api_key()
def register_user():
    data = request.json
    email = data["email"]
    username = data["username"]
    password = data["password"]

    exists = User.query.filter(or_(User.email == email, User.username == username)).first()
    if exists:
        return jsonify({"error": "El email o usuario ya existe"}), 400

    salt = generate_salt()
    hashed_password = hash_password(password, salt)

    new_user = User(
        username=username,
        email=email,
        password=hashed_password,
        salt=salt,
        bio=data.get("bio"),
        is_admin=bool(data.get("is_admin", False)),
        reported_for_name=False
    )
    db.session.add(new_user)
    db.session.commit()

    # Asegurarnos de que el ID se devuelva en la respuesta
    return jsonify({
        "id": str(new_user.id),  # Convertir a string para asegurar serialización
        "username": new_user.username,
        "email": new_user.email,
        "bio": new_user.bio,
        "is_admin": new_user.is_admin,
        "password": hashed_password,  # Necesario para el cliente
        "salt": salt  # Necesario para el cliente
    }), 201

@ruta_user.route("/login", methods=["POST"])
@require_api_key()
def login_user():
    data = request.json
    email = data["email"]
    password = data["password"]

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404

    if hash_password(password, user.salt or "") == user.password:
        return user_schema.jsonify(user)
    return jsonify({"error": "Contraseña incorrecta"}), 401

@ruta_user.route("/updateUser/<string:user_id>", methods=["PUT"])
@require_api_key()
def update_user(user_id):
    from models.user_strikes import UserStrike

    data = request.json
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404

    new_username = data.get("username")
    if new_username and new_username != user.username:
        print(f"🟢 Nombre cambiado de {user.username} a {new_username}")
        user.username = new_username
        user.status = "active"
        user.name_change_deadline = None

    user.email = data.get("email", user.email)
    user.bio = data.get("bio", user.bio)
    user.is_admin = data.get("is_admin", user.is_admin)
    user.reported_for_name = data.get("reported_for_name", user.reported_for_name)  # ✅

    db.session.commit()

    if user.status == "active" and data.get("reported_for_name"):
        print(f"⚠️ Usuario {user_id} ha sido reportado nuevamente por nombre.")
        strike = UserStrike(user_id=user.id, reason="Nombre inapropiado")
        db.session.add(strike)
        db.session.commit()

    return user_schema.jsonify(user)

@ruta_user.route("/changePassword/<string:user_id>", methods=["PUT"])
@require_api_key()
def change_password(user_id):
    new_password = request.json.get("new_password")
    salt = generate_salt()
    hashed = hash_password(new_password, salt)
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404
    
    user.password = hashed
    user.salt = salt
    db.session.commit()
    return user_schema.jsonify(user)

@ruta_user.route("/getUser/<string:user_id>", methods=["GET"])
@require_api_key()
def get_user_by_id(user_id):
    user = User.query.get(user_id)
    return user_schema.jsonify(user) if user else jsonify({"error": "No encontrado"}), 404

@ruta_user.route("/getAllUsers", methods=["GET"])
@require_api_key()
def get_all_users():
    users = User.query.all()
    return jsonify(users_schema.dump(users))

@ruta_user.route("/updateBio/<string:user_id>", methods=["PUT"])
@require_api_key()
def update_bio(user_id):
    bio = request.json.get("bio", "")
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404
    
    user.bio = bio
    db.session.commit()
    return user_schema.jsonify(user)

@ruta_user.route("/deleteUser/<string:user_id>", methods=["DELETE"])
@require_api_key()
def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "No encontrado"}), 404
    db.session.delete(user)
    db.session.commit()
    return user_schema.jsonify(user)

@ruta_user.route("/isAdmin/<string:user_id>", methods=["GET"])
@require_api_key()
def is_admin(user_id):
    user = User.query.filter_by(id=user_id, is_admin=True).first()
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404
    return user_schema.jsonify(user)

@ruta_user.route("/searchUsers", methods=["GET"])
@require_api_key()
def search_users():
    query = request.args.get("query", "")
    users = User.query.filter(User.username.ilike(f"%{query}%")).all()
    return jsonify(users_schema.dump(users))

# =================== 📚 Seguimiento ===================

@ruta_user.route("/followAuthor", methods=["POST"])
@require_api_key()
def follow_author():
    data = request.json
    user_id = data["user_id"]
    author_id = data["author_id"]
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404
        
    db.session.execute(
        "INSERT INTO followers (user_id, author_id) VALUES (:user_id, :author_id)",
        {"user_id": user_id, "author_id": author_id}
    )
    db.session.commit()
    return user_schema.jsonify(user)

@ruta_user.route("/unfollowAuthor", methods=["DELETE"])
@require_api_key()
def unfollow_author():
    data = request.json
    user_id = data["user_id"]
    author_id = data["author_id"]
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404
        
    db.session.execute(
        "DELETE FROM followers WHERE user_id = :user_id AND author_id = :author_id",
        {"user_id": user_id, "author_id": author_id}
    )
    db.session.commit()
    return user_schema.jsonify(user)

@ruta_user.route("/getFollowedAuthors/<string:user_id>", methods=["GET"])
@require_api_key()
def get_followed_authors(user_id):
    result = db.session.execute(
        "SELECT author_id FROM followers WHERE user_id = :user_id",
        {"user_id": user_id}
    ).fetchall()
    authors = [row[0] for row in result]
    return jsonify(authors)
