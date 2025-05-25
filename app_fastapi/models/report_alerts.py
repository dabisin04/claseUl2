from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal
from .base import PyObjectId
from bson import ObjectId

class ReportAlertBase(BaseModel):
    book_id: str
    report_reason: str
    status: Literal['alert', 'removed', 'restored'] = 'alert'

class ReportAlertCreate(ReportAlertBase):
    pass

class ReportAlert(ReportAlertBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat()
        }
