from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from .base import PyObjectId
from bson import ObjectId

class CommentBase(BaseModel):
    user_id: str
    book_id: str
    content: str
    parent_comment_id: Optional[str] = None
    root_comment_id: Optional[str] = None

class CommentCreate(CommentBase):
    pass

class Comment(CommentBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
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
