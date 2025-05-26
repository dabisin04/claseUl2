from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime

class BookBase(BaseModel):
    title: str
    author_id: str
    description: Optional[str] = None
    genre: str
    additional_genres: Optional[List[str]] = Field(default_factory=list)
    publication_date: Optional[datetime] = None
    content: Optional[Dict[str, Any]] = None
    is_trashed: bool = False
    has_chapters: bool = False
    status: Literal['pending', 'published', 'rejected', 'alert'] = 'pending'
    content_type: Literal['book', 'story', 'poem'] = 'book'

class BookCreate(BookBase):
    from_flask: bool = False
    id: Optional[str] = Field(default=None, alias="_id")  # Para aceptar _id también

    model_config = {
        "populate_by_name": True
    }

class Book(BookBase):
    id: str = Field(alias="_id")
    upload_date: datetime = Field(default_factory=datetime.utcnow)
    views: int = 0
    rating: float = 0.0
    ratings_count: int = 0
    reports: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "populate_by_name": True,
        "json_encoders": {
            datetime: lambda dt: dt.isoformat()
        }
    }

class BookUpdate(BaseModel):
    title: Optional[str] = None
    author_id: Optional[str] = None
    description: Optional[str] = None
    genre: Optional[str] = None
    additional_genres: Optional[List[str]] = Field(default_factory=list)
    publication_date: Optional[datetime] = None
    content: Optional[Dict[str, Any]] = None
    is_trashed: Optional[bool] = None
    has_chapters: Optional[bool] = None
    status: Optional[Literal['pending', 'published', 'rejected']] = None
    content_type: Optional[Literal['book', 'story', 'poem']] = None
    from_flask: bool = False

    model_config = {
        "populate_by_name": True,
        "json_encoders": {
            datetime: lambda dt: dt.isoformat()
        }
    }
