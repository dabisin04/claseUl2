from fastapi import APIRouter, HTTPException, Query, Request
from typing import List
from models.favorite import Favorite, FavoriteCreate
from datetime import datetime

router = APIRouter()

# 🔹 Agregar libro a favoritos
@router.post("/addFavorite", response_model=Favorite)
async def add_favorite(favorite: FavoriteCreate, request: Request):
    db = request.app.mongodb
    existing = await db.favorites.find_one({
        "user_id": favorite.user_id,
        "book_id": favorite.book_id
    })
    if existing:
        existing["id"] = str(existing["_id"])
        return Favorite.model_validate(existing)

    favorite_data = favorite.model_dump()
    favorite_data["created_at"] = datetime.utcnow()
    favorite_data["updated_at"] = datetime.utcnow()
    result = await db.favorites.insert_one(favorite_data)

    new_fav = await db.favorites.find_one({"_id": result.inserted_id})
    new_fav["id"] = str(new_fav["_id"])
    return Favorite.model_validate(new_fav)

# 🔹 Eliminar libro de favoritos
@router.delete("/removeFavorite")
async def remove_favorite(user_id: str = Query(...), book_id: str = Query(...), request: Request = None):
    db = request.app.mongodb
    result = await db.favorites.delete_one({
        "user_id": user_id,
        "book_id": book_id
    })
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Favorito no encontrado")
    return {"message": "Eliminado de favoritos"}

# 🔹 Obtener IDs de libros favoritos por usuario
@router.get("/favoriteBookIds/{user_id}", response_model=List[str])
async def get_favorite_book_ids(user_id: str, request: Request):
    db = request.app.mongodb
    cursor = db.favorites.find({"user_id": user_id})
    book_ids = []
    async for fav in cursor:
        book_ids.append(fav["book_id"])
    return book_ids

# 🔹 Verificar si un libro está en favoritos
@router.get("/isFavorite")
async def is_favorite(user_id: str = Query(...), book_id: str = Query(...), request: Request = None):
    db = request.app.mongodb
    fav = await db.favorites.find_one({
        "user_id": user_id,
        "book_id": book_id
    })
    return {"is_favorite": bool(fav)}
