from fastapi import APIRouter, HTTPException, Request, Query
from typing import List
from bson import ObjectId
from datetime import datetime
from config.db import chapters, books
from models.chapter import Chapter, ChapterCreate
import pymongo
import json
import logging
import uuid

# Configuración del logging
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

def convert_flask_chapter(flask_chapter: dict) -> dict:
    """Convierte un capítulo de Flask a formato MongoDB"""
    logger.info(f"Convirtiendo capítulo de Flask: {flask_chapter.get('title', 'Sin título')}")
    
    id_value = flask_chapter.get("id")
    if not id_value or not isinstance(id_value, str) or not _is_valid_uuid(id_value):
        id_value = str(uuid.uuid4())
        logger.info(f"ID inválido o faltante, generando nuevo UUID: {id_value}")

    return {
        "_id": id_value,
        "book_id": flask_chapter["book_id"],
        "title": flask_chapter["title"],
        "content": json.loads(flask_chapter["content"]) if isinstance(flask_chapter.get("content"), str) else flask_chapter.get("content", {}),
        "chapter_number": flask_chapter["chapter_number"],
        "upload_date": datetime.fromisoformat(flask_chapter["upload_date"]) if flask_chapter.get("upload_date") else datetime.utcnow(),
        "publication_date": datetime.fromisoformat(flask_chapter["publication_date"]) if flask_chapter.get("publication_date") else None,
        "views": flask_chapter.get("views", 0),
        "rating": float(flask_chapter.get("rating", 0.0)),
        "ratings_count": flask_chapter.get("ratings_count", 0),
        "reports": flask_chapter.get("reports", 0),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

def to_response(doc):
    if not doc:
        return None
    doc["id"] = str(doc["_id"])
    del doc["_id"]
    return doc

@router.get("/chapters/{book_id}", response_model=List[Chapter])
async def get_chapters_by_book(book_id: str):
    logger.info(f"Obteniendo capítulos del libro: {book_id}")
    try:
        book_id = str(book_id)
        # Verificar que el libro existe
        book = books.find_one({"_id": book_id})
        if not book:
            logger.warning(f"Libro no encontrado: {book_id}")
            raise HTTPException(status_code=404, detail="Libro no encontrado")

        docs = chapters.find({"book_id": book_id}).sort("chapter_number", pymongo.ASCENDING)
        chapters_list = [Chapter.model_validate(to_response(c)) for c in docs]
        logger.info(f"Se encontraron {len(chapters_list)} capítulos")
        return chapters_list
    except Exception as e:
        logger.error(f"Error al obtener capítulos del libro {book_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/addChapter", response_model=Chapter)
async def add_chapter(chapter: ChapterCreate):
    logger.info(f"Intentando agregar capítulo: {chapter.title}")
    try:
        book_id = str(chapter.book_id)
        # Verificar que el libro existe
        book = books.find_one({"_id": book_id})
        if not book:
            logger.warning(f"Libro no encontrado: {book_id}")
            raise HTTPException(status_code=404, detail="Libro no encontrado")

        # Si el capítulo viene de Flask, usar sus datos directamente
        if hasattr(chapter, "from_flask") and chapter.from_flask:
            logger.info("Procesando capítulo desde Flask")
            data = convert_flask_chapter(chapter.model_dump())
        else:
            logger.info("Procesando nuevo capítulo")
            data = chapter.model_dump()
            if chapter.id:
                data["_id"] = str(chapter.id)
            else:
                data["_id"] = str(uuid.uuid4())
                
            now = datetime.utcnow()
            data.update({
                "book_id": book_id,
                "upload_date": now,
                "publication_date": datetime.fromisoformat(data["publication_date"]) if data.get("publication_date") else None,
                "views": data.get("views", 0),
                "rating": data.get("rating", 0.0),
                "ratings_count": data.get("ratings_count", 0),
                "reports": data.get("reports", 0),
                "created_at": now,
                "updated_at": now
            })

        chapters.insert_one(data)
        logger.info(f"Capítulo agregado exitosamente: {chapter.title}")
        return Chapter.model_validate(to_response(data))
    except Exception as e:
        logger.error(f"Error al agregar capítulo {chapter.title}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/updateChapter")
async def update_chapter(chapter: ChapterCreate):
    logger.info(f"Intentando actualizar capítulo: {chapter.title}")
    try:
        if not chapter.id:
            logger.error("Intento de actualizar capítulo sin ID")
            raise HTTPException(status_code=400, detail="ID requerido")

        chapter_id = str(chapter.id)
        # Verificar que el capítulo existe
        existing = chapters.find_one({"_id": chapter_id})
        if not existing:
            logger.warning(f"Capítulo no encontrado: {chapter_id}")
            raise HTTPException(status_code=404, detail="Capítulo no encontrado")

        update_data = chapter.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()

        if "publication_date" in update_data and update_data["publication_date"]:
            update_data["publication_date"] = datetime.fromisoformat(update_data["publication_date"])

        if "content" in update_data and isinstance(update_data["content"], dict):
            update_data["content"] = json.dumps(update_data["content"])

        result = chapters.update_one({"_id": chapter_id}, {"$set": update_data})
        if result.matched_count == 0:
            logger.warning(f"Capítulo no encontrado para actualizar: {chapter_id}")
            raise HTTPException(status_code=404, detail="Capítulo no encontrado")

        updated = chapters.find_one({"_id": chapter_id})
        logger.info(f"Capítulo actualizado exitosamente: {chapter.title}")
        return Chapter.model_validate(to_response(updated))
    except Exception as e:
        logger.error(f"Error al actualizar capítulo {chapter.title}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/deleteChapter/{chapter_id}")
async def delete_chapter(chapter_id: str):
    logger.info(f"Intentando eliminar capítulo: {chapter_id}")
    try:
        chapter_id = str(chapter_id)
        result = chapters.delete_one({"_id": chapter_id})
        if result.deleted_count == 0:
            logger.warning(f"Capítulo no encontrado para eliminar: {chapter_id}")
            raise HTTPException(status_code=404, detail="Capítulo no encontrado")
        logger.info(f"Capítulo eliminado exitosamente: {chapter_id}")
        return {"message": "Capítulo eliminado"}
    except Exception as e:
        logger.error(f"Error al eliminar capítulo {chapter_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/updateChapterViews/{chapter_id}")
async def update_chapter_views(chapter_id: str):
    logger.info(f"Actualizando vistas del capítulo: {chapter_id}")
    try:
        chapter_id = str(chapter_id)
        chapters.update_one({"_id": chapter_id}, {"$inc": {"views": 1}})
        logger.info(f"Vistas del capítulo actualizadas exitosamente: {chapter_id}")
        return {"message": "Vistas del capítulo actualizadas"}
    except Exception as e:
        logger.error(f"Error al actualizar vistas del capítulo {chapter_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/updateChapterContent/{chapter_id}")
async def update_chapter_content(chapter_id: str, request: Request):
    logger.info(f"Actualizando contenido del capítulo: {chapter_id}")
    try:
        chapter_id = str(chapter_id)
        data = await request.json()
        content = data.get("content", {})
        
        # Convertir el contenido a JSON string si es un diccionario
        if isinstance(content, dict):
            content = json.dumps(content)

        chapters.update_one(
            {"_id": chapter_id},
            {"$set": {"content": content, "updated_at": datetime.utcnow()}}
        )
        logger.info(f"Contenido del capítulo actualizado exitosamente: {chapter_id}")
        return {"message": "Contenido actualizado"}
    except Exception as e:
        logger.error(f"Error al actualizar contenido del capítulo {chapter_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/updateChapterPublicationDate/{chapter_id}")
async def update_chapter_publication_date(chapter_id: str, request: Request):
    logger.info(f"Actualizando fecha de publicación del capítulo: {chapter_id}")
    try:
        chapter_id = str(chapter_id)
        data = await request.json()
        date_str = data.get("publication_date")
        pub_date = datetime.fromisoformat(date_str) if date_str else None

        chapters.update_one(
            {"_id": chapter_id},
            {"$set": {"publication_date": pub_date, "updated_at": datetime.utcnow()}}
        )
        logger.info(f"Fecha de publicación del capítulo actualizada exitosamente: {chapter_id}")
        return {"message": "Fecha de publicación actualizada"}
    except Exception as e:
        logger.error(f"Error al actualizar fecha de publicación del capítulo {chapter_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/updateChapterDetails/{chapter_id}")
async def update_chapter_details(chapter_id: str, request: Request):
    logger.info(f"Actualizando detalles del capítulo: {chapter_id}")
    try:
        chapter_id = str(chapter_id)
        data = await request.json()
        fields = {}
        if "title" in data:
            fields["title"] = data["title"]
        if "description" in data:
            fields["description"] = data["description"]

        if fields:
            fields["updated_at"] = datetime.utcnow()
            chapters.update_one({"_id": chapter_id}, {"$set": fields})
            logger.info(f"Detalles del capítulo actualizados exitosamente: {chapter_id}")
            return {"message": "Detalles actualizados"}
        logger.info(f"Sin cambios en los detalles del capítulo: {chapter_id}")
        return {"message": "Sin cambios"}
    except Exception as e:
        logger.error(f"Error al actualizar detalles del capítulo {chapter_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/searchChapters", response_model=List[Chapter])
async def search_chapters(query: str = Query("")):
    logger.info(f"Buscando capítulos con query: {query}")
    try:
        results = chapters.find({
            "title": {"$regex": query, "$options": "i"},
            "reports": 0
        })
        chapters_list = [Chapter.model_validate(to_response(c)) for c in results]
        logger.info(f"Se encontraron {len(chapters_list)} capítulos")
        return chapters_list
    except Exception as e:
        logger.error(f"Error al buscar capítulos: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
