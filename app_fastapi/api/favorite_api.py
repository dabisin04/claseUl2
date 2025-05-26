from fastapi import APIRouter, HTTPException, Query, Request
from typing import List
from models.favorite import Favorite, FavoriteCreate
from datetime import datetime
from bson import ObjectId
from config.db import favorites, books, users
import logging
import uuid

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

def _is_valid_uuid(val: str) -> bool:
    try:
        uuid.UUID(val)
        return True
    except ValueError:
        return False

def convert_flask_favorite(flask_favorite: dict) -> dict:
    """Convierte un favorito de Flask a formato MongoDB"""
    logger.info(f"Convirtiendo favorito de Flask para usuario {flask_favorite.get('user_id')}")
    
    id_value = flask_favorite.get("id")
    if not id_value or not isinstance(id_value, str) or not _is_valid_uuid(id_value):
        id_value = str(uuid.uuid4())
        logger.info(f"ID inválido o faltante, generando nuevo UUID: {id_value}")

    return {
        "_id": id_value,
        "user_id": flask_favorite["user_id"],
        "book_id": flask_favorite["book_id"],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

def to_response(doc):
    if not doc:
        return None
    doc["id"] = str(doc["_id"])
    del doc["_id"]
    return doc

# 🔹 Agregar libro a favoritos
@router.post("/addFavorite", response_model=Favorite)
async def add_favorite(favorite: FavoriteCreate):
    try:
        logger.info(f"[POST /addFavorite] Iniciando proceso para usuario {favorite.user_id}")
        
        # Asegurar que se use str
        user_id = str(favorite.user_id)
        book_id = str(favorite.book_id)

        # Verificar que el usuario existe
        user = users.find_one({"_id": user_id})
        if not user:
            logger.warning(f"[POST /addFavorite] Usuario no encontrado: {user_id}")
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        logger.info(f"[POST /addFavorite] Usuario encontrado")

        # Verificar que el libro existe
        book = books.find_one({"_id": book_id})
        if not book:
            logger.warning(f"[POST /addFavorite] Libro no encontrado: {book_id}")
            raise HTTPException(status_code=404, detail="Libro no encontrado")
        logger.info(f"[POST /addFavorite] Libro encontrado")

        # Verificar si ya existe el favorito
        existing = favorites.find_one({
            "user_id": user_id,
            "book_id": book_id
        })
        if existing:
            logger.info(f"[POST /addFavorite] Favorito ya existe")
            return Favorite.model_validate(existing)

        # Construir favorito
        favorite_data = favorite.model_dump()
        favorite_data["_id"] = favorite.id or str(uuid.uuid4())
        favorite_data["user_id"] = user_id
        favorite_data["book_id"] = book_id
        favorite_data["created_at"] = datetime.utcnow()
        favorite_data["updated_at"] = datetime.utcnow()

        result = favorites.insert_one(favorite_data)
        new_fav = favorites.find_one({"_id": result.inserted_id})

        logger.info(f"[POST /addFavorite] Favorito creado exitosamente: {result.inserted_id}")
        return Favorite.model_validate(new_fav)

    except HTTPException as he:
        logger.error(f"[POST /addFavorite] Error HTTP: {str(he)}")
        raise he
    except Exception as e:
        logger.error(f"[POST /addFavorite] Error inesperado: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error interno del servidor: {str(e)}"
        )

# 🔹 Eliminar libro de favoritos
@router.delete("/removeFavorite")
async def remove_favorite(user_id: str = Query(...), book_id: str = Query(...)):
    try:
        # Asegurar que se use str
        user_id = str(user_id)
        book_id = str(book_id)

        logger.info(f"[DELETE /removeFavorite] Intentando eliminar favorito para usuario {user_id} y libro {book_id}")

        # Verificar que el favorito existe
        fav = favorites.find_one({
            "user_id": user_id,
            "book_id": book_id
        })
        if not fav:
            logger.warning(f"[DELETE /removeFavorite] Favorito no encontrado")
            raise HTTPException(status_code=404, detail="Favorito no encontrado")

        result = favorites.delete_one({
            "user_id": user_id,
            "book_id": book_id
        })
        logger.info(f"[DELETE /removeFavorite] Favorito eliminado exitosamente")
        return {"message": "Eliminado de favoritos"}

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"[DELETE /removeFavorite] Error inesperado: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

# 🔹 Obtener IDs de libros favoritos por usuario
@router.get("/favoriteBookIds/{user_id}", response_model=List[str])
async def get_favorite_book_ids(user_id: str):
    try:
        logger.info(f"[GET /favoriteBookIds/{user_id}] Iniciando búsqueda de favoritos")

        # Log de tipo de dato recibido
        logger.info(f"[GET /favoriteBookIds/{user_id}] Tipo de user_id recibido: {type(user_id)}")

        # Asegurar str explícitamente
        user_id = str(user_id)

        # Log de ID antes de consulta
        logger.info(f"[GET /favoriteBookIds/{user_id}] Buscando usuario con _id = '{user_id}'")
        
        user = users.find_one({"_id": user_id})
        if not user:
            logger.warning(f"[GET /favoriteBookIds/{user_id}] Usuario no encontrado con _id = '{user_id}'")
            logger.info("[GET /favoriteBookIds/{user_id}] Dump de todos _id en la colección de usuarios:")
            for u in users.find({}, {"_id": 1}):
                logger.info(f" - Usuario en DB: _id = {u['_id']} (tipo: {type(u['_id'])})")
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        logger.info(f"[GET /favoriteBookIds/{user_id}] Usuario encontrado con _id = {user.get('_id')}")

        cursor = favorites.find({"user_id": user_id})
        book_ids = [str(fav["book_id"]) for fav in cursor]

        valid_book_ids = []
        for book_id in book_ids:
            book = books.find_one({"_id": str(book_id)})
            if book:
                valid_book_ids.append(book_id)
            else:
                logger.warning(f"[GET /favoriteBookIds/{user_id}] Libro no encontrado: {book_id}")
        
        logger.info(f"[GET /favoriteBookIds/{user_id}] Libros válidos retornados: {valid_book_ids}")
        return valid_book_ids

    except HTTPException as he:
        logger.error(f"[GET /favoriteBookIds/{user_id}] Error HTTP: {str(he)}")
        raise he
    except Exception as e:
        logger.error(f"[GET /favoriteBookIds/{user_id}] Error inesperado: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")


# 🔹 Verificar si un libro está en favoritos
@router.get("/isFavorite")
async def is_favorite(user_id: str = Query(...), book_id: str = Query(...)):
    try:
        user_id = str(user_id)
        book_id = str(book_id)

        logger.info(f"[GET /isFavorite] Verificando favorito para usuario {user_id} y libro {book_id}")

        user = users.find_one({"_id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        book = books.find_one({"_id": book_id})
        if not book:
            raise HTTPException(status_code=404, detail="Libro no encontrado")

        fav = favorites.find_one({
            "user_id": user_id,
            "book_id": book_id
        })

        return {"is_favorite": bool(fav)}

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"[GET /isFavorite] Error inesperado: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

