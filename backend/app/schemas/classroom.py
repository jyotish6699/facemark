from pydantic import BaseModel
from typing import Optional

class SubjectCreate(BaseModel):
    name: str # e.g. "Operating Systems"
    code: Optional[str] = None # e.g. "CS501"

class SubjectResponse(BaseModel):
    id: str
    name: str
    code: str

    class Config:
        from_attributes = True

class ClassCreate(BaseModel):
    name: str # e.g. "CSE-A"
    subject: Optional[str] = None # e.g. "Operating Systems"
    semester: Optional[int] = 5
    academic_year: Optional[str] = "2026-2027"

class ClassResponse(BaseModel):
    id: str
    name: str
    semester: Optional[int] = None
    academic_year: Optional[str] = None
    subject: Optional[str] = "General"
    student_count: int = 0
    teacher_name: Optional[str] = None

    class Config:
        from_attributes = True

class ClassDetailResponse(ClassResponse):
    status: str
