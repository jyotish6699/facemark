from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_teacher
from app.db.session import get_db
from app.schemas import DashboardResponse
from app.services.demo_service import get_dashboard_data

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/teacher/{teacher_id}", response_model=DashboardResponse)
def get_dashboard(
    teacher_id: str,
    db: Session = Depends(get_db),
    current_teacher=Depends(get_current_teacher),
):
    if current_teacher.teacher_id != teacher_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to access another teacher's dashboard",
        )
    try:
        data = get_dashboard_data(db, teacher_id)
        return DashboardResponse(**data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
