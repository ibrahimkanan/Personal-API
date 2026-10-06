from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel


class MetricCreate(BaseModel):
    name: str
    type: Literal["numeric", "boolean", "duration"]
    unit: Optional[str] = None
    group_name: Optional[str] = None


class MetricGroupCreate(BaseModel):
    group_name: str
    type: Literal["numeric", "boolean", "duration"]
    items: List[str]  # e.g. ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]


class MetricOut(BaseModel):
    id: int
    name: str
    type: str
    unit: Optional[str]
    group_name: Optional[str]

    class Config:
        from_attributes = True


class LogCreate(BaseModel):
    metric_id: int
    value: Optional[float] = None
    duration_seconds: Optional[int] = None
    logged_at: Optional[datetime] = None  # defaults to now if omitted


class LogOut(BaseModel):
    id: int
    metric_id: int
    value: Optional[float]
    duration_seconds: Optional[int]
    logged_at: datetime

    class Config:
        from_attributes = True