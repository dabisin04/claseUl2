from fastapi import APIRouter, HTTPException, Query, Form, Header
from typing import List, Optional
from bson import ObjectId
from datetime import datetime
from models.user import User, UserCreate
from utils.security import generate_salt, hash_password
from config.db import users
from pydantic import EmailStr, BaseModel
import logging
from pymongo import MongoClient
import uuid

# Configuración del logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Esto enviará los logs a stdout, que Docker capturará
    ]
)

logger = logging.getLogger(__name__)

router = APIRouter()
client = MongoClient('mongodb://mongodb:27017/')
db = client['books_db']
users = db['users']

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

def _is_valid_uuid(val: str) -> bool:
    try:
        uuid.UUID(val)
        return True
    except ValueError:
        return False

def convert_flask_user(flask_user: dict) -> dict:
    """Convierte un usuario de Flask a formato MongoDB"""
    logger.info(f"Convirtiendo usuario de Flask: {flask_user.get('username', 'Sin nombre')}")
    
    id_value = flask_user.get("id")
    if not id_value or not isinstance(id_value, str) or not _is_valid_uuid(id_value):
        id_value = str(uuid.uuid4())
        logger.info(f"ID inválido o faltante, generando nuevo UUID: {id_value}")

    return {
        "_id": id_value,
        "username": flask_user["username"],
        "email": flask_user["email"],
        "password": flask_user["password"],
        "salt": flask_user.get("salt"),
        "bio": flask_user.get("bio", ""),
        "is_admin": flask_user.get("is_admin", False),
        "status": flask_user.get("status", "active"),
        "reported_for_name": flask_user.get("reported_for_name", False),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

def to_response(doc):
    if not doc:
        return None
    doc["id"] = str(doc["_id"])
    del doc["_id"]
    return doc

@router.post("/register", response_model=User)
async def register_user(data: UserCreate):
    # Verificar si el usuario ya existe
    existing = users.find_one({
        "$or": [{"email": data.email}, {"username": data.username}]
    })
    if existing:
        logger.warning(f"Intento de registro fallido: email o usuario ya existe - Email: {data.email}, Username: {data.username}")
        raise HTTPException(status_code=400, detail="El email o usuario ya existe")

    if data.from_flask:
        logger.info(f"Registrando usuario desde Flask - Email: {data.email}")
        user_dict = convert_flask_user(data.model_dump())
    else:
        logger.info(f"Iniciando registro nuevo - Email: {data.email}")
        salt = data.salt or generate_salt()
        hashed = hash_password(data.password, salt)
        user_dict = data.model_dump()
        user_dict["_id"] = str(data.id) if data.id else str(uuid.uuid4())
        user_dict.pop("id", None)
        user_dict.pop("from_flask", None)

        user_dict.update({
            "password": hashed,
            "salt": salt,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "status": "active",
            "reported_for_name": False
        })

    try:
        users.insert_one(user_dict)
        new_user = users.find_one({"_id": user_dict["_id"]})
        return User.model_validate(to_response(new_user))
    except Exception as e:
        logger.error(f"Error al registrar usuario - Email: {data.email}, Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al registrar usuario")

@router.post("/login", response_model=User)
async def login_user(data: LoginRequest):
    user = users.find_one({"email": data.email})
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    hashed = hash_password(data.password, user.get("salt", ""))
    if user["password"] != hashed:
        raise HTTPException(status_code=401, detail="Contraseña incorrecta")

    return User.model_validate(to_response(user))

@router.get("/getUser/{user_id}", response_model=User)
async def get_user(user_id: str):
    try:
        user_id = str(user_id)
        user = users.find_one({"_id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        return User.model_validate(to_response(user))
    except Exception as e:
        logger.error(f"Error al obtener usuario {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/getAllUsers", response_model=List[User])
async def get_all_users():
    return [User.model_validate(to_response(u)) for u in users.find()]

@router.put("/updateUser/{user_id}", response_model=User)
async def update_user(user_id: str, update_data: dict):
    try:
        user_id = str(user_id)
        user = users.find_one({"_id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        # Manejar cambios de nombre de usuario
        if "username" in update_data:
            if user.get("username") != update_data["username"]:
                update_data["status"] = "active"
                update_data["name_change_deadline"] = None

        update_data["updated_at"] = datetime.utcnow()
        users.update_one({"_id": user_id}, {"$set": update_data})
        updated = users.find_one({"_id": user_id})
        return User.model_validate(to_response(updated))
    except Exception as e:
        logger.error(f"Error al actualizar usuario {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/changePassword/{user_id}")
async def change_password(user_id: str, new_password: str):
    try:
        user_id = str(user_id)
        user = users.find_one({"_id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        salt = generate_salt()
        hashed = hash_password(new_password, salt)
        users.update_one(
            {"_id": user_id},
            {"$set": {"password": hashed, "salt": salt, "updated_at": datetime.utcnow()}}
        )
        return {"message": "Contraseña actualizada"}
    except Exception as e:
        logger.error(f"Error al cambiar contraseña de usuario {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/updateBio/{user_id}")
async def update_bio(user_id: str, bio: str):
    try:
        user_id = str(user_id)
        user = users.find_one({"_id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        users.update_one(
            {"_id": user_id},
            {"$set": {"bio": bio, "updated_at": datetime.utcnow()}}
        )
        return {"message": "Biografía actualizada"}
    except Exception as e:
        logger.error(f"Error al actualizar biografía de usuario {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/deleteUser/{user_id}")
async def delete_user(user_id: str):
    try:
        user_id = str(user_id)
        user = users.find_one({"_id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        users.delete_one({"_id": user_id})
        return {"message": "Usuario eliminado"}
    except Exception as e:
        logger.error(f"Error al eliminar usuario {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/isAdmin/{user_id}")
async def is_admin(user_id: str):
    try:
        user_id = str(user_id)
        user = users.find_one({"_id": user_id, "is_admin": True})
        return {"is_admin": bool(user)}
    except Exception as e:
        logger.error(f"Error al verificar admin de usuario {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/searchUsers", response_model=List[User])
async def search_users(query: str = Query(...)):
    return [User.model_validate(to_response(u)) for u in users.find({"username": {"$regex": query, "$options": "i"}})]

# Endpoints para seguimiento de autores
@router.post("/followAuthor")
async def follow_author(user_id: str, author_id: str):
    try:
        user_id = str(user_id)
        author_id = str(author_id)
        user = users.find_one({"_id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        users.update_one(
            {"_id": user_id},
            {"$addToSet": {"following": author_id}}
        )
        return {"message": "Autor seguido"}
    except Exception as e:
        logger.error(f"Error al seguir autor {author_id} por usuario {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/unfollowAuthor")
async def unfollow_author(user_id: str, author_id: str):
    try:
        user_id = str(user_id)
        author_id = str(author_id)
        user = users.find_one({"_id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        users.update_one(
            {"_id": user_id},
            {"$pull": {"following": author_id}}
        )
        return {"message": "Autor dejado de seguir"}
    except Exception as e:
        logger.error(f"Error al dejar de seguir autor {author_id} por usuario {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/getFollowedAuthors/{user_id}")
async def get_followed_authors(user_id: str):
    try:
        user_id = str(user_id)
        user = users.find_one({"_id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        return {"following": user.get("following", [])}
    except Exception as e:
        logger.error(f"Error al obtener autores seguidos por usuario {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
