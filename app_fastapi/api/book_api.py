from fastapi import APIRouter, HTTPException, Query
from typing import List
from models.book import Book, BookCreate
from bson import ObjectId
from datetime import datetime
from config.db import books

router = APIRouter()

# Utilidad para validar IDs
def validate_object_id(book_id: str):
    if not ObjectId.is_valid(book_id):
        raise HTTPException(status_code=400, detail="Invalid book ID")
    return ObjectId(book_id)

# GET /books (con filtrado por papelera)
@router.get("/books", response_model=List[Book])
async def get_all_books(trashed: bool = Query(False)):
    query = {"is_trashed": trashed, "status": {"$ne": "alert"}}
    return [Book(**b) for b in books.find(query)]

# GET /alertedBooks
@router.get("/alertedBooks", response_model=List[Book])
async def get_alerted_books():
    return [Book(**b) for b in books.find({"status": "alert", "is_trashed": False})]

# GET /book/{book_id}
@router.get("/book/{book_id}", response_model=Book)
async def get_book_by_id(book_id: str):
    book = books.find_one({"_id": validate_object_id(book_id)})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return Book(**book)

# POST /addBook
@router.post("/addBook", response_model=Book)
async def add_book(book: BookCreate):
    if not book.author_id:
        raise HTTPException(status_code=400, detail="El libro debe tener un authorId válido.")
    if not book.id:
        raise HTTPException(status_code=400, detail="Falta el ID del libro.")
    if books.find_one({"_id": book.id}):
        raise HTTPException(status_code=409, detail="Ya existe un libro con ese ID")

    book_dict = book.model_dump()
    book_dict.update({
        "_id": book.id,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "upload_date": datetime.utcnow(),
        "views": 0,
        "rating": 0.0,
        "ratings_count": 0,
        "reports": 0,
    })
    books.insert_one(book_dict)
    return Book(**book_dict)

# DELETE /deleteBook/{book_id}
@router.delete("/deleteBook/{book_id}")
async def delete_book(book_id: str):
    result = books.delete_one({"_id": validate_object_id(book_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    return {"message": "Libro eliminado"}

# PUT /trashBook/{book_id}
@router.put("/trashBook/{book_id}", response_model=Book)
async def trash_book(book_id: str):
    result = books.update_one({"_id": validate_object_id(book_id)}, {"$set": {"is_trashed": True, "updated_at": datetime.utcnow()}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    return Book(**books.find_one({"_id": validate_object_id(book_id)}))

# PUT /restoreBook/{book_id}
@router.put("/restoreBook/{book_id}", response_model=Book)
async def restore_book(book_id: str):
    result = books.update_one({"_id": validate_object_id(book_id)}, {"$set": {"is_trashed": False, "updated_at": datetime.utcnow()}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    return Book(**books.find_one({"_id": validate_object_id(book_id)}))

# PUT /updateBookDetails/{book_id}
@router.put("/updateBookDetails/{book_id}", response_model=Book)
async def update_book_details(book_id: str, book: BookCreate):
    book_dict = book.model_dump()
    book_dict["updated_at"] = datetime.utcnow()
    result = books.update_one({"_id": validate_object_id(book_id)}, {"$set": book_dict})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    return Book(**books.find_one({"_id": validate_object_id(book_id)}))

# PUT /updateBookContent/{book_id}
@router.put("/updateBookContent/{book_id}", response_model=Book)
async def update_book_content(book_id: str, content: dict):
    result = books.update_one({"_id": validate_object_id(book_id)}, {"$set": {"content": content, "updated_at": datetime.utcnow()}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    return Book(**books.find_one({"_id": validate_object_id(book_id)}))

# PUT /updatePublicationDate/{book_id}
@router.put("/updatePublicationDate/{book_id}", response_model=Book)
async def update_publication_date(book_id: str, date: str):
    try:
        pub_date = datetime.fromisoformat(date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido")
    result = books.update_one({"_id": validate_object_id(book_id)}, {"$set": {"publication_date": pub_date, "updated_at": datetime.utcnow()}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    return Book(**books.find_one({"_id": validate_object_id(book_id)}))

# GET /searchBooks
@router.get("/searchBooks", response_model=List[Book])
async def search_books(query: str = Query(...)):
    return [Book(**b) for b in books.find({"title": {"$regex": query, "$options": "i"}, "is_trashed": False, "status": {"$ne": "alert"}})]

# GET /booksByAuthor/{author_id}
@router.get("/booksByAuthor/{author_id}", response_model=List[Book])
async def get_books_by_author(author_id: str):
    return [Book(**b) for b in books.find({"author_id": author_id, "is_trashed": False})]

# GET /topRatedBooks
@router.get("/topRatedBooks", response_model=List[Book])
async def get_top_rated_books():
    return [Book(**b) for b in books.find({"is_trashed": False, "status": {"$ne": "alert"}}).sort("rating", -1).limit(10)]

# GET /mostViewedBooks
@router.get("/mostViewedBooks", response_model=List[Book])
async def get_most_viewed_books():
    return [Book(**b) for b in books.find({"is_trashed": False, "status": {"$ne": "alert"}}).sort("views", -1).limit(10)]
