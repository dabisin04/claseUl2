from fastapi import APIRouter, HTTPException, Query
from typing import List
from models.rating import RatingCreate
from bson import ObjectId
from datetime import datetime
from config.db import ratings, books, users
import logging
import uuid

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

router = APIRouter()

def _is_valid_uuid(val: str) -> bool:
    try:
        uuid.UUID(val)
        return True
    except ValueError:
        return False

def convert_flask_rating(flask_rating: dict) -> dict:
    logger.info(f"Convirtiendo rating de Flask: {flask_rating.get('rating', 0)} estrellas")
    id_value = flask_rating.get("id")
    if not id_value or not isinstance(id_value, str) or not _is_valid_uuid(id_value):
        id_value = str(uuid.uuid4())
        logger.info(f"ID inválido o faltante, generando nuevo UUID: {id_value}")
    return {
        "_id": id_value,
        "user_id": flask_rating["user_id"],
        "book_id": flask_rating["book_id"],
        "rating": float(flask_rating["rating"]),
        "timestamp": datetime.fromisoformat(flask_rating["timestamp"]) if flask_rating.get("timestamp") else datetime.utcnow(),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

@router.post("/rateBook")
async def rate_book(rating: RatingCreate):
    try:
        user_id = str(rating.user_id)
        book_id = str(rating.book_id)

        if getattr(rating, "from_flask", False):
            logger.info(f"Buscando usuario Flask por id: {user_id}")
            user = users.find_one({"id": user_id})
            book = books.find_one({"id": book_id})
        else:
            logger.info(f"Buscando usuario MongoDB por _id: {user_id}")
            user = users.find_one({"_id": user_id})
            book = books.find_one({"_id": book_id})

        if not user:
            logger.warning(f"Usuario no encontrado: {user_id}")
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        if not book:
            logger.warning(f"Libro no encontrado: {book_id}")
            raise HTTPException(status_code=404, detail="Libro no encontrado")

        if getattr(rating, "from_flask", False):
            rating_data = convert_flask_rating(rating.model_dump())
        else:
            rating_data = rating.model_dump()
            rating_data["_id"] = str(rating.id) if rating.id else str(uuid.uuid4())
            rating_data.update({
                "user_id": user_id,
                "book_id": book_id,
                "timestamp": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            })

        existing = ratings.find_one({"user_id": user_id, "book_id": book_id})
        if existing:
            ratings.update_one({"_id": existing["_id"]}, {"$set": rating_data})
        else:
            rating_data["created_at"] = datetime.utcnow()
            ratings.insert_one(rating_data)

        await recalculate_book_rating(book_id)
        return {"message": "Rating actualizado correctamente"}
    except Exception as e:
        logger.error(f"Error al calificar libro {book_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/getUserRating")
async def get_user_rating(user_id: str = Query(...), book_id: str = Query(...)):
    try:
        rating = ratings.find_one({"user_id": user_id, "book_id": book_id})
        return {"rating": rating["rating"] if rating else None}
    except Exception as e:
        logger.error(f"Error al obtener rating: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/getGlobalAverage/{book_id}")
async def get_global_average(book_id: str):
    try:
        ratings_list = list(ratings.find({"book_id": book_id}))
        if not ratings_list:
            return {"average": 0.0, "count": 0}
        avg = sum(r["rating"] for r in ratings_list) / len(ratings_list)
        return {"average": round(avg, 2), "count": len(ratings_list)}
    except Exception as e:
        logger.error(f"Error al calcular promedio: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/getRatingDistribution/{book_id}")
async def get_distribution(book_id: str):
    try:
        distribution = {i: 0 for i in range(1, 6)}
        for doc in ratings.find({"book_id": book_id}):
            bucket = round(doc["rating"])
            if 1 <= bucket <= 5:
                distribution[bucket] += 1
        return distribution
    except Exception as e:
        logger.error(f"Error al obtener distribución: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/deleteRating")
async def delete_rating(user_id: str = Query(...), book_id: str = Query(...)):
    try:
        result = ratings.delete_one({"user_id": user_id, "book_id": book_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Rating no encontrado")
        await recalculate_book_rating(book_id)
        return {"message": "Rating eliminado"}
    except Exception as e:
        logger.error(f"Error al eliminar rating: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/getBookRatings/{book_id}")
async def get_book_ratings(book_id: str, page: int = 1, limit: int = 10):
    try:
        skip = (page - 1) * limit
        cursor = ratings.find({"book_id": book_id}).sort("timestamp", -1).skip(skip).limit(limit)
        ratings_list = []
        for r in cursor:
            user = users.find_one({"id": r["user_id"]}) or users.find_one({"_id": r["user_id"]})
            ratings_list.append({
                "id": str(r["_id"]),
                "user_id": r["user_id"],
                "book_id": r["book_id"],
                "rating": r["rating"],
                "timestamp": r["timestamp"],
                "username": user["username"] if user else ""
            })
        return ratings_list
    except Exception as e:
        logger.error(f"Error al obtener ratings del libro: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def recalculate_book_rating(book_id: str):
    try:
        ratings_list = list(ratings.find({"book_id": book_id}))
        book = books.find_one({"id": book_id}) or books.find_one({"_id": book_id})
        if not ratings_list:
            if book:
                books.update_one({"_id": book["_id"]}, {"$set": {"rating": 0.0, "ratings_count": 0}})
            return
        avg = sum(r["rating"] for r in ratings_list) / len(ratings_list)
        if book:
            books.update_one({"_id": book["_id"]}, {"$set": {"rating": round(avg, 2), "ratings_count": len(ratings_list)}})
    except Exception as e:
        logger.error(f"Error al recalcular rating promedio: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
