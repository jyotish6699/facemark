from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.student import StudentCreate, StudentResponse
from app.schemas.common import MessageResponse

from app.models.student import Student, ClassMembership
from app.models.enrollment import FaceEnrollment
from app.models.classroom import Classroom
from app.models.user import User

from app.api.deps import get_current_teacher


router = APIRouter(
    prefix="/students",
    tags=["Students"]
)


# ============================================================
# Helper
# ============================================================

def build_student_response(
    student: Student,
    db: Session
) -> StudentResponse:
    """
    Convert Student model into StudentResponse.
    Also checks whether the student has an active face enrollment.
    """

    has_enrollment = (
        db.query(FaceEnrollment)
        .filter(
            FaceEnrollment.student_id == student.id,
            FaceEnrollment.status == "ACTIVE"
        )
        .first()
        is not None
    )

    return StudentResponse(
        id=student.id,
        student_number=student.student_number,
        full_name=student.full_name,
        email=student.email,
        status=student.status,
        has_face_enrollment=has_enrollment
    )


# ============================================================
# Create Student
# ============================================================

@router.post(
    "",
    response_model=StudentResponse,
    status_code=status.HTTP_201_CREATED
)
def create_student(
    student_data: StudentCreate,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """
    Create a new student.

    Registration/roll number must be unique.
    Email must also be unique when provided.
    Optionally enrolls the student into a class.
    """

    student_number = student_data.student_number.strip()

    existing = (
        db.query(Student)
        .filter(Student.student_number == student_number)
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Registration number '{student_number}' already exists."
            )
        )

    email = None

    if student_data.email:
        email = student_data.email.strip().lower()

        email_exists = (
            db.query(Student)
            .filter(Student.email == email)
            .first()
        )

        if email_exists:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Email '{email}' is already registered."
            )

    student = Student(
        student_number=student_number,
        full_name=student_data.full_name.strip(),
        email=email
    )

    db.add(student)
    db.flush()

    # --------------------------------------------------------
    # Optional class enrollment
    # --------------------------------------------------------

    if student_data.class_id:

        cls = (
            db.query(Classroom)
            .filter(Classroom.id == student_data.class_id)
            .first()
        )

        if not cls:
            db.rollback()

            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Class not found."
            )

        already_enrolled = (
            db.query(ClassMembership)
            .filter(
                ClassMembership.class_id == cls.id,
                ClassMembership.student_id == student.id
            )
            .first()
        )

        if not already_enrolled:
            db.add(
                ClassMembership(
                    class_id=cls.id,
                    student_id=student.id
                )
            )

    db.commit()
    db.refresh(student)

    return build_student_response(student, db)


# ============================================================
# Get Student
# ============================================================

@router.get(
    "/{student_id}",
    response_model=StudentResponse
)
def get_student(
    student_id: str,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """
    Get a student by ID.
    """

    student = (
        db.query(Student)
        .filter(Student.id == student_id)
        .first()
    )

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found."
        )

    return build_student_response(student, db)


# ============================================================
# List Students
# ============================================================

@router.get(
    "",
    response_model=List[StudentResponse]
)
def list_students(
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """
    Return all active students.
    """

    students = (
        db.query(Student)
        .filter(Student.status == "ACTIVE")
        .order_by(Student.student_number)
        .all()
    )

    return [
        build_student_response(student, db)
        for student in students
    ]


# ============================================================
# Enroll Student Into Class
# ============================================================

@router.post(
    "/{student_id}/enroll/{class_id}",
    response_model=MessageResponse
)
def enroll_student_in_class(
    student_id: str,
    class_id: str,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """
    Enroll an existing student into a class.
    """

    student = (
        db.query(Student)
        .filter(
            Student.id == student_id,
            Student.status == "ACTIVE"
        )
        .first()
    )

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found."
        )

    cls = (
        db.query(Classroom)
        .filter(Classroom.id == class_id)
        .first()
    )

    if not cls:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found."
        )

    already_enrolled = (
        db.query(ClassMembership)
        .filter(
            ClassMembership.class_id == cls.id,
            ClassMembership.student_id == student.id
        )
        .first()
    )

    if already_enrolled:

        # If old membership exists but is inactive,
        # reactivate it instead of creating a duplicate.
        if hasattr(already_enrolled, "status"):
            already_enrolled.status = "ACTIVE"
            db.commit()

            return MessageResponse(
                message=(
                    f"'{student.full_name}' enrollment in "
                    f"'{cls.name}' has been reactivated."
                )
            )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"'{student.full_name}' is already enrolled "
                f"in '{cls.name}'."
            )
        )

    db.add(
        ClassMembership(
            class_id=cls.id,
            student_id=student.id
        )
    )

    db.commit()

    return MessageResponse(
        message=(
            f"'{student.full_name}' enrolled in "
            f"'{cls.name}' successfully."
        )
    )


# ============================================================
# DELETE STUDENT
# ============================================================

@router.delete(
    "/{student_id}",
    response_model=MessageResponse
)
def delete_student(
    student_id: str,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """
    Safely remove a student from the active roster.

    We intentionally use a SOFT DELETE instead of physically
    deleting the database row.

    Why?
    - Attendance history may reference the student.
    - Face enrollments may reference the student.
    - Class memberships may reference the student.
    - Hard deleting could cause foreign-key errors.
    - Historical attendance should not be destroyed.

    The student becomes INACTIVE and disappears from the
    active Students & Faces list.
    """

    student = (
        db.query(Student)
        .filter(Student.id == student_id)
        .first()
    )

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found."
        )

    if student.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student is already inactive."
        )

    student_name = student.full_name

    try:

        # ----------------------------------------------------
        # 1. Deactivate student
        # ----------------------------------------------------

        student.status = "INACTIVE"

        # ----------------------------------------------------
        # 2. Deactivate all active face enrollments
        # ----------------------------------------------------

        face_enrollments = (
            db.query(FaceEnrollment)
            .filter(
                FaceEnrollment.student_id == student.id,
                FaceEnrollment.status == "ACTIVE"
            )
            .all()
        )

        for enrollment in face_enrollments:
            enrollment.status = "INACTIVE"

        # ----------------------------------------------------
        # 3. Deactivate class memberships
        # ----------------------------------------------------

        memberships = (
            db.query(ClassMembership)
            .filter(
                ClassMembership.student_id == student.id
            )
            .all()
        )

        for membership in memberships:

            # Only change status if the model has a status field.
            if hasattr(membership, "status"):
                membership.status = "INACTIVE"

        db.commit()

    except Exception as exc:

        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to delete student: {str(exc)}"
        )

    return MessageResponse(
        message=f"Student '{student_name}' deleted successfully."
    )


# ============================================================
# Remove / Disable Face Enrollment
# ============================================================

@router.delete(
    "/{student_id}/face-enrollment",
    response_model=MessageResponse
)
def remove_face_enrollment(
    student_id: str,
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """
    Remove the student's active biometric enrollment.

    The student itself is NOT deleted.
    Only active face enrollment records are deactivated.
    """

    student = (
        db.query(Student)
        .filter(Student.id == student_id)
        .first()
    )

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found."
        )

    enrollments = (
        db.query(FaceEnrollment)
        .filter(
            FaceEnrollment.student_id == student.id,
            FaceEnrollment.status == "ACTIVE"
        )
        .all()
    )

    if not enrollments:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active face enrollment found."
        )

    for enrollment in enrollments:
        enrollment.status = "INACTIVE"

    db.commit()

    return MessageResponse(
        message=(
            f"Biometric enrollment for "
            f"'{student.full_name}' removed successfully."
        )
    )