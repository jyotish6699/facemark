from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.schemas.history import AttendanceHistoryItem, StudentAttendanceSummary, StudentAttendanceHistoryItem
from app.models.session import AttendanceSession, SessionStatus
from app.models.classroom import Classroom
from app.models.student import Student
from app.models.attendance import AttendanceRecord, FinalAttendanceStatus
from app.models.user import User
from app.api.deps import get_current_teacher

router = APIRouter(prefix="/history", tags=["Attendance History"])

@router.get("/classes/{class_id}", response_model=List[AttendanceHistoryItem])
def get_class_attendance_history(
    class_id: str,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get chronological list of finalized attendance sessions for a class."""
    cls = db.query(Classroom).filter(Classroom.id == class_id).first()
    if not cls:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found.")

    sessions = (
        db.query(AttendanceSession)
        .filter(AttendanceSession.class_id == class_id)
        .order_by(desc(AttendanceSession.session_date), desc(AttendanceSession.created_at))
        .all()
    )

    history = []
    for s in sessions:
        present_count = sum(1 for r in s.attendance_records if r.final_status == FinalAttendanceStatus.PRESENT)
        absent_count = sum(1 for r in s.attendance_records if r.final_status == FinalAttendanceStatus.ABSENT)
        
        # If open/in-progress, compute from records or default
        if not s.attendance_records:
            present_count = 0
            absent_count = 0

        history.append(AttendanceHistoryItem(
            session_id=s.id,
            date=s.session_date,
            class_id=cls.id,
            class_name=cls.name,
            subject=s.subject.name if s.subject else "General",
            present=present_count,
            absent=absent_count,
            status=s.status.value,
            finalized_at=s.finalized_at
        ))

    return history

@router.get("/students/{student_id}", response_model=StudentAttendanceSummary)
def get_student_attendance_history(
    student_id: str,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get individual student attendance history and percentage."""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found.")

    records = (
        db.query(AttendanceRecord)
        .filter(AttendanceRecord.student_id == student_id)
        .join(AttendanceSession)
        .order_by(desc(AttendanceSession.session_date))
        .all()
    )

    total_sessions = len(records)
    attended_sessions = sum(1 for r in records if r.final_status == FinalAttendanceStatus.PRESENT)
    percentage = round((attended_sessions / total_sessions * 100.0), 1) if total_sessions > 0 else 0.0

    history_items = [
        StudentAttendanceHistoryItem(
            date=r.session.session_date if r.session else "N/A",
            subject=r.session.subject.name if r.session and r.session.subject else "Subject",
            status=r.final_status.value,
            source=r.source.value,
            reviewed_at=r.reviewed_at
        )
        for r in records
    ]

    return StudentAttendanceSummary(
        student_id=student.id,
        student_name=student.full_name,
        total_sessions=total_sessions,
        attended_sessions=attended_sessions,
        attendance_percentage=percentage,
        history=history_items
    )
