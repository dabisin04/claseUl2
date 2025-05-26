from pydantic import BaseModel, Field, Extra
from datetime import datetime
from typing import Literal, Optional

class ReportAlertBase(BaseModel):
    book_id: str
    report_reason: str
    status: Literal['alert', 'removed', 'restored'] = 'alert'

    class Config:
        extra = Extra.ignore

class ReportAlertCreate(ReportAlertBase):
    from_flask: bool = False
    id: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        extra = Extra.ignore

class ReportAlert(ReportAlertBase):
    id: str = Field(alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        extra = Extra.ignore
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }
