from pydantic import BaseModel, Field
from datetime import datetime
from .base import PyObjectId
from bson import ObjectId
from typing import Optional

class FavoriteBase(BaseModel):
    user_id: str
    book_id: str

class FavoriteCreate(FavoriteBase):
    from_flask: bool = False  # Campo para identificar si el favorito viene de Flask
    id: Optional[str] = None  # Campo para guardar la ID de Flask si existe

class Favorite(FavoriteBase):
    id: str = Field(alias="_id")  # UUID como string, usando alias para MongoDB
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }
