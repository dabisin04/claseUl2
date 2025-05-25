from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
from .base import PyObjectId

class ChapterBase(BaseModel):
    book_id: str
    title: str
    content: Optional[Dict[str, Any]] = None
    chapter_number: int
    publication_date: Optional[datetime] = None

class ChapterCreate(ChapterBase):
    pass

class Chapter(ChapterBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    upload_date: datetime = Field(default_factory=datetime.utcnow)
    views: int = 0
    rating: float = 0.0
    ratings_count: int = 0
    reports: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat()
        }
