from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.classroom import SubjectCreate, SubjectResponse
from app.models.classroom import Subject
from app.models.user import User
from app.api.deps import get_current_teacher

router = APIRouter(prefix="/subjects", tags=["Subjects"])

@router.get("", response_model=List[SubjectResponse])
def list_subjects(
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """List all available subjects."""
    return db.query(Subject).order_by(Subject.name).all()

@router.post("", response_model=SubjectResponse, status_code=status.HTTP_201_CREATED)
def create_subject(
    data: SubjectCreate,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """
    Create a new subject with unique code.
    Rejects duplicate subject names and codes.
    """
    name = data.name.strip()
    code = (data.code or name[:3].upper()).strip().upper()

    # Duplicate name check
    existing_name = db.query(Subject).filter(Subject.name == name).first()
    if existing_name:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Subject '{name}' already exists."
        )

    # Duplicate code check
    existing_code = db.query(Subject).filter(Subject.code == code).first()
    if existing_code:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Subject code '{code}' is already in use by '{existing_code.name}'."
        )

    subject = Subject(name=name, code=code)
    db.add(subject)
    db.commit()
    db.refresh(subject)
    return subject

@router.delete("/{subject_id}", response_model=dict)
def delete_subject(
    subject_id: str,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Delete a subject."""
    sub = db.query(Subject).filter(Subject.id == subject_id).first()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found.")
    
    db.delete(sub)
    db.commit()
    return {"message": f"Subject '{sub.name}' deleted successfully."}
