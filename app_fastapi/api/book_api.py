from fastapi import APIRouter, HTTPException, Query, Request, FastAPI, Body
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from typing import List, Optional
from models.book import Book, BookCreate, BookUpdate
from bson import ObjectId
from datetime import datetime
from config.db import books, users
from pydantic import BaseModel
import logging
import uuid
import json

# Configuración del logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

class PublicationDatePayload(BaseModel):
    publication_date: Optional[datetime] = None

logger = logging.getLogger(__name__)

router = APIRouter()

app = FastAPI()

def get_valid_author_or_fail(author_id: str) -> dict:
    """Valida que el autor exista y tenga datos esenciales."""
    query = {"_id": str(author_id)}  # Aseguramos que sea string siempre
    author = users.find_one(query)

    if not author:
        logger.error(f"❌ Autor no encontrado: {author_id}")
        raise HTTPException(status_code=404, detail="Autor no encontrado")

    if not author.get("username") or not author.get("email"):
        logger.error(f"❌ Autor incompleto: {author_id}")
        raise HTTPException(status_code=400, detail="Autor incompleto o no válido")

    return author

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error("❌ Error 422: Validación fallida")
    logger.error(f"➡ Path: {request.url.path}")
    logger.error(f"➡ Método: {request.method}")
    
    # Log detallado de cada error de validación
    for err in exc.errors():
        logger.error(f"  🔸 Error en campo: {err['loc']}")
        logger.error(f"  🔸 Mensaje: {err['msg']}")
        logger.error(f"  🔸 Tipo: {err['type']}")
        if 'ctx' in err:
            logger.error(f"  🔸 Contexto: {err['ctx']}")
    
    # Intentar leer y loguear el body de la petición
    try:
        body = await request.body()
        logger.error(f"📦 Body recibido (raw): {body.decode('utf-8')}")
        try:
            body_json = json.loads(body)
            logger.error(f"📦 Body parseado: {json.dumps(body_json, indent=2)}")
        except json.JSONDecodeError:
            logger.error("⚠️ Body no es un JSON válido")
    except Exception as e:
        logger.error(f"⚠️ No se pudo leer el body: {e}")
    
    return await request_validation_exception_handler(request, exc)

def _is_valid_uuid(val: str) -> bool:
    try:
        uuid.UUID(val)
        return True
    except ValueError:
        return False

def convert_flask_book(flask_book: dict) -> dict:
    """Convierte un libro de Flask a formato MongoDB válido para el modelo Book"""
    from datetime import datetime
    import json

    logger.info(f"Convirtiendo libro de Flask: {flask_book.get('title', 'Sin título')}")

    id_value = flask_book.get("id")
    if not id_value or not isinstance(id_value, str) or not _is_valid_uuid(id_value):
        id_value = str(uuid.uuid4())
        logger.info(f"ID inválido o faltante, generando nuevo UUID: {id_value}")

    # Convertir fechas si vienen como strings
    def parse_date(val):
        if isinstance(val, str):
            try:
                return datetime.fromisoformat(val)
            except ValueError:
                return None
        return val

    pub_date = parse_date(flask_book.get("publication_date"))
    upload_date = parse_date(flask_book.get("upload_date")) or datetime.utcnow()

    # Convertir additional_genres si viene como string
    additional_genres = flask_book.get("additional_genres", [])
    if isinstance(additional_genres, str):
        try:
            additional_genres = json.loads(additional_genres)
        except json.JSONDecodeError:
            logger.warning("❌ additional_genres inválido. Se usará lista vacía.")
            additional_genres = []

    # Validar género (obligatorio)
    genre = flask_book.get("genre", "").strip()
    if not genre:
        logger.warning("❌ genre faltante. Se usará 'Sin género'")
        genre = "Sin género"

    # Validar status según modelo Pydantic
    status = flask_book.get("status", "pending")
    if status not in {"pending", "published", "rejected"}:
        logger.warning(f"❌ status inválido ('{status}'). Se usará 'pending'")
        status = "pending"

    return {
        "_id": id_value,
        "title": flask_book.get("title", "Sin título"),
        "description": flask_book.get("description", ""),
        "author_id": flask_book.get("author_id"),
        "content": flask_book.get("content", {}),
        "publication_date": pub_date,
        "upload_date": upload_date,
        "views": flask_book.get("views", 0),
        "rating": float(flask_book.get("rating", 0.0)),
        "ratings_count": flask_book.get("ratings_count", 0),
        "reports": flask_book.get("reports", 0),
        "is_trashed": flask_book.get("is_trashed", False),
        "status": status,
        "genre": genre,
        "additional_genres": additional_genres,
        "has_chapters": flask_book.get("has_chapters", False),
        "content_type": flask_book.get("content_type", "book"),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }



def to_response(doc):
    if not doc:
        return None
    doc["id"] = str(doc["_id"])
    del doc["_id"]
    return doc

@router.get("/books", response_model=List[Book])
async def get_all_books(trashed: bool = Query(False)):
    logger.info(f"Obteniendo todos los libros (trashed={trashed})")
    try:
        query = {"is_trashed": trashed, "status": {"$ne": "alert"}}
        books_list = [Book.model_validate(to_response(b)) for b in books.find(query)]
        logger.info(f"Se encontraron {len(books_list)} libros")
        return books_list
    except Exception as e:
        logger.error(f"Error al obtener libros: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/alertedBooks", response_model=List[Book])
async def get_alerted_books():
    logger.info("Obteniendo libros alertados")
    try:
        books_list = [Book.model_validate(to_response(b)) for b in books.find({"status": "alert", "is_trashed": False})]
        logger.info(f"Se encontraron {len(books_list)} libros alertados")
        return books_list
    except Exception as e:
        logger.error(f"Error al obtener libros alertados: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/book/{book_id}", response_model=Book)
async def get_book_by_id(book_id: str):
    logger.info(f"Obteniendo libro por ID: {book_id}")
    try:
        book_id = str(book_id)
        book = books.find_one({"_id": book_id})
        if not book:
            logger.warning(f"Libro no encontrado: {book_id}")
            raise HTTPException(status_code=404, detail="Libro no encontrado")
        logger.info(f"Libro encontrado: {book.get('title', 'Sin título')}")
        return Book.model_validate(to_response(book))
    except Exception as e:
        logger.error(f"Error al obtener libro {book_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/addBook", response_model=Book)
async def add_book(request: Request):
    try:
        logger.info("📥 Entrando al endpoint /addBook")

        raw_data = await request.json()
        logger.info("🔍 Datos crudos recibidos del request:")
        logger.info(json.dumps(raw_data, indent=2))

        import json as pyjson
        from datetime import datetime

        def parse_json_field(field_name, default):
            value = raw_data.get(field_name, default)
            if isinstance(value, str):
                try:
                    return pyjson.loads(value)
                except pyjson.JSONDecodeError:
                    logger.warning(f"❌ {field_name} inválido, se usará {default}")
                    return default
            return value

        def parse_date_field(field_name):
            value = raw_data.get(field_name)
            if isinstance(value, str):
                try:
                    return datetime.fromisoformat(value)
                except ValueError:
                    logger.warning(f"❌ {field_name} con formato inválido, se ignorará.")
                    return None
            return value

        raw_data["additional_genres"] = parse_json_field("additional_genres", [])
        raw_data["content"] = parse_json_field("content", {})
        raw_data["upload_date"] = parse_date_field("upload_date") or datetime.utcnow()
        raw_data["publication_date"] = parse_date_field("publication_date")

        try:
            book = BookCreate.model_validate(raw_data)
            logger.info("✅ Modelo validado correctamente")
        except Exception as e:
            logger.error(f"❌ Error en validación del modelo: {str(e)}")
            raise HTTPException(status_code=422, detail="Error al validar datos del libro")

        book_dict = book.model_dump()
        logger.info(f"📦 Datos del libro: {json.dumps(book_dict, indent=2, default=str)}")

        # Validar autor con lógica unificada
        author_id = str(book.author_id)
        get_valid_author_or_fail(author_id)

        if getattr(book, "from_flask", False):
            logger.info("⚙️ Procesando libro desde Flask")
            book_dict = convert_flask_book(book_dict)
        else:
            logger.info("⚙️ Procesando libro nuevo")
            book_dict["_id"] = book.id or str(uuid.uuid4())

        now = datetime.utcnow()
        book_dict.update({
            "author_id": author_id,
            "created_at": now,
            "updated_at": now,
            "upload_date": now,
            "views": 0,
            "rating": 0.0,
            "ratings_count": 0,
            "reports": 0,
            "is_trashed": False,
            "status": "pending"
        })

        books.insert_one(book_dict)
        logger.info(f"✅ Libro agregado exitosamente: {book_dict['title']}")

        response_obj = Book.model_validate(to_response(book_dict))
        return JSONResponse(content=jsonable_encoder(response_obj))

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"💥 Error al agregar libro: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno al guardar el libro")


