from datetime import date
from typing import Any

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    email: str
    password: str


class TeacherResponse(BaseModel):
    teacher_id: str
    name: str
    email: str
    role: str
    assigned_section_id: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    teacher: TeacherResponse


class SubjectResponse(BaseModel):
    subject_id: str
    subject_name: str
    schedule_day: str | None = None
    room: str | None = None


class SectionResponse(BaseModel):
    section_id: str
    section_name: str
    department: str
    semester: str
    academic_year: str


class DashboardResponse(BaseModel):
    teacher: TeacherResponse
    section: SectionResponse
    subjects: list[SubjectResponse]
    stats: dict[str, int]
    recent_sessions: list[dict[str, Any]] = []


class AttendanceSessionCreate(BaseModel):
    teacher_id: str
    section_id: str
    subject_id: str
    session_date: date
    notes: str | None = None


class AttendanceSessionResponse(BaseModel):
    session_id: str
    teacher_id: str
    section_id: str
    subject_id: str
    session_date: str
    status: str
    notes: str | None = None


class RecognitionResultItem(BaseModel):
    student_id: str | None = None
    name: str | None = None
    roll_number: str | None = None
    confidence: float | None = None
    final_status: str | None = None
    recognition_status: str = "confident"


class RecognitionResponse(BaseModel):
    session_id: str
    results: dict[str, list[RecognitionResultItem]]


class FinalizeRequest(BaseModel):
    teacher_id: str
    decisions: dict[str, str] = Field(default_factory=dict)


class AttendanceRecordResponse(BaseModel):
    attendance_id: str
    session_id: str
    student_id: str
    recognition_status: str
    confidence_score: float | None = None
    final_status: str | None = None
    source_photo: str | None = None
    is_teacher_override: bool


class SessionDetailStudent(BaseModel):
    student_id: str
    full_name: str
    roll_number: str | None = None
    recognition_status: str
    confidence_score: float | None = None
    final_status: str | None = None


class AttendanceSessionDetailResponse(BaseModel):
    session_id: str
    teacher_id: str
    section_id: str
    subject_id: str
    session_date: str
    status: str
    notes: str | None = None
    students: list[SessionDetailStudent]


class HistoryItem(BaseModel):
    session_id: str
    subject_name: str
    section_name: str
    session_date: str
    total_students: int
    present_count: int
    status: str
