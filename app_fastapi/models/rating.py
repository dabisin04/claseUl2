from pydantic import BaseModel, Field, validator
from datetime import datetime
from .base import PyObjectId
from bson import ObjectId

class RatingBase(BaseModel):
    user_id: str
    book_id: str
    rating: float

    @validator('rating')
    def validate_rating(cls, v):
        if not 1 <= v <= 5:
            raise ValueError("El rating debe estar entre 1 y 5")
        return v

class RatingCreate(RatingBase):
    pass

class Rating(RatingBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat()
        }
