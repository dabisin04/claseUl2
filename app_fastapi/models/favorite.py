from pydantic import BaseModel, Field
from datetime import datetime
from .base import PyObjectId
from bson import ObjectId  # 🔥 IMPORTANTE: Faltaba esto

class FavoriteBase(BaseModel):
    user_id: str
    book_id: str

class FavoriteCreate(FavoriteBase):
    pass

class Favorite(FavoriteBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat()
        }
