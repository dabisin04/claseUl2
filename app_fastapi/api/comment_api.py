from fastapi import APIRouter, HTTPException, Header, Request
from models.comment import Comment, CommentCreate
from models.user import User
from bson import ObjectId
from datetime import datetime
from typing import List
from config.db import comments, users
from pydantic import BaseModel
import uuid
import logging

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

class UpdateCommentPayload(BaseModel):
    content: str

def _is_valid_uuid(val: str) -> bool:
    try:
        uuid.UUID(val)
        return True
    except ValueError:
        return False

def convert_flask_comment(flask_comment: dict) -> dict:
    """Convierte un comentario de Flask a formato MongoDB"""
    logger.info(f"Convirtiendo comentario de Flask: {flask_comment.get('content', '')[:50]}...")
    
    id_value = flask_comment.get("id")
    if not id_value or not isinstance(id_value, str) or not _is_valid_uuid(id_value):
        id_value = str(uuid.uuid4())
        logger.info(f"ID inválido o faltante, generando nuevo UUID: {id_value}")

    return {
        "_id": id_value,
        "user_id": flask_comment["user_id"],
        "book_id": flask_comment["book_id"],
        "content": flask_comment["content"],
        "timestamp": datetime.fromisoformat(flask_comment["timestamp"]) if flask_comment.get("timestamp") else datetime.utcnow(),
        "parent_comment_id": flask_comment.get("parent_comment_id"),
        "root_comment_id": flask_comment.get("root_comment_id"),
        "reports": flask_comment.get("reports", 0),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

def get_valid_user_or_fail(user_id: str) -> dict:
    """Valida que el usuario exista y sea completo (tenga username y email)."""
    user = users.find_one({"_id": user_id}) or users.find_one({"id": user_id})
    
    if not user:
        logger.error(f"❌ Usuario no encontrado: {user_id}")
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if not user.get("username") or not user.get("email"):
        logger.error(f"❌ Usuario incompleto: {user_id}")
        raise HTTPException(status_code=400, detail="Usuario incompleto o no válido")

    return user

def to_response(doc):
    if not doc:
        return None
    return {
        **doc,
        "id": str(doc["_id"])  # Añade 'id', pero no elimina '_id'
    }


@router.post("/addComment", response_model=Comment)
async def add_comment(comment: CommentCreate):
    try:
        logger.info(f"Intentando agregar comentario para usuario {comment.user_id}")
        user_id = str(comment.user_id)
        book_id = str(comment.book_id)

        # ✅ Verificar existencia y validez del usuario
        user = get_valid_user_or_fail(user_id)

        # Verificar restricciones
        if user.get("status") in ["rename_required", "suspended"]:
            logger.warning(f"Usuario {user_id} tiene restricciones: {user.get('status')}")
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "Tu cuenta tiene restricciones y no puedes comentar por ahora.",
                    "status": user.get("status")
                }
            )

        # Procesar comentario
        if getattr(comment, "from_flask", False):
            logger.info("Procesando comentario desde Flask")
            data = convert_flask_comment(comment.model_dump())
        else:
            logger.info("Procesando nuevo comentario")
            data = comment.model_dump()
            now = datetime.utcnow()
            data["_id"] = str(comment.id) if comment.id else str(uuid.uuid4())
            data.update({
                "user_id": user_id,
                "book_id": book_id,
                "timestamp": now,
                "created_at": now,
                "updated_at": now,
                "reports": 0
            })

        # Determinar root_comment_id si es respuesta
        if data.get("parent_comment_id"):
            logger.info(f"Buscando comentario padre: {data['parent_comment_id']}")
            parent = comments.find_one({"_id": str(data["parent_comment_id"])})
            if parent:
                data["root_comment_id"] = parent.get("root_comment_id") or str(parent["_id"])
                logger.info(f"Root comment ID establecido: {data['root_comment_id']}")
            else:
                data["root_comment_id"] = data["parent_comment_id"]
                logger.warning(f"Comentario padre no encontrado, usando ID como root: {data['root_comment_id']}")

        result = comments.insert_one(data)
        created = comments.find_one({"_id": result.inserted_id})
        logger.info(f"Comentario agregado exitosamente: {result.inserted_id}")
        return Comment.model_validate(to_response(created))

    except KeyError as e:
        logger.error(f"Error de validación: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Falta el campo obligatorio: {str(e)}")
    except Exception as e:
        logger.error(f"Error al agregar comentario: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ocurrió un error al agregar el comentario")


@router.get("/commentsByBook/{book_id}", response_model=List[Comment])
async def fetch_comments_by_book(book_id: str):
    logger.info(f"Obteniendo comentarios del libro: {book_id}")
    try:
        book_id = str(book_id)
        docs = comments.find({"book_id": book_id})
        comments_list = [Comment.model_validate(to_response(c)) for c in docs]
        logger.info(f"Se encontraron {len(comments_list)} comentarios")
        return comments_list
    except Exception as e:
        logger.error(f"Error al obtener comentarios del libro {book_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/replies/{comment_id}", response_model=List[Comment])
async def fetch_replies(comment_id: str):
    logger.info(f"Obteniendo respuestas del comentario: {comment_id}")
    try:
        comment_id = str(comment_id)
        docs = comments.find({"parent_comment_id": comment_id})
        replies = [Comment.model_validate(to_response(c)) for c in docs]
        logger.info(f"Se encontraron {len(replies)} respuestas")
        return replies
    except Exception as e:
        logger.error(f"Error al obtener respuestas del comentario {comment_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/deleteComment/{comment_id}")
async def delete_comment(comment_id: str, x_user_id: str = Header(...)):
    logger.info(f"Intentando eliminar comentario {comment_id} por usuario {x_user_id}")
    try:
        comment_id = str(comment_id)
        x_user_id = str(x_user_id)

        # ✅ Validar que el usuario existe y es válido
        get_valid_user_or_fail(x_user_id)

        comment = comments.find_one({"_id": comment_id})
        if not comment:
            logger.warning(f"Comentario no encontrado: {comment_id}")
            raise HTTPException(status_code=404, detail="Comentario no encontrado")

        if comment["user_id"] != x_user_id:
            logger.warning(f"Usuario {x_user_id} no tiene permiso para eliminar comentario {comment_id}")
            raise HTTPException(status_code=403, detail="No tienes permiso para eliminar este comentario")

        comments.delete_one({"_id": comment_id})
        logger.info(f"Comentario eliminado exitosamente: {comment_id}")
        return {"message": "Comentario eliminado"}
    except Exception as e:
        logger.error(f"Error al eliminar comentario {comment_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/updateComment/{comment_id}")
async def update_comment(
    comment_id: str,
    payload: UpdateCommentPayload,
    x_user_id: str = Header(...)
):
    logger.info(f"Intentando actualizar comentario {comment_id} por usuario {x_user_id}")
    
    try:
        comment_id = str(comment_id)
        x_user_id = str(x_user_id)

        if not payload.content.strip():
            logger.error("Falta el contenido nuevo")
            raise HTTPException(status_code=400, detail="Falta el contenido nuevo")

        get_valid_user_or_fail(x_user_id)

        comment = comments.find_one({"_id": comment_id})
        if not comment:
            raise HTTPException(status_code=404, detail="Comentario no encontrado")

        if comment["user_id"] != x_user_id:
            raise HTTPException(status_code=403, detail="No tienes permiso para editar este comentario")

        comments.update_one(
            {"_id": comment_id},
            {"$set": {"content": payload.content, "updated_at": datetime.utcnow()}}
        )

        logger.info(f"Comentario actualizado exitosamente: {comment_id}")
        return {"message": "Comentario actualizado"}

    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        logger.error(f"Error al actualizar comentario {comment_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno al actualizar el comentario")
