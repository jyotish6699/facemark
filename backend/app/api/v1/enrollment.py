import json

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
from app.schemas.enrollment import FaceEnrollmentResponse
from app.models.student import Student
from app.models.enrollment import FaceEnrollment, FaceEmbedding
from app.models.user import User
from app.api.deps import get_current_teacher
from app.services.storage_service import storage_service
from app.services.recognition_service import recognition_service


router = APIRouter(
    prefix="/students",
    tags=["Face Enrollment"],
)


@router.post(
    "/{student_id}/face-enrollment",
    response_model=FaceEnrollmentResponse,
)
async def enroll_student_face(
    student_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """
    Enroll a student's face using a real InsightFace / ArcFace embedding.

    Enrollment requirements:
    - Valid image
    - Exactly one detectable face
    - Real 512-dimensional ArcFace embedding
    - Minimum face quality
    """

    # ==========================================================
    # 1. FIND STUDENT
    # ==========================================================

    student = (
        db.query(Student)
        .filter(Student.id == student_id)
        .first()
    )

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found.",
        )

    # ==========================================================
    # 2. SAVE UPLOADED IMAGE
    # ==========================================================

    try:
        (
            storage_key,
            filename,
            file_size,
            file_hash,
        ) = await storage_service.save_upload_image(
            file,
            settings.ENROLLMENT_DIR,
        )

    except HTTPException:
        raise

    # Absolute path of saved image
    abs_path = storage_service.get_absolute_path(
        storage_key
    )

    try:

        # ======================================================
        # 3. DETECT FACES
        # ======================================================

        detected_faces = (
            recognition_service.detect_faces_in_photo(
                abs_path,
                photo_order=1,
            )
        )

        # Enrollment photo must contain exactly ONE face.
        if len(detected_faces) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "No face detected. "
                    "Please upload a clear photo containing "
                    "only the student's face."
                ),
            )

        if len(detected_faces) > 1:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "Multiple faces detected. "
                    "Please upload a photo containing "
                    "only this student."
                ),
            )

        detected_face = detected_faces[0]

        # ======================================================
        # 4. CHECK FACE QUALITY
        # ======================================================

        quality_score = float(
            detected_face.get(
                "quality_score",
                0.0,
            )
        )

        if quality_score < settings.MIN_FACE_QUALITY:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "Face quality is too low. "
                    "Please use a clearer, well-lit photo "
                    "with the face clearly visible."
                ),
            )

        # ======================================================
        # 5. GENERATE REAL ARCFACE EMBEDDING
        # ======================================================

        embedding_vec = (
            recognition_service.generate_face_embedding(
                abs_path
            )
        )

        # ======================================================
        # 6. VALIDATE EMBEDDING
        # ======================================================

        if len(embedding_vec) != 512:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "Invalid face embedding dimension. "
                    "Expected 512 dimensions."
                ),
            )

        # ======================================================
        # 7. DEACTIVATE PREVIOUS ENROLLMENTS
        # ======================================================

        (
            db.query(FaceEnrollment)
            .filter(
                FaceEnrollment.student_id
                == student.id
            )
            .update(
                {
                    "status": "REPLACED"
                },
                synchronize_session=False,
            )
        )

        # ======================================================
        # 8. CREATE NEW ENROLLMENT
        # ======================================================

        enrollment = FaceEnrollment(
            student_id=student.id,
            image_storage_key=storage_key,
            quality_score=quality_score,
            status="ACTIVE",
        )

        db.add(enrollment)

        # Get enrollment.id before creating embedding.
        db.flush()

        # ======================================================
        # 9. SAVE EMBEDDING
        # ======================================================

        face_embedding = FaceEmbedding(
            enrollment_id=enrollment.id,

            # Backward-compatible JSON representation
            embedding_json=json.dumps(
                embedding_vec
            ),

            # PostgreSQL + pgvector representation
            embedding_vector=embedding_vec,

            dimension="512",

            model_name="ArcFace-InsightFace",

            model_version=(
                settings.INSIGHTFACE_MODEL
            ),
        )

        db.add(face_embedding)

        # ======================================================
        # 10. COMMIT
        # ======================================================

        db.commit()

        db.refresh(enrollment)

    except HTTPException:
        # Rollback database transaction
        db.rollback()

        # Remove image if enrollment failed
        try:
            abs_path.unlink(
                missing_ok=True
            )
        except Exception:
            pass

        raise

    except Exception as exc:

        db.rollback()

        # Remove uploaded image if AI processing failed
        try:
            abs_path.unlink(
                missing_ok=True
            )
        except Exception:
            pass

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                f"Face enrollment failed: {str(exc)}"
            ),
        )

    # ==========================================================
    # 11. RESPONSE
    # ==========================================================

    return FaceEnrollmentResponse(
        id=enrollment.id,
        student_id=student.id,
        student_name=student.full_name,
        quality_score=enrollment.quality_score,
        status=enrollment.status,
        created_at=enrollment.created_at,
        embedding_dimension=512,
    )