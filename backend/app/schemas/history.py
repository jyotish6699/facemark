from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class AttendanceHistoryItem(BaseModel):
    session_id: str
    date: str # "YYYY-MM-DD"
    class_id: str
    class_name: str
    subject: str
    present: int
    absent: int
    status: str
    finalized_at: Optional[datetime] = None

class StudentAttendanceHistoryItem(BaseModel):
    date: str
    subject: str
    status: str
    source: str
    reviewed_at: Optional[datetime] = None

class StudentAttendanceSummary(BaseModel):
    student_id: str
    student_name: str
    total_sessions: int
    attended_sessions: int
    attendance_percentage: float
    history: List[StudentAttendanceHistoryItem] = []
