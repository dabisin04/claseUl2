from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class CommentBase(BaseModel):
    user_id: str
    book_id: str
    content: str
    parent_comment_id: Optional[str] = None
    root_comment_id: Optional[str] = None

class CommentCreate(CommentBase):
    from_flask: bool = False  # Campo para identificar si el comentario viene de Flask
    id: Optional[str] = None  # Campo opcional para ID si proviene de Flask

class Comment(CommentBase):
    id: str = Field(alias="_id")  # UUID como string, usando alias para MongoDB
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    reports: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True  # Permite usar 'id' en vez de '_id'
        populate_by_name = True                # Requiere que '_id' esté presente en dict, pero acepta 'id' también
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }
