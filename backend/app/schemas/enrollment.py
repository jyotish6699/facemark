from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class FaceEnrollmentResponse(BaseModel):
    id: str
    student_id: str
    student_name: str
    quality_score: float
    status: str
    created_at: datetime
    embedding_dimension: int = 512

    class Config:
        from_attributes = True
