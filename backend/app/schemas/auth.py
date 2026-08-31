from pydantic import BaseModel, EmailStr
from typing import Optional
from app.models.user import UserRole, UserStatus

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: UserRole
    status: UserStatus
    teacher_id: Optional[str] = None
    employee_number: Optional[str] = None

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
