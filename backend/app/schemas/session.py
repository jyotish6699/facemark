from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.session import SessionStatus

class SessionCreateRequest(BaseModel):
    class_id: str
    subject_id: Optional[str] = None
    subject_name: Optional[str] = None
    session_date: Optional[str] = None # "YYYY-MM-DD"

class PhotoInfo(BaseModel):
    id: str
    photo_order: int
    storage_key: str
    original_filename: Optional[str]
    processing_status: str
    faces_detected: int = 0
    uploaded_at: datetime

    class Config:
        from_attributes = True

class AttendanceSessionResponse(BaseModel):
    id: str
    class_id: str
    class_name: str
    subject_id: str
    subject_name: str
    session_date: str
    status: SessionStatus
    student_count: int
    started_at: datetime
    finalized_at: Optional[datetime] = None
    photos: List[PhotoInfo] = []

    class Config:
        from_attributes = True
