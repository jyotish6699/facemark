from pydantic import BaseModel
from typing import List, Optional
from app.models.attendance import FinalAttendanceStatus

class StudentReviewItem(BaseModel):
    id: str # student id
    name: str
    student_number: str
    recognition: str # "Present", "Review", "Unknown", "Not detected"
    final_status: FinalAttendanceStatus # PRESENT, ABSENT, REVIEW
    confidence: str # e.g. "98%", "N/A"
    is_confirmed: bool = False

class ReviewTableResponse(BaseModel):
    session_id: str
    class_name: str
    subject_name: str
    session_date: str
    students: List[StudentReviewItem]

class UpdateStudentStatusRequest(BaseModel):
    student_id: str
    final_status: FinalAttendanceStatus

class BatchReviewUpdateRequest(BaseModel):
    updates: List[UpdateStudentStatusRequest]

class FinalizeSessionResponse(BaseModel):
    session_id: str
    status: str
    finalized_at: str
    total_students: int
    present_count: int
    absent_count: int
    message: str
