from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_teacher
from app.db.session import get_db
from app.schemas import LoginRequest, TeacherResponse, TokenResponse
from app.services.demo_service import authenticate_teacher, generate_token_for_teacher, seed_demo_data

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    seed_demo_data(db)
    teacher = authenticate_teacher(db, payload.email, payload.password)
    if not teacher:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    token = generate_token_for_teacher(teacher)
    return TokenResponse(
        access_token=token,
        teacher=TeacherResponse(
            teacher_id=teacher.teacher_id,
            name=teacher.name,
            email=teacher.email,
            role=teacher.role,
            assigned_section_id=teacher.assigned_section_id,
        ),
    )


@router.get("/me", response_model=TeacherResponse)
def me(current_teacher=Depends(get_current_teacher)):
    return TeacherResponse(
        teacher_id=current_teacher.teacher_id,
        name=current_teacher.name,
        email=current_teacher.email,
        role=current_teacher.role,
        assigned_section_id=current_teacher.assigned_section_id,
    )
