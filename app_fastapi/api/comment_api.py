from fastapi import APIRouter, HTTPException, Header, Request
from models.comment import Comment, CommentCreate
from models.user import User
from bson import ObjectId
from datetime import datetime
from typing import List
from config.db import comments, users

router = APIRouter()

def to_response(doc):
    if not doc:
        return None
    doc["id"] = str(doc["_id"])
    del doc["_id"]
    return doc

@router.post("/addComment", response_model=Comment)
async def add_comment(comment: CommentCreate):
    user_id = comment.user_id

    user = users.find_one({"_id": ObjectId(user_id)})
    if user and user.get("status") in ["rename_required", "suspended"]:
        raise HTTPException(status_code=403, detail="Tu cuenta tiene restricciones y no puedes comentar por ahora.")

    root_comment_id = None
    if comment.parent_comment_id:
        parent = comments.find_one({"_id": ObjectId(comment.parent_comment_id)})
        if parent:
            root_comment_id = parent.get("root_comment_id") or str(parent["_id"])
        else:
            root_comment_id = comment.parent_comment_id

    data = comment.model_dump()
    now = datetime.utcnow()
    data.update({
        "root_comment_id": root_comment_id,
        "timestamp": now,
        "created_at": now,
        "updated_at": now,
        "reports": 0
    })

    result = comments.insert_one(data)
    created = comments.find_one({"_id": result.inserted_id})
    return Comment.model_validate(to_response(created))


@router.get("/commentsByBook/{book_id}", response_model=List[Comment])
async def fetch_comments_by_book(book_id: str):
    docs = comments.find({"book_id": book_id})
    return [Comment.model_validate(to_response(c)) for c in docs]


@router.get("/replies/{comment_id}", response_model=List[Comment])
async def fetch_replies(comment_id: str):
    docs = comments.find({"parent_comment_id": comment_id})
    return [Comment.model_validate(to_response(c)) for c in docs]


@router.delete("/comments/{comment_id}")
async def delete_comment(comment_id: str, x_user_id: str = Header(...)):
    comment = comments.find_one({"_id": ObjectId(comment_id)})
    if not comment:
        raise HTTPException(status_code=404, detail="Comentario no encontrado")
    if comment["user_id"] != x_user_id:
        raise HTTPException(status_code=403, detail="No tienes permiso para eliminar este comentario")

    comments.delete_one({"_id": ObjectId(comment_id)})
    return {"message": "Comentario eliminado"}


@router.put("/comments/{comment_id}")
async def update_comment(comment_id: str, x_user_id: str = Header(...), content: str = None):
    if not content:
        raise HTTPException(status_code=400, detail="Falta el contenido nuevo")

    comment = comments.find_one({"_id": ObjectId(comment_id)})
    if not comment:
        raise HTTPException(status_code=404, detail="Comentario no encontrado")
    if comment["user_id"] != x_user_id:
        raise HTTPException(status_code=403, detail="No tienes permiso para editar este comentario")

    comments.update_one(
        {"_id": ObjectId(comment_id)},
        {"$set": {"content": content, "updated_at": datetime.utcnow()}}
    )
    return {"message": "Comentario actualizado"}
