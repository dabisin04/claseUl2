from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, Union

class RatingBase(BaseModel):
    user_id: Union[str, None]  # Puede ser UUID (Flask) o ObjectId en string
    book_id: Union[str, None]
    rating: float

    @validator('rating')
    def validate_rating(cls, v):
        if not 1 <= v <= 5:
            raise ValueError("El rating debe estar entre 1 y 5")
        return v

class RatingCreate(RatingBase):
    from_flask: bool = False
    id: Optional[str] = None  # Soporta ID externo desde Flask

class Rating(RatingBase):
    id: str = Field(alias="_id")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }
