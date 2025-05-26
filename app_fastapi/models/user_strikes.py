from pydantic import BaseModel, Field, Extra
from datetime import datetime
from typing import Optional

class UserStrikeBase(BaseModel):
    user_id: str
    reason: str
    strike_count: int = 1
    is_active: bool = True

    class Config:
        extra = Extra.ignore

class UserStrikeCreate(UserStrikeBase):
    from_flask: bool = False
    id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        extra = Extra.ignore

class UserStrike(UserStrikeBase):
    id: str = Field(alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        extra = Extra.ignore
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }
