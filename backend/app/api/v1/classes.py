from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.classroom import ClassCreate, ClassResponse, ClassDetailResponse, SubjectCreate, SubjectResponse
from app.schemas.student import StudentRosterItem
from app.models.classroom import Classroom, Subject
from app.models.teacher import TeacherClass
from app.models.student import ClassMembership, Student
from app.models.enrollment import FaceEnrollment
from app.models.user import User, UserRole
from app.api.deps import get_current_teacher

router = APIRouter(prefix="/classes", tags=["Classes"])

# ───────────── List classes ─────────────

@router.get("", response_model=List[ClassResponse])
def list_classes(
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    # Let all teachers and admins view all active classes
    classes = db.query(Classroom).filter(Classroom.status == "ACTIVE").all()

    results = []
    for cls in classes:
        student_count = (
            db.query(ClassMembership)
            .filter(ClassMembership.class_id == cls.id, ClassMembership.status == "ACTIVE")
            .count()
        )

        teacher_name = current_user.full_name
        first_assignment = cls.teacher_assignments[0] if cls.teacher_assignments else None
        if first_assignment and first_assignment.teacher and first_assignment.teacher.user:
            teacher_name = first_assignment.teacher.user.full_name

        # Look up the subject from the subject column, or fallback to "General"
        subject_name = cls.subject or "General"

        results.append(ClassResponse(
            id=cls.id,
            name=cls.name,
            semester=cls.semester,
            academic_year=cls.academic_year,
            subject=subject_name,
            student_count=student_count,
            teacher_name=teacher_name
        ))

    return results

# ───────────── Create class ─────────────

@router.post("", response_model=ClassResponse, status_code=status.HTTP_201_CREATED)
def create_class(
    data: ClassCreate,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """
    Create a new class and auto-assign the current teacher.
    Rejects duplicates by class name.
    """
    existing = db.query(Classroom).filter(Classroom.name == data.name.strip()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Class '{data.name}' already exists."
        )

    cls = Classroom(
        name=data.name.strip(),
        semester=data.semester,
        academic_year=data.academic_year,
        subject=data.subject or "General"
    )
    db.add(cls)
    db.flush()

    # Auto-assign current teacher
    teacher = current_user.teacher_profile
    if teacher:
        db.add(TeacherClass(teacher_id=teacher.id, class_id=cls.id))

    db.commit()
    db.refresh(cls)

    return ClassResponse(
        id=cls.id,
        name=cls.name,
        semester=cls.semester,
        academic_year=cls.academic_year,
        subject=cls.subject,
        student_count=0,
        teacher_name=current_user.full_name
    )

# ───────────── Get class details ─────────────

@router.get("/{class_id}", response_model=ClassDetailResponse)
def get_class_details(
    class_id: str,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get details of a specific class."""
    cls = db.query(Classroom).filter(Classroom.id == class_id).first()
    if not cls:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found.")

    student_count = (
        db.query(ClassMembership)
        .filter(ClassMembership.class_id == cls.id, ClassMembership.status == "ACTIVE")
        .count()
    )

    teacher_name = current_user.full_name
    first_assignment = cls.teacher_assignments[0] if cls.teacher_assignments else None
    if first_assignment and first_assignment.teacher and first_assignment.teacher.user:
        teacher_name = first_assignment.teacher.user.full_name

    subject_name = cls.subject or "General"

    return ClassDetailResponse(
        id=cls.id,
        name=cls.name,
        semester=cls.semester,
        academic_year=cls.academic_year,
        subject=subject_name,
        student_count=student_count,
        teacher_name=teacher_name,
        status=cls.status
    )

# ───────────── Get class roster ─────────────

@router.get("/{class_id}/students", response_model=List[StudentRosterItem])
def get_class_student_roster(
    class_id: str,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Get all students enrolled in a class."""
    cls = db.query(Classroom).filter(Classroom.id == class_id).first()
    if not cls:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found.")

    memberships = (
        db.query(ClassMembership)
        .filter(ClassMembership.class_id == class_id, ClassMembership.status == "ACTIVE")
        .all()
    )

    roster = []
    for m in memberships:
        student = m.student
        if not student:
            continue

        has_enrollment = (
            db.query(FaceEnrollment)
            .filter(FaceEnrollment.student_id == student.id, FaceEnrollment.status == "ACTIVE")
            .first()
            is not None
        )

        roster.append(StudentRosterItem(
            id=student.id,
            student_number=student.student_number,
            name=student.full_name,
            status=student.status,
            has_enrollment=has_enrollment
        ))

    return roster

# ───────────── Delete class ─────────────

@router.delete("/{class_id}", response_model=dict)
def delete_class(
    class_id: str,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Delete a class and associated memberships."""
    cls = db.query(Classroom).filter(Classroom.id == class_id).first()
    if not cls:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found.")
    
    db.delete(cls)
    db.commit()
    return {"message": f"Class '{cls.name}' deleted successfully."}
