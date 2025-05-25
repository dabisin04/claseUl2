from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from bson import ObjectId
from .base import PyObjectId

class BookBase(BaseModel):
    title: str
    author_id: str
    description: Optional[str] = None
    genre: str
    additional_genres: List[str] = []
    publication_date: Optional[datetime] = None
    content: Optional[Dict[str, Any]] = None
    is_trashed: bool = False
    has_chapters: bool = False
    status: Literal['pending', 'published', 'rejected'] = 'pending'
    content_type: Literal['book', 'story', 'poem'] = 'book'

class BookCreate(BookBase):
    pass

class Book(BookBase):
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