from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.demo_service import list_subjects_for_section

router = APIRouter(prefix="/api/sections", tags=["sections"])


@router.get("/{section_id}/subjects")
def get_subjects(section_id: str, db: Session = Depends(get_db)):
    return list_subjects_for_section(db, section_id)
