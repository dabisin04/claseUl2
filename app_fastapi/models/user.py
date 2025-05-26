from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    username: str
    email: EmailStr
    bio: Optional[str] = None
    is_admin: bool = False
    status: str = "active"
    name_change_deadline: Optional[str] = None
    reported_for_name: bool = False

class UserCreate(UserBase):
    # Este alias permite que si te llega "_id" en lugar de "id", también lo acepte
    id: Optional[str] = Field(default=None, alias="_id")
    password: str
    salt: Optional[str] = None
    from_flask: bool = False

    model_config = {
        "populate_by_name": True
    }

class User(UserBase):
    id: str = Field(..., alias="_id")
    password: str
    salt: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "populate_by_name": True,
        "json_encoders": {
            datetime: lambda dt: dt.isoformat()
        }
    }
