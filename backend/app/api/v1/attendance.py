from datetime import datetime
from typing import List, Optional
from pathlib import Path
import tempfile

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    UploadFile,
    File,
)
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings

from app.schemas.session import (
    SessionCreateRequest,
    AttendanceSessionResponse,
    PhotoInfo,
)

from app.schemas.recognition import (
    CategorizedResultsResponse,
)

from app.schemas.review import (
    ReviewTableResponse,
    BatchReviewUpdateRequest,
    FinalizeSessionResponse,
)

from app.models.session import (
    AttendanceSession,
    SessionStatus,
)

from app.models.classroom import (
    Classroom,
    Subject,
)

from app.models.student import (
    ClassMembership,
)

from app.models.user import User

from app.api.deps import (
    get_current_teacher,
)

from app.services.attendance_service import (
    attendance_service,
)

from app.services.storage_service import (
    storage_service,
)


router = APIRouter(
    prefix="/attendance-sessions",
    tags=["Attendance Workflow"],
)


# ==========================================================
# CREATE ATTENDANCE SESSION
# ==========================================================

@router.post(
    "",
    response_model=AttendanceSessionResponse,
)
def create_attendance_session(
    request_data: SessionCreateRequest,
    current_user: User = Depends(
        get_current_teacher
    ),
    db: Session = Depends(get_db),
):
    """
    Starts a new attendance session for an assigned class.

    Session status:
        OPEN
    """

    # ======================================================
    # FIND CLASS
    # ======================================================

    cls = (
        db.query(Classroom)
        .filter(
            Classroom.id
            == request_data.class_id
        )
        .first()
    )

    if not cls:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found.",
        )

    # ======================================================
    # FIND TEACHER
    # ======================================================

    teacher = (
        current_user.teacher_profile
    )

    if (
        not teacher
        and current_user.role.value
        != "ADMIN"
    ):

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Teacher profile missing.",
        )

    # ======================================================
    # RESOLVE SUBJECT
    # ======================================================

    subject = None

    # ------------------------------------------------------
    # 1. Explicit subject ID
    # ------------------------------------------------------

    if request_data.subject_id:

        subject = (
            db.query(Subject)
            .filter(
                Subject.id
                == request_data.subject_id
            )
            .first()
        )

    # ------------------------------------------------------
    # 2. Subject name
    # ------------------------------------------------------

    if (
        not subject
        and request_data.subject_name
        and request_data.subject_name
        != "General"
    ):

        subject = (
            db.query(Subject)
            .filter(
                Subject.name
                == request_data
                .subject_name
                .strip()
            )
            .first()
        )

        if not subject:

            sub_name = (
                request_data
                .subject_name
                .strip()
            )

            subject = Subject(
                name=sub_name,
                code=(
                    f"SUB-{sub_name[:3].upper()}"
                ),
            )

            db.add(subject)

            db.flush()

    # ------------------------------------------------------
    # 3. Most recent session subject
    # ------------------------------------------------------

    if not subject:

        last_session = (
            db.query(
                AttendanceSession
            )
            .filter(
                AttendanceSession.class_id
                == cls.id
            )
            .order_by(
                AttendanceSession
                .created_at
                .desc()
            )
            .first()
        )

        if (
            last_session
            and last_session.subject
        ):

            subject = (
                last_session.subject
            )

    # ------------------------------------------------------
    # 4. Latest existing subject
    # ------------------------------------------------------

    if not subject:

        subject = (
            db.query(Subject)
            .order_by(
                Subject.created_at.desc()
            )
            .first()
        )

    # ------------------------------------------------------
    # 5. Create default subject
    # ------------------------------------------------------

    if not subject:

        sub_name = (
            f"{cls.name} Subject"
        )

        subject = Subject(
            name=sub_name,
            code=(
                f"SUB-{cls.name[:3].upper()}"
            ),
        )

        db.add(subject)

        db.flush()

    # ======================================================
    # SESSION DATE
    # ======================================================

    session_date = (
        request_data.session_date
        or datetime.utcnow().strftime(
            "%Y-%m-%d"
        )
    )

    # ======================================================
    # CREATE SESSION
    # ======================================================

    session = AttendanceSession(
        class_id=cls.id,

        subject_id=subject.id,

        teacher_id=(
            teacher.id
            if teacher
            else cls
            .teacher_assignments[0]
            .teacher_id
        ),

        session_date=session_date,

        status=SessionStatus.OPEN,
    )

    db.add(session)

    db.commit()

    db.refresh(session)

    # ======================================================
    # COUNT STUDENTS
    # ======================================================

    student_count = (
        db.query(ClassMembership)
        .filter(
            ClassMembership.class_id
            == cls.id,

            ClassMembership.status
            == "ACTIVE",
        )
        .count()
    )

    # ======================================================
    # RESPONSE
    # ======================================================

    return AttendanceSessionResponse(
        id=session.id,

        class_id=cls.id,

        class_name=cls.name,

        subject_id=subject.id,

        subject_name=subject.name,

        session_date=session.session_date,

        status=session.status,

        student_count=student_count,

        started_at=session.started_at,

        finalized_at=session.finalized_at,

        photos=[],
    )


# ==========================================================
# GET ATTENDANCE SESSION
# ==========================================================

@router.get(
    "/{session_id}",
    response_model=AttendanceSessionResponse,
)
def get_session(
    session_id: str,

    current_user: User = Depends(
        get_current_teacher
    ),

    db: Session = Depends(get_db),
):
    """
    Get attendance session details
    and uploaded classroom photos.
    """

    session = (
        db.query(AttendanceSession)
        .filter(
            AttendanceSession.id
            == session_id
        )
        .first()
    )

    if not session:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "Attendance session not found."
            ),
        )

    # ======================================================
    # COUNT STUDENTS
    # ======================================================

    student_count = (
        db.query(ClassMembership)
        .filter(
            ClassMembership.class_id
            == session.class_id,

            ClassMembership.status
            == "ACTIVE",
        )
        .count()
    )

    # ======================================================
    # PHOTO INFORMATION
    # ======================================================

    photos_info = [

        PhotoInfo(
            id=photo.id,

            photo_order=photo.photo_order,

            storage_key=photo.storage_key,

            original_filename=(
                photo.original_filename
            ),

            processing_status=(
                photo.processing_status
            ),

            faces_detected=len(
                photo.detected_faces
            ),

            uploaded_at=photo.uploaded_at,
        )

        for photo
        in session.photos
    ]

    # ======================================================
    # RESPONSE
    # ======================================================

    return AttendanceSessionResponse(
        id=session.id,

        class_id=(
            session.classroom.id
            if session.classroom
            else ""
        ),

        class_name=(
            session.classroom.name
            if session.classroom
            else "Class"
        ),

        subject_id=(
            session.subject.id
            if session.subject
            else ""
        ),

        subject_name=(
            session.subject.name
            if session.subject
            else "Subject"
        ),

        session_date=session.session_date,

        status=session.status,

        student_count=student_count,

        started_at=session.started_at,

        finalized_at=session.finalized_at,

        photos=photos_info,
    )


# ==========================================================
# UPLOAD CLASSROOM PHOTO
# ==========================================================

@router.post(
    "/{session_id}/photos",
    response_model=CategorizedResultsResponse,
)
async def upload_classroom_photo(
    session_id: str,

    file: UploadFile = File(...),

    current_user: User = Depends(
        get_current_teacher
    ),

    db: Session = Depends(get_db),
):
    """
    Upload classroom photo.

    The photo is processed using:

        InsightFace
            ↓
        Face Detection
            ↓
        ArcFace Embedding
            ↓
        Student Matching
            ↓
        Recognition Results
    """

    # ======================================================
    # FIND SESSION
    # ======================================================

    session = (
        db.query(AttendanceSession)
        .filter(
            AttendanceSession.id
            == session_id
        )
        .first()
    )

    if not session:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "Attendance session not found."
            ),
        )

    # ======================================================
    # CHECK SESSION STATUS
    # ======================================================

    if (
        session.status
        == SessionStatus.FINALIZED
    ):

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Attendance session has already "
                "been finalized."
            ),
        )

    # ======================================================
    # SAVE UPLOADED IMAGE
    # ======================================================

    (
        storage_key,
        filename,
        file_size,
        file_hash,
    ) = await storage_service.save_upload_image(
        file,
        settings.ATTENDANCE_DIR,
    )

    # ======================================================
    # PROCESS PHOTO
    # ======================================================

    attendance_service.process_session_photo(
        db=db,

        session_id=session_id,

        storage_key=storage_key,

        original_filename=filename,

        mime_type=(
            file.content_type
            or "image/jpeg"
        ),

        file_size=file_size,

        file_hash=file_hash,
    )

    # ======================================================
    # RETURN RESULTS
    # ======================================================

    return (
        attendance_service
        .get_categorized_session_results(
            db,
            session_id,
        )
    )


# ==========================================================
# REAL-TIME WEBCAM FRAME
# ==========================================================

@router.post(
    "/{session_id}/live-frame"
)
async def process_live_frame(
    session_id: str,

    file: UploadFile = File(...),

    current_user: User = Depends(
        get_current_teacher
    ),

    db: Session = Depends(get_db),
):
    """
    Process one webcam frame for real-time attendance.

    Flow:

        Browser Webcam
              ↓
        JPEG Frame
              ↓
        Temporary File
              ↓
        InsightFace
              ↓
        ArcFace
              ↓
        Student Matching
              ↓
        Evidence Accumulation
              ↓
        Attendance Record
              ↓
        JSON Response

    The webcam frame is NOT permanently stored.
    It is deleted after processing.

    Recognition failure does NOT mean absence.
    A student becomes absent only during finalization.
    """

    # ======================================================
    # 1. FIND SESSION
    # ======================================================

    session = (
        db.query(AttendanceSession)
        .filter(
            AttendanceSession.id
            == session_id
        )
        .first()
    )

    if not session:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "Attendance session not found."
            ),
        )

    # ======================================================
    # 2. CHECK SESSION STATUS
    # ======================================================

    if (
        session.status
        == SessionStatus.FINALIZED
    ):

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Attendance session has already "
                "been finalized."
            ),
        )

    # ======================================================
    # 3. VALIDATE IMAGE TYPE
    # ======================================================

    allowed_types = getattr(
        settings,
        "ALLOWED_IMAGE_TYPES",
        [
            "image/jpeg",
            "image/png",
            "image/webp",
        ],
    )

    if (
        file.content_type
        not in allowed_types
    ):

        raise HTTPException(
            status_code=(
                status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
            ),
            detail=(
                "Unsupported webcam image type."
            ),
        )

    # ======================================================
    # 4. READ FRAME
    # ======================================================

    frame_data = await file.read()

    if not frame_data:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty webcam frame.",
        )

    # ======================================================
    # 5. CHECK FRAME SIZE
    # ======================================================

    max_upload_mb = getattr(
        settings,
        "MAX_UPLOAD_SIZE_MB",
        10,
    )

    max_size = (
        max_upload_mb
        * 1024
        * 1024
    )

    if len(frame_data) > max_size:

        raise HTTPException(
            status_code=(
                status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
            ),
            detail=(
                "Webcam frame is too large."
            ),
        )

    # ======================================================
    # 6. CREATE TEMPORARY FILE
    # ======================================================

    suffix = (
        ".jpg"
        if file.content_type
        == "image/jpeg"
        else ".png"
    )

    temp_file = (
        tempfile.NamedTemporaryFile(
            prefix="facemark-live-",
            suffix=suffix,
            delete=False,
        )
    )

    temp_path = Path(
        temp_file.name
    )

    try:

        # ==================================================
        # 7. WRITE FRAME
        # ==================================================

        temp_file.write(
            frame_data
        )

        temp_file.flush()

        temp_file.close()

        # ==================================================
        # 8. PROCESS FRAME
        # ==================================================

        result = (
            attendance_service
            .process_live_frame(
                db=db,

                session_id=session_id,

                image_path=temp_path,
            )
        )

        # ==================================================
        # 9. RETURN LIVE RESULT
        # ==================================================

        return result

    except ValueError as exc:

        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail=str(exc),
        )

    except HTTPException:

        raise

    except Exception as exc:

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                f"Live attendance processing "
                f"failed: {str(exc)}"
            ),
        )

    finally:

        # ==================================================
        # 10. DELETE TEMPORARY FRAME
        # ==================================================

        try:

            temp_path.unlink(
                missing_ok=True
            )

        except Exception:

            pass


# ==========================================================
# GET RECOGNITION RESULTS
# ==========================================================

@router.get(
    "/{session_id}/results",
    response_model=CategorizedResultsResponse,
)
def get_recognition_results(
    session_id: str,

    current_user: User = Depends(
        get_current_teacher
    ),

    db: Session = Depends(get_db),
):
    """
    Get categorized recognition results:

        - Confident
        - Review
        - Unknown
        - Not Detected

    Multi-photo merge is applied.
    """

    return (
        attendance_service
        .get_categorized_session_results(
            db,
            session_id,
        )
    )


# ==========================================================
# GET REVIEW TABLE
# ==========================================================

@router.get(
    "/{session_id}/review-table",
    response_model=ReviewTableResponse,
)
def get_review_table(
    session_id: str,

    current_user: User = Depends(
        get_current_teacher
    ),

    db: Session = Depends(get_db),
):
    """
    Get complete student-by-student
    roster table for teacher review.
    """

    return (
        attendance_service
        .get_review_table_data(
            db,
            session_id,
        )
    )


# ==========================================================
# FINALIZE ATTENDANCE
# ==========================================================

@router.post(
    "/{session_id}/finalize",
    response_model=FinalizeSessionResponse,
)
def finalize_session(
    session_id: str,

    request_data: Optional[
        BatchReviewUpdateRequest
    ] = None,

    current_user: User = Depends(
        get_current_teacher
    ),

    db: Session = Depends(get_db),
):
    """
    Finalize attendance session.

    Operations:

        1. Apply teacher overrides
        2. Create final attendance records
        3. Freeze session
        4. Generate audit log
    """

    # ======================================================
    # EXTRACT MANUAL OVERRIDES
    # ======================================================

    overrides = None

    if (
        request_data
        and request_data.updates
    ):

        overrides = [
            update.model_dump()
            for update
            in request_data.updates
        ]

    # ======================================================
    # FINALIZE
    # ======================================================

    result = (
        attendance_service
        .finalize_attendance_session(
            db=db,

            session_id=session_id,

            actor_user_id=current_user.id,

            manual_overrides=overrides,
        )
    )

    # ======================================================
    # RESPONSE
    # ======================================================

    return FinalizeSessionResponse(
        **result
    )