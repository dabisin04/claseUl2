from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime
from bson import ObjectId
from .base import PyObjectId

class UserBase(BaseModel):
    username: str
    email: EmailStr
    bio: Optional[str] = None
    is_admin: bool = False
    status: str = "active"
    name_change_deadline: Optional[str] = None
    reported_for_name: bool = False  # Campo nuevo del modelo SQL

class UserCreate(UserBase):
    password: str
    salt: Optional[str] = None

class User(UserBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    password: str
    salt: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat()
        }
