from pydantic import BaseModel, EmailStr
from typing import Optional

class StudentCreate(BaseModel):
    student_number: str
    full_name: str
    email: Optional[EmailStr] = None
    class_id: Optional[str] = None

class StudentResponse(BaseModel):
    id: str
    student_number: str
    full_name: str
    email: Optional[str] = None
    status: str
    has_face_enrollment: bool = False

    class Config:
        from_attributes = True

class StudentRosterItem(BaseModel):
    id: str
    student_number: str
    name: str
    status: str
    has_enrollment: bool

    class Config:
        from_attributes = True
