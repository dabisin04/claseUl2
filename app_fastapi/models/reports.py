from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
from .base import PyObjectId
from bson import ObjectId

class ReportBase(BaseModel):
    reporter_id: str
    target_id: str
    target_type: Literal['user', 'book', 'comment']
    reason: str
    status: Literal['pending', 'reviewed', 'dismissed'] = 'pending'
    admin_id: Optional[str] = None

class ReportCreate(ReportBase):
    pass

class Report(ReportBase):
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
