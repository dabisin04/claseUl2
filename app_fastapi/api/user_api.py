from fastapi import APIRouter, HTTPException, Query, Form
from typing import List
from bson import ObjectId
from datetime import datetime
from models.user import User, UserCreate
from utils.security import generate_salt, hash_password
from config.db import users
from pydantic import EmailStr, BaseModel

router = APIRouter()

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

@router.post("/register", response_model=User)
async def register_user(data: UserCreate):
    existing = users.find_one({
        "$or": [{"email": data.email}, {"username": data.username}]
    })
    if existing:
        raise HTTPException(status_code=400, detail="El email o usuario ya existe")

    salt = data.salt or generate_salt()
    hashed = hash_password(data.password, salt)
    user_dict = data.model_dump()
    user_dict["password"] = hashed
    user_dict["salt"] = salt
    user_dict["created_at"] = datetime.utcnow()
    user_dict["updated_at"] = datetime.utcnow()

    result = users.insert_one(user_dict)
    new_user = users.find_one({"_id": result.inserted_id})
    return User(**new_user)

@router.post("/login", response_model=User)
async def login_user(data: LoginRequest):
    user = users.find_one({"email": data.email})
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    hashed = hash_password(data.password, user.get("salt", ""))
    if user["password"] != hashed:
        raise HTTPException(status_code=401, detail="Contraseña incorrecta")

    return User.model_validate(user)

    return User.model_validate(user)

@router.get("/getUser/{user_id}", response_model=User)
async def get_user(user_id: str):
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="ID inválido")
    user = users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="No encontrado")
    return user

@router.get("/getAllUsers", response_model=List[User])
async def get_all_users():
    return [User(**u) for u in users.find()]


@router.put("/updateUser/{user_id}", response_model=User)
async def update_user(user_id: str, update_data: dict):
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="ID inválido")
    update_data["updated_at"] = datetime.utcnow()
    users.update_one({"_id": ObjectId(user_id)}, {"$set": update_data})
    updated = users.find_one({"_id": ObjectId(user_id)})
    return updated

@router.put("/changePassword/{user_id}")
async def change_password(user_id: str, new_password: str):
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="ID inválido")
    salt = generate_salt()
    hashed = hash_password(new_password, salt)
    users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"password": hashed, "salt": salt, "updated_at": datetime.utcnow()}}
    )
    return {"message": "Contraseña actualizada"}

@router.put("/updateBio/{user_id}")
async def update_bio(user_id: str, bio: str):
    users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"bio": bio, "updated_at": datetime.utcnow()}}
    )
    return {"message": "Biografía actualizada"}

@router.delete("/deleteUser/{user_id}")
async def delete_user(user_id: str):
    users.delete_one({"_id": ObjectId(user_id)})
    return {"message": "Usuario eliminado"}

@router.get("/isAdmin/{user_id}")
async def is_admin(user_id: str):
    user = users.find_one({"_id": ObjectId(user_id), "is_admin": True})
    return {"is_admin": bool(user)}

@router.get("/searchUsers", response_model=List[User])
async def search_users(query: str = Query(...)):
    return list(users.find({"username": {"$regex": query, "$options": "i"}}))
