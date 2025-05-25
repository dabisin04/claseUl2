from fastapi import APIRouter, HTTPException, Request, Query
from typing import List
from bson import ObjectId
from datetime import datetime
from config.db import chapters
from models.chapter import Chapter, ChapterCreate
import pymongo

router = APIRouter()

def validate_id(id: str):
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="ID inválido")
    return ObjectId(id)

def convert_doc(doc):
    doc["id"] = str(doc["_id"])
    del doc["_id"]
    return doc

@router.get("/chapters/{book_id}", response_model=List[Chapter])
async def get_chapters_by_book(book_id: str):
    docs = chapters.find({"book_id": book_id}).sort("chapter_number", pymongo.ASCENDING)
    return [Chapter.model_validate(convert_doc(c)) for c in docs]

@router.post("/addChapter", response_model=Chapter)
async def add_chapter(chapter: ChapterCreate):
    data = chapter.model_dump()
    now = datetime.utcnow()
    data.update({
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
    return Chapter.model_validate(convert_doc(data))

@router.put("/updateChapter")
async def update_chapter(chapter: ChapterCreate):
    if not chapter.id:
        raise HTTPException(status_code=400, detail="ID requerido")

    update_data = chapter.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()

    if "publication_date" in update_data and update_data["publication_date"]:
        update_data["publication_date"] = datetime.fromisoformat(update_data["publication_date"])

    result = chapters.update_one({"_id": validate_id(chapter.id)}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Capítulo no encontrado")

    updated = chapters.find_one({"_id": validate_id(chapter.id)})
    return Chapter.model_validate(convert_doc(updated))

@router.delete("/deleteChapter/{chapter_id}")
async def delete_chapter(chapter_id: str):
    result = chapters.delete_one({"_id": validate_id(chapter_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Capítulo no encontrado")
    return {"message": "Capítulo eliminado"}

@router.put("/updateChapterViews/{chapter_id}")
async def update_chapter_views(chapter_id: str):
    chapters.update_one({"_id": validate_id(chapter_id)}, {"$inc": {"views": 1}})
    return {"message": "Vistas del capítulo actualizadas"}

@router.put("/updateChapterContent/{chapter_id}")
async def update_chapter_content(chapter_id: str, request: Request):
    data = await request.json()
    content = data.get("content", {})
    chapters.update_one(
        {"_id": validate_id(chapter_id)},
        {"$set": {"content": content, "updated_at": datetime.utcnow()}}
    )
    return {"message": "Contenido actualizado"}

@router.put("/updateChapterPublicationDate/{chapter_id}")
async def update_chapter_publication_date(chapter_id: str, request: Request):
    data = await request.json()
    date_str = data.get("publication_date")
    pub_date = datetime.fromisoformat(date_str) if date_str else None

    chapters.update_one(
        {"_id": validate_id(chapter_id)},
        {"$set": {"publication_date": pub_date, "updated_at": datetime.utcnow()}}
    )
    return {"message": "Fecha de publicación actualizada"}

@router.put("/updateChapterDetails/{chapter_id}")
async def update_chapter_details(chapter_id: str, request: Request):
    data = await request.json()
    fields = {}
    if "title" in data:
        fields["title"] = data["title"]
    if "description" in data:
        fields["description"] = data["description"]

    if fields:
        fields["updated_at"] = datetime.utcnow()
        chapters.update_one({"_id": validate_id(chapter_id)}, {"$set": fields})
        return {"message": "Detalles actualizados"}
    return {"message": "Sin cambios"}

@router.get("/searchChapters", response_model=List[Chapter])
async def search_chapters(query: str = Query("")):
    results = chapters.find({
        "title": {"$regex": query, "$options": "i"},
        "reports": 0
    })
    return [Chapter.model_validate(convert_doc(c)) for c in results]
