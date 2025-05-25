from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from .base import PyObjectId
from bson import ObjectId

class UserStrikeBase(BaseModel):
    user_id: str
    reason: str
    strike_count: int = 1
    is_active: bool = True

class UserStrikeCreate(UserStrikeBase):
    pass

class UserStrike(UserStrikeBase):
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
