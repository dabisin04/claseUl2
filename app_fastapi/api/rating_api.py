from fastapi import APIRouter, HTTPException, Query, Request
from typing import List, Dict
from models.rating import RatingCreate
from bson import ObjectId
from datetime import datetime

router = APIRouter()

# 📌 Upsert de rating
@router.post("/rateBook")
async def rate_book(rating: RatingCreate, request: Request):
    db = request.app.mongodb
    rating_id = f"{rating.user_id}-{rating.book_id}"
    rating_data = rating.dict()
    rating_data["timestamp"] = datetime.utcnow()
    rating_data["updated_at"] = datetime.utcnow()

    existing = await db.ratings.find_one({
        "user_id": rating.user_id,
        "book_id": rating.book_id
    })

    if existing:
        await db.ratings.update_one(
            {"_id": existing["_id"]},
            {"$set": rating_data}
        )
    else:
        rating_data["created_at"] = datetime.utcnow()
        await db.ratings.insert_one(rating_data)

    await recalculate_book_rating(rating.book_id, request)
    return {"message": "Rating actualizado correctamente"}

# 📌 Obtener rating del usuario
@router.get("/getUserRating")
async def get_user_rating(user_id: str = Query(...), book_id: str = Query(...), request: Request = None):
    db = request.app.mongodb
    rating = await db.ratings.find_one({"user_id": user_id, "book_id": book_id})
    return {"rating": rating["rating"] if rating else None}

# 📌 Obtener promedio y cantidad
@router.get("/getGlobalAverage/{book_id}")
async def get_global_average(book_id: str, request: Request):
    db = request.app.mongodb
    cursor = db.ratings.find({"book_id": book_id})
    ratings = [r async for r in cursor]
    if not ratings:
        return {"average": 0.0, "count": 0}
    avg = sum(r["rating"] for r in ratings) / len(ratings)
    return {"average": round(avg, 2), "count": len(ratings)}

# 📌 Obtener distribución de ratings
@router.get("/getRatingDistribution/{book_id}")
async def get_distribution(book_id: str, request: Request):
    db = request.app.mongodb
    cursor = db.ratings.find({"book_id": book_id})
    distribution = {i: 0 for i in range(1, 6)}
    async for doc in cursor:
        bucket = round(doc["rating"])
        if 1 <= bucket <= 5:
            distribution[bucket] += 1
    return distribution

# 📌 Eliminar rating
@router.delete("/deleteRating")
async def delete_rating(user_id: str = Query(...), book_id: str = Query(...), request: Request = None):
    db = request.app.mongodb
    await db.ratings.delete_one({"user_id": user_id, "book_id": book_id})
    await recalculate_book_rating(book_id, request)
    return {"message": "Rating eliminado"}

# 📌 Obtener calificaciones de usuarios con nombre
@router.get("/getBookRatings/{book_id}")
async def get_book_ratings(book_id: str, page: int = 1, limit: int = 10, request: Request = None):
    db = request.app.mongodb
    skip = (page - 1) * limit
    cursor = db.ratings.find({"book_id": book_id}).sort("timestamp", -1).skip(skip).limit(limit)
    ratings = []
    async for r in cursor:
        user = await db.users.find_one({"_id": ObjectId(r["user_id"])} if ObjectId.is_valid(r["user_id"]) else {"id": r["user_id"]})
        ratings.append({
            "id": str(r["_id"]),
            "user_id": r["user_id"],
            "book_id": r["book_id"],
            "rating": r["rating"],
            "timestamp": r["timestamp"],
            "username": user["username"] if user else ""
        })
    return ratings

# 📌 Recalcular promedio en colección books
async def recalculate_book_rating(book_id: str, request: Request):
    db = request.app.mongodb
    cursor = db.ratings.find({"book_id": book_id})
    ratings = [r async for r in cursor]
    if not ratings:
        await db.books.update_one({"_id": ObjectId(book_id)}, {"$set": {"rating": 0.0, "ratings_count": 0}})
        return
    avg = sum(r["rating"] for r in ratings) / len(ratings)
    await db.books.update_one(
        {"_id": ObjectId(book_id)},
        {"$set": {"rating": round(avg, 2), "ratings_count": len(ratings)}}
    )
