from pydantic import BaseModel
from typing import Optional, List
from app.models.attendance import RecognitionStatus

class ConfidentMatchItem(BaseModel):
    student_id: str
    name: str
    student_number: str
    confidence: str # e.g. "98%"
    confidence_score: float
    source_photo_order: int = 1

class ReviewMatchItem(BaseModel):
    face_id: str
    candidate_student_id: Optional[str]
    candidate_name: Optional[str]
    confidence: str # e.g. "67%"
    confidence_score: float
    source_photo_order: int = 1

class UnknownMatchItem(BaseModel):
    face_id: str
    candidate: str = "Unknown"
    source_photo_order: int = 1

class NotDetectedItem(BaseModel):
    student_id: str
    name: str
    student_number: str
    status: str = "Not detected"

class CategorizedResultsResponse(BaseModel):
    session_id: str
    photo_count: int
    total_enrolled: int
    confident: List[ConfidentMatchItem] = []
    review: List[ReviewMatchItem] = []
    unknown: List[UnknownMatchItem] = []
    not_detected: List[NotDetectedItem] = []