@router.delete("/deleteBook/{book_id}")
async def delete_book(book_id: str):
    logger.info(f"Intentando eliminar libro: {book_id}")
    try:
        book_id = str(book_id)
        result = books.delete_one({"_id": book_id})
        if result.deleted_count == 0:
            logger.warning(f"Libro no encontrado para eliminar: {book_id}")
            raise HTTPException(status_code=404, detail="Libro no encontrado")
        logger.info(f"Libro eliminado exitosamente: {book_id}")
        return {"message": "Libro eliminado"}
    except Exception as e:
        logger.error(f"Error al eliminar libro {book_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/trashBook/{book_id}", response_model=Book)
async def trash_book(book_id: str):
    logger.info(f"Intentando mover a papelera libro: {book_id}")
    try:
        book_id = str(book_id)
        result = books.update_one(
            {"_id": book_id},
            {"$set": {"is_trashed": True, "updated_at": datetime.utcnow()}}
        )
        if result.matched_count == 0:
            logger.warning(f"Libro no encontrado para mover a papelera: {book_id}")
            raise HTTPException(status_code=404, detail="Libro no encontrado")
        logger.info(f"Libro movido a papelera exitosamente: {book_id}")
        return Book.model_validate(to_response(books.find_one({"_id": book_id})))
    except Exception as e:
        logger.error(f"Error al mover libro a papelera {book_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/restoreBook/{book_id}", response_model=Book)
async def restore_book(book_id: str):
    logger.info(f"Intentando restaurar libro: {book_id}")
    try:
        book_id = str(book_id)
        result = books.update_one(
            {"_id": book_id},
            {"$set": {"is_trashed": False, "updated_at": datetime.utcnow()}}
        )
        if result.matched_count == 0:
            logger.warning(f"Libro no encontrado para restaurar: {book_id}")
            raise HTTPException(status_code=404, detail="Libro no encontrado")
        logger.info(f"Libro restaurado exitosamente: {book_id}")
        return Book.model_validate(to_response(books.find_one({"_id": book_id})))
    except Exception as e:
        logger.error(f"Error al restaurar libro {book_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/updateBookDetails/{book_id}", response_model=Book)
async def update_book_details(book_id: str, book: BookUpdate):
    logger.info(f"📥 Intentando actualizar detalles del libro: {book_id}")
    try:
        book_id = str(book_id)

        # Obtener sólo campos enviados (evita overwrites no intencionales)
        book_dict = book.model_dump(exclude_unset=True)

        if not book_dict:
            logger.warning("⚠️ No se enviaron datos para actualizar")
            raise HTTPException(status_code=400, detail="No se enviaron datos para actualizar")

        # Validar author_id si está incluido
        if "author_id" in book_dict:
            get_valid_author_or_fail(str(book_dict["author_id"]))

        # Extra debugging para confirmar payload
        logger.info("📦 Payload recibido para actualización:")
        for key, value in book_dict.items():
            logger.info(f"  ├── {key}: {value} ({type(value).__name__})")

        # Procesar additional_genres si vino como string malformado
        if "additional_genres" in book_dict and isinstance(book_dict["additional_genres"], str):
            try:
                book_dict["additional_genres"] = json.loads(book_dict["additional_genres"])
                logger.info("✅ additional_genres fue decodificado correctamente")
            except json.JSONDecodeError:
                logger.warning("❌ additional_genres malformado. Se usará lista vacía")
                book_dict["additional_genres"] = []

        # Procesar content si vino como string malformado
        if "content" in book_dict and isinstance(book_dict["content"], str):
            try:
                book_dict["content"] = json.loads(book_dict["content"])
                logger.info("✅ content fue decodificado correctamente")
            except json.JSONDecodeError:
                logger.warning("❌ content malformado. Se usará dict vacío")
                book_dict["content"] = {}

        # Actualizar el timestamp de modificación
        book_dict["updated_at"] = datetime.utcnow()

        # Intentar actualizar el documento
        result = books.update_one({"_id": book_id}, {"$set": book_dict})
        if result.matched_count == 0:
            logger.warning(f"⚠️ Libro no encontrado para actualizar: {book_id}")
            raise HTTPException(status_code=404, detail="Libro no encontrado")

        logger.info(f"✅ Detalles del libro actualizados exitosamente: {book_id}")
        updated_book = to_response(books.find_one({"_id": book_id}))

        # 🔍 Validación manual para campos obligatorios
        mandatory_defaults = {
            "author_id": "Desconocido",
            "status": "pending",
            "is_trashed": False,
            "has_chapters": False,
        }
        for key, default in mandatory_defaults.items():
            if updated_book.get(key) is None:
                logger.warning(f"⚠️ Campo {key} está en None, asignando valor por defecto: {default}")
                updated_book[key] = default

        # Validar y retornar
        return Book.model_validate(updated_book)


    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"💥 Error al actualizar detalles del libro {book_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno al actualizar el libro")


@router.put("/updateBookContent/{book_id}", response_model=Book)
async def update_book_content(book_id: str, update: BookUpdate = Body(...)):
    logger.info(f"📥 Intentando actualizar contenido del libro: {book_id}")
    try:
        book_id = str(book_id)

        # Obtener solo los campos que se enviaron explícitamente
        update_dict = update.model_dump(exclude_unset=True)

        if "content" not in update_dict:
            logger.warning("⚠️ No se proporcionó campo 'content' en la petición")
            raise HTTPException(status_code=400, detail="Falta el campo 'content'")

        # Validar el contenido si es string (por seguridad)
        if isinstance(update_dict["content"], str):
            import json
            try:
                update_dict["content"] = json.loads(update_dict["content"])
            except json.JSONDecodeError:
                logger.warning("❌ Content recibido como string malformado, usando objeto vacío")
                update_dict["content"] = {}

        # Actualizar updated_at
        update_dict["updated_at"] = datetime.utcnow()

        result = books.update_one({"_id": book_id}, {"$set": update_dict})
        if result.matched_count == 0:
            logger.warning(f"📛 Libro no encontrado para actualizar contenido: {book_id}")
            raise HTTPException(status_code=404, detail="Libro no encontrado")

        updated_book = books.find_one({"_id": book_id})

        # 🔍 Normalizar campos requeridos si vinieron como None
        for field, default in {
            "author_id": "Desconocido",
            "is_trashed": False,
            "has_chapters": False,
            "status": "pending",
            "additional_genres": [],
        }.items():
            if updated_book.get(field) is None:
                logger.warning(f"⚠️ Campo {field} está en None, asignando valor por defecto: {default}")
                updated_book[field] = default

        logger.info(f"✅ Contenido del libro actualizado exitosamente: {book_id}")
        return Book.model_validate(to_response(updated_book))

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"💥 Error al actualizar contenido del libro {book_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno al actualizar el contenido del libro")

@router.put("/updatePublicationDate/{book_id}", response_model=Book)
async def update_publication_date(book_id: str, payload: PublicationDatePayload = Body(...)):
    logger.info(f"📅 Intentando actualizar fecha de publicación del libro: {book_id}")
    try:
        pub_date = payload.publication_date

        result = books.update_one(
            {"_id": book_id},
            {"$set": {
                "publication_date": pub_date,
                "updated_at": datetime.utcnow()
            }}
        )

        if result.matched_count == 0:
            logger.warning(f"⚠️ Libro no encontrado para actualizar fecha: {book_id}")
            raise HTTPException(status_code=404, detail="Libro no encontrado")

        logger.info(f"✅ Fecha de publicación actualizada exitosamente: {book_id}")
        updated_book = books.find_one({"_id": book_id})
        return Book.model_validate(to_response(updated_book))

    except Exception as e:
        logger.error(f"💥 Error al actualizar fecha de publicación del libro {book_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno al actualizar fecha de publicación")
    
@router.put("/updateViews/{book_id}", response_model=Book)
async def update_book_views(book_id: str):
    logger.info(f"👁️ Intentando actualizar vistas del libro: {book_id}")
    try:
        book_id = str(book_id)

        # Incrementar el contador de vistas
        result = books.update_one(
            {"_id": book_id},
            {"$inc": {"views": 1}, "$set": {"updated_at": datetime.utcnow()}}
        )

        if result.matched_count == 0:
            logger.warning(f"⚠️ Libro no encontrado para actualizar vistas: {book_id}")
            raise HTTPException(status_code=404, detail="Libro no encontrado")

        updated_book = books.find_one({"_id": book_id})

        # Normalizar campos obligatorios para evitar errores en la validación
        defaults = {
            "author_id": "Desconocido",
            "status": "pending",
            "is_trashed": False,
            "has_chapters": False,
            "additional_genres": []
        }
        for key, default in defaults.items():
            if updated_book.get(key) is None:
                logger.warning(f"⚠️ Campo {key} está en None, asignando valor por defecto: {default}")
                updated_book[key] = default

        logger.info(f"✅ Vistas del libro actualizadas exitosamente: {book_id}")
        return Book.model_validate(to_response(updated_book))

    except Exception as e:
        logger.error(f"💥 Error al actualizar vistas del libro {book_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno al actualizar vistas")

@router.get("/searchBooks", response_model=List[Book])
async def search_books(query: str = Query(...)):
    logger.info(f"Buscando libros con query: {query}")
    try:
        books_list = [Book.model_validate(to_response(b)) for b in books.find({
            "title": {"$regex": query, "$options": "i"},
            "is_trashed": False,
            "status": {"$ne": "alert"}
        })]
        logger.info(f"Se encontraron {len(books_list)} libros")
        return books_list
    except Exception as e:
        logger.error(f"Error al buscar libros: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/booksByAuthor/{author_id}", response_model=List[Book])
async def get_books_by_author(author_id: str):
    logger.info(f"Buscando libros del autor: {author_id}")
    try:
        author_id = str(author_id)
        books_list = [Book.model_validate(to_response(b)) for b in books.find({
            "author_id": author_id,
            "is_trashed": False
        })]
        logger.info(f"Se encontraron {len(books_list)} libros del autor")
        return books_list
    except Exception as e:
        logger.error(f"Error al buscar libros del autor {author_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/topRatedBooks", response_model=List[Book])
async def get_top_rated_books():
    logger.info("Obteniendo libros mejor calificados")
    try:
        books_list = [Book.model_validate(to_response(b)) for b in books.find({
            "is_trashed": False,
            "status": {"$ne": "alert"}
        }).sort("rating", -1).limit(10)]
        logger.info(f"Se encontraron {len(books_list)} libros mejor calificados")
        return books_list
    except Exception as e:
        logger.error(f"Error al obtener libros mejor calificados: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/mostViewedBooks", response_model=List[Book])
async def get_most_viewed_books():
    logger.info("Obteniendo libros más vistos")
    try:
        books_list = [Book.model_validate(to_response(b)) for b in books.find({
            "is_trashed": False,
            "status": {"$ne": "alert"}
        }).sort("views", -1).limit(10)]
        logger.info(f"Se encontraron {len(books_list)} libros más vistos")
        return books_list
    except Exception as e:
        logger.error(f"Error al obtener libros más vistos: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
