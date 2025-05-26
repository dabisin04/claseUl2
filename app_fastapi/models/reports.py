from pydantic import BaseModel, Field, Extra
from datetime import datetime
from typing import Optional, Literal

class ReportBase(BaseModel):
    reporter_id: str
    target_id: str
    target_type: Literal['user', 'book', 'comment']
    reason: str
    status: Literal['pending', 'reviewed', 'dismissed'] = 'pending'
    admin_id: Optional[str] = None

    class Config:
        extra = Extra.ignore

class ReportCreate(ReportBase):
    from_flask: bool = False
    id: Optional[str] = None
    timestamp: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        extra = Extra.ignore

class Report(ReportBase):
    id: str = Field(alias="_id")
    timestamp: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        extra = Extra.ignore
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }
