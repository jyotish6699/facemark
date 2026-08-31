import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings

from app.models.session import (
    AttendanceSession,
    AttendancePhoto,
    SessionStatus,
)

from app.models.attendance import (
    DetectedFace,
    RecognitionResult,
    AttendanceRecord,
    RecognitionStatus,
    FinalAttendanceStatus,
    AttendanceSource,
)

from app.models.student import (
    Student,
    ClassMembership,
)

from app.models.enrollment import (
    FaceEnrollment,
    FaceEmbedding,
)

from app.models.audit import AuditLog

from app.services.recognition_service import (
    recognition_service,
)

from app.services.merge_service import (
    merge_service,
)

from app.services.storage_service import (
    storage_service,
)


class AttendanceService:

    # ==========================================================
    # LIVE ATTENDANCE EVIDENCE
    # ==========================================================
    #
    # Structure:
    #
    # {
    #     session_id: {
    #         student_id: [
    #             {
    #                 "timestamp": datetime,
    #                 "confidence": float,
    #                 "quality": float
    #             }
    #         ]
    #     }
    # }
    #
    # This lets us collect evidence from multiple frames.
    #
    # IMPORTANT:
    # This is an in-memory MVP mechanism. Later, if needed,
    # we can move this to Redis/database for multi-worker
    # production deployment.
    # ==========================================================

    _live_evidence: Dict[
        str,
        Dict[str, List[Dict[str, Any]]]
    ] = {}

    # ==========================================================
    # GET ENROLLED STUDENTS + EMBEDDINGS
    # ==========================================================

    @staticmethod
    def get_enrolled_students_with_embeddings(
        db: Session,
        class_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve all active students enrolled in a class
        together with their active face embedding.

        Preference:

            PostgreSQL + pgvector
                    ↓
              embedding_vector

        Fallback:

              embedding_json
        """

        memberships = (
            db.query(ClassMembership)
            .filter(
                ClassMembership.class_id == class_id,
                ClassMembership.status == "ACTIVE",
            )
            .all()
        )

        student_data = []

        for membership in memberships:

            student = membership.student

            if not student:
                continue

            if student.status != "ACTIVE":
                continue

            # --------------------------------------------------
            # Get active enrollment
            # --------------------------------------------------

            enrollment = (
                db.query(FaceEnrollment)
                .filter(
                    FaceEnrollment.student_id == student.id,
                    FaceEnrollment.status == "ACTIVE",
                )
                .order_by(
                    FaceEnrollment.created_at.desc()
                )
                .first()
            )

            embedding_vec = None

            if enrollment:

                embedding_record = (
                    db.query(FaceEmbedding)
                    .filter(
                        FaceEmbedding.enrollment_id
                        == enrollment.id
                    )
                    .order_by(
                        FaceEmbedding.created_at.desc()
                    )
                    .first()
                )

                if embedding_record:

                    # ==========================================
                    # FIRST: pgvector
                    # ==========================================

                    vector_value = getattr(
                        embedding_record,
                        "embedding_vector",
                        None,
                    )

                    if vector_value is not None:

                        try:

                            embedding_vec = list(
                                vector_value
                            )

                        except Exception:

                            embedding_vec = None

                    # ==========================================
                    # FALLBACK: JSON
                    # ==========================================

                    if (
                        embedding_vec is None
                        and embedding_record.embedding_json
                    ):

                        try:

                            embedding_vec = json.loads(
                                embedding_record.embedding_json
                            )

                        except Exception:

                            embedding_vec = None

            # --------------------------------------------------
            # Add student
            # --------------------------------------------------

            student_data.append(
                {
                    "id": student.id,

                    "name": student.full_name,

                    "student_number": (
                        student.student_number
                    ),

                    "email": student.email,

                    "embedding": embedding_vec,
                }
            )

        return student_data

    # ==========================================================
    # PROCESS SESSION PHOTO
    # ==========================================================

    @staticmethod
    def process_session_photo(
        db: Session,
        session_id: str,
        storage_key: str,
        original_filename: str,
        mime_type: str,
        file_size: int,
        file_hash: str,
    ) -> AttendancePhoto:
        """
        Process an uploaded classroom photo.

        Pipeline:

        1. Validate session.
        2. Check duplicate photo.
        3. Detect multiple faces.
        4. Generate ArcFace embeddings.
        5. Match against class roster.
        6. Save detection results.
        7. Save recognition results.
        """

        # ======================================================
        # 1. GET SESSION
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

        if session.status == SessionStatus.FINALIZED:

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Attendance session has already "
                    "been finalized and frozen."
                ),
            )

        # ======================================================
        # 2. DUPLICATE PHOTO CHECK
        # ======================================================

        existing_photo = (
            db.query(AttendancePhoto)
            .filter(
                AttendancePhoto.session_id
                == session_id,

                AttendancePhoto.file_hash
                == file_hash,
            )
            .first()
        )

        if existing_photo:

            return existing_photo

        # ======================================================
        # 3. PHOTO ORDER
        # ======================================================

        photo_order = (
            len(session.photos) + 1
        )

        # ======================================================
        # 4. CREATE PHOTO RECORD
        # ======================================================

        photo = AttendancePhoto(
            session_id=session_id,

            storage_key=storage_key,

            original_filename=(
                original_filename
            ),

            mime_type=mime_type,

            file_size=file_size,

            file_hash=file_hash,

            photo_order=photo_order,

            processing_status="PROCESSING",
        )

        db.add(photo)

        db.flush()

        # ======================================================
        # 5. GET IMAGE PATH
        # ======================================================

        absolute_photo_path = (
            storage_service.get_absolute_path(
                storage_key
            )
        )

        try:

            # ==================================================
            # 6. REAL FACE DETECTION
            # ==================================================

            detected_faces = (
                recognition_service.detect_faces_in_photo(
                    absolute_photo_path,
                    photo_order=photo_order,
                )
            )

            # ==================================================
            # 7. GET CLASS ROSTER
            # ==================================================

            enrolled_students = (
                AttendanceService
                .get_enrolled_students_with_embeddings(
                    db,
                    session.class_id,
                )
            )

            # ==================================================
            # 8. REAL FACE MATCHING
            # ==================================================

            match_results = (
                recognition_service
                .match_faces_against_class_roster(
                    detected_faces,
                    enrolled_students,
                    photo_order=photo_order,
                )
            )

            # ==================================================
            # 9. PERSIST DETECTED FACES
            # ==================================================

            for face in detected_faces:

                detected_face = DetectedFace(
                    photo_id=photo.id,

                    face_index=face[
                        "face_index"
                    ],

                    bounding_box_json=json.dumps(
                        face["bounding_box"]
                    ),

                    quality_score=face[
                        "quality_score"
                    ],
                )

                db.add(detected_face)

                db.flush()

                # ==============================================
                # IMPORTANT:
                # recognition_service now returns:
                #
                # Face #1
                # Face #2
                # Face #3
                #
                # Do NOT modify the label using photo_order.
                # ==============================================

                face_label = (
                    f"Face #{face['face_index']}"
                )

                # ==============================================
                # CONFIDENT MATCH
                # ==============================================

                confident_match = next(
                    (
                        item
                        for item
                        in match_results["confident"]
                        if item["face_id"]
                        == face_label
                    ),
                    None,
                )

                if confident_match:

                    recognition_result = (
                        RecognitionResult(
                            session_id=session_id,

                            photo_id=photo.id,

                            detected_face_id=(
                                detected_face.id
                            ),

                            candidate_student_id=(
                                confident_match[
                                    "student_id"
                                ]
                            ),

                            confidence_score=(
                                confident_match[
                                    "confidence_score"
                                ]
                            ),

                            recognition_status=(
                                RecognitionStatus
                                .CONFIDENT_MATCH
                            ),
                        )
                    )

                    db.add(
                        recognition_result
                    )

                    continue

                # ==============================================
                # REVIEW MATCH
                # ==============================================

                review_match = next(
                    (
                        item
                        for item
                        in match_results["review"]
                        if item["face_id"]
                        == face_label
                    ),
                    None,
                )

                if review_match:

                    recognition_result = (
                        RecognitionResult(
                            session_id=session_id,

                            photo_id=photo.id,

                            detected_face_id=(
                                detected_face.id
                            ),

                            candidate_student_id=(
                                review_match.get(
                                    "candidate_student_id"
                                )
                            ),

                            confidence_score=(
                                review_match.get(
                                    "confidence_score"
                                )
                            ),

                            recognition_status=(
                                RecognitionStatus
                                .UNCERTAIN
                            ),
                        )
                    )

                    db.add(
                        recognition_result
                    )

                    continue

                # ==============================================
                # UNKNOWN
                # ==============================================

                recognition_result = (
                    RecognitionResult(
                        session_id=session_id,

                        photo_id=photo.id,

                        detected_face_id=(
                            detected_face.id
                        ),

                        candidate_student_id=None,

                        confidence_score=None,

                        recognition_status=(
                            RecognitionStatus
                            .UNKNOWN
                        ),
                    )
                )

                db.add(
                    recognition_result
                )

            # ==================================================
            # 10. COMPLETE PROCESSING
            # ==================================================

            photo.processing_status = (
                "COMPLETED"
            )

            session.status = (
                SessionStatus.REVIEW
            )

            db.commit()

            db.refresh(photo)

            return photo

        except Exception:

            db.rollback()

            raise

    # ==========================================================
    # GET CATEGORIZED SESSION RESULTS
    # ==========================================================

    @staticmethod
    def get_categorized_session_results(
        db: Session,
        session_id: str,
    ) -> Dict[str, Any]:
        """
        Calculate merged multi-photo recognition results.
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
                detail="Session not found.",
            )

        enrolled_students = (
            AttendanceService
            .get_enrolled_students_with_embeddings(
                db,
                session.class_id,
            )
        )

        photos = sorted(
            session.photos,
            key=lambda photo: photo.photo_order,
        )

        # ======================================================
        # NO PHOTOS
        # ======================================================

        if not photos:

            not_detected = [

                {
                    "student_id": student["id"],

                    "name": student["name"],

                    "student_number": (
                        student["student_number"]
                    ),

                    "status": "Not detected",
                }

                for student
                in enrolled_students
            ]

            return {
                "session_id": session.id,

                "photo_count": 0,

                "total_enrolled": (
                    len(enrolled_students)
                ),

                "confident": [],

                "review": [],

                "unknown": [],

                "not_detected": not_detected,
            }

        # ======================================================
        # PROCESS EACH PHOTO
        # ======================================================

        photo_results = []

        for photo in photos:

            result_for_photo = {
                "confident": [],
                "review": [],
                "unknown": [],
            }

            matched_ids = set()

            for result in photo.recognition_results:

                detected_face = (
                    result.detected_face
                )

                face_index = (
                    detected_face.face_index
                    if detected_face
                    else 1
                )

                face_id = (
                    f"Face #{face_index}"
                )

                # ==============================================
                # CONFIDENT
                # ==============================================

                if (
                    result.recognition_status
                    == RecognitionStatus.CONFIDENT_MATCH
                    and
                    result.candidate_student
                ):

                    score = (
                        result.confidence_score
                        or 0.0
                    )

                    result_for_photo[
                        "confident"
                    ].append(
                        {
                            "face_id": face_id,

                            "student_id": (
                                result
                                .candidate_student
                                .id
                            ),

                            "name": (
                                result
                                .candidate_student
                                .full_name
                            ),

                            "student_number": (
                                result
                                .candidate_student
                                .student_number
                            ),

                            "confidence_score": score,

                            "confidence": (
                                f"{int(score * 100)}%"
                            ),

                            "source_photo_order": (
                                photo.photo_order
                            ),
                        }
                    )

                    matched_ids.add(
                        result
                        .candidate_student
                        .id
                    )

                # ==============================================
                # UNCERTAIN
                # ==============================================

                elif (
                    result.recognition_status
                    == RecognitionStatus.UNCERTAIN
                ):

                    score = (
                        result.confidence_score
                        or 0.0
                    )

                    result_for_photo[
                        "review"
                    ].append(
                        {
                            "face_id": face_id,

                            "candidate_student_id": (
                                result
                                .candidate_student
                                .id
                                if result.candidate_student
                                else None
                            ),

                            "candidate_name": (
                                result
                                .candidate_student
                                .full_name
                                if result.candidate_student
                                else "Uncertain"
                            ),

                            "confidence_score": score,

                            "confidence": (
                                f"{int(score * 100)}%"
                            ),

                            "source_photo_order": (
                                photo.photo_order
                            ),
                        }
                    )

                # ==============================================
                # UNKNOWN
                # ==============================================

                else:

                    result_for_photo[
                        "unknown"
                    ].append(
                        {
                            "face_id": face_id,

                            "candidate": "Unknown",

                            "source_photo_order": (
                                photo.photo_order
                            ),
                        }
                    )

            # ==================================================
            # NOT DETECTED
            # ==================================================

            result_for_photo[
                "not_detected"
            ] = [

                {
                    "student_id": student["id"],

                    "name": student["name"],

                    "student_number": (
                        student["student_number"]
                    ),

                    "status": "Not detected",
                }

                for student
                in enrolled_students

                if student["id"]
                not in matched_ids
            ]

            photo_results.append(
                result_for_photo
            )

        # ======================================================
        # MERGE MULTIPLE PHOTOS
        # ======================================================

        if len(photo_results) == 1:

            merged = photo_results[0]

        else:

            merged = photo_results[0]

            for next_result in photo_results[1:]:

                merged = (
                    merge_service
                    .merge_photo_recognition_results(
                        merged,
                        next_result,
                    )
                )

        # ======================================================
        # RETURN
        # ======================================================

        return {
            "session_id": session.id,

            "photo_count": len(photos),

            "total_enrolled": (
                len(enrolled_students)
            ),

            "confident": merged[
                "confident"
            ],

            "review": merged[
                "review"
            ],

            "unknown": merged[
                "unknown"
            ],

            "not_detected": merged[
                "not_detected"
            ],
        }

    # ==========================================================
    # REVIEW TABLE
    # ==========================================================

    @staticmethod
    def get_review_table_data(
        db: Session,
        session_id: str,
    ) -> Dict[str, Any]:
        """
        Build student-by-student attendance review table.
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
                detail="Session not found.",
            )

        enrolled_students = (
            AttendanceService
            .get_enrolled_students_with_embeddings(
                db,
                session.class_id,
            )
        )

        categorized = (
            AttendanceService
            .get_categorized_session_results(
                db,
                session_id,
            )
        )

        # ======================================================
        # CREATE LOOKUP MAPS
        # ======================================================

        confident_map = {
            item["student_id"]: item
            for item
            in categorized["confident"]
        }

        review_candidate_map = {
            item["candidate_student_id"]: item

            for item
            in categorized["review"]

            if item.get(
                "candidate_student_id"
            )
        }

        # ======================================================
        # EXISTING ATTENDANCE RECORDS
        # ======================================================

        existing_records = {
            record.student_id: record

            for record
            in session.attendance_records
        }

        students_review = []

        # ======================================================
        # BUILD STUDENT TABLE
        # ======================================================

        for student in enrolled_students:

            student_id = student["id"]

            # ================================================
            # ALREADY RECORDED
            # ================================================

            if student_id in existing_records:

                record = (
                    existing_records[
                        student_id
                    ]
                )

                is_present = (
                    record.final_status
                    == FinalAttendanceStatus.PRESENT
                )

                students_review.append(
                    {
                        "id": student_id,

                        "name": student["name"],

                        "student_number": (
                            student["student_number"]
                        ),

                        "recognition": (
                            "Present"
                            if is_present
                            else "Absent"
                        ),

                        "final_status": (
                            record.final_status
                        ),

                        "confidence": "Confirmed",

                        "is_confirmed": True,
                    }
                )

                continue

            # ================================================
            # CONFIDENT AI MATCH
            # ================================================

            if student_id in confident_map:

                item = (
                    confident_map[
                        student_id
                    ]
                )

                students_review.append(
                    {
                        "id": student_id,

                        "name": student["name"],

                        "student_number": (
                            student["student_number"]
                        ),

                        "recognition": "Present",

                        "final_status": (
                            FinalAttendanceStatus.PRESENT
                        ),

                        "confidence": (
                            item["confidence"]
                        ),

                        "is_confirmed": False,
                    }
                )

                continue

            # ================================================
            # UNCERTAIN AI MATCH
            # ================================================

            if student_id in review_candidate_map:

                item = (
                    review_candidate_map[
                        student_id
                    ]
                )

                students_review.append(
                    {
                        "id": student_id,

                        "name": student["name"],

                        "student_number": (
                            student["student_number"]
                        ),

                        "recognition": "Review",

                        "final_status": (
                            FinalAttendanceStatus.PRESENT
                        ),

                        "confidence": (
                            item["confidence"]
                        ),

                        "is_confirmed": False,
                    }
                )

                continue

            # ================================================
            # NOT DETECTED
            # ================================================

            students_review.append(
                {
                    "id": student_id,

                    "name": student["name"],

                    "student_number": (
                        student["student_number"]
                    ),

                    "recognition": (
                        "Not detected"
                    ),

                    "final_status": (
                        FinalAttendanceStatus.ABSENT
                    ),

                    "confidence": "N/A",

                    "is_confirmed": False,
                }
            )

        # ======================================================
        # RETURN
        # ======================================================

        return {
            "session_id": session.id,

            "class_name": (
                session.classroom.name
                if session.classroom
                else "Class"
            ),

            "subject_name": (
                session.subject.name
                if session.subject
                else "Subject"
            ),

            "session_date": (
                session.session_date
            ),

            "students": students_review,
        }

    # ==========================================================
    # FINALIZE ATTENDANCE
    # ==========================================================

    @staticmethod
    def finalize_attendance_session(
        db: Session,
        session_id: str,
        actor_user_id: str,
        manual_overrides: Optional[
            List[Dict[str, Any]]
        ] = None,
    ) -> Dict[str, Any]:
        """
        Finalize attendance.

        IMPORTANT:

        A student who was not recognized during one frame
        is NOT automatically considered absent.

        Absence is decided at finalization time.
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
                detail="Session not found.",
            )

        if session.status == SessionStatus.FINALIZED:

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Session is already finalized."
                ),
            )

        review_data = (
            AttendanceService
            .get_review_table_data(
                db,
                session_id,
            )
        )

        students_review = {
            student["id"]: student

            for student
            in review_data["students"]
        }

        # ======================================================
        # APPLY MANUAL OVERRIDES
        # ======================================================

        if manual_overrides:

            for item in manual_overrides:

                student_id = item.get(
                    "student_id"
                )

                status_value = item.get(
                    "final_status"
                )

                if (
                    student_id
                    in students_review
                    and
                    status_value
                ):

                    students_review[
                        student_id
                    ][
                        "final_status"
                    ] = FinalAttendanceStatus(
                        status_value
                    )

        # ======================================================
        # CLEAR DRAFT RECORDS
        # ======================================================

        (
            db.query(AttendanceRecord)
            .filter(
                AttendanceRecord.session_id
                == session_id
            )
            .delete(
                synchronize_session=False
            )
        )

        present_count = 0

        absent_count = 0

        # ======================================================
        # CREATE FINAL RECORDS
        # ======================================================

        for student_id, student_info in (
            students_review.items()
        ):

            final_status = (
                student_info[
                    "final_status"
                ]
            )

            if isinstance(
                final_status,
                str,
            ):

                final_status = (
                    FinalAttendanceStatus(
                        final_status
                    )
                )

            if (
                final_status
                == FinalAttendanceStatus.PRESENT
            ):

                present_count += 1

            else:

                absent_count += 1

            record = AttendanceRecord(
                session_id=session_id,

                student_id=student_id,

                final_status=final_status,

                source=AttendanceSource.TEACHER,

                reviewed_by=actor_user_id,

                reviewed_at=datetime.utcnow(),
            )

            db.add(record)

        # ======================================================
        # FINALIZE SESSION
        # ======================================================

        session.status = (
            SessionStatus.FINALIZED
        )

        session.finalized_at = (
            datetime.utcnow()
        )

        # ======================================================
        # AUDIT LOG
        # ======================================================

        audit = AuditLog(
            actor_user_id=actor_user_id,

            entity_type="AttendanceSession",

            entity_id=session.id,

            action="FINALIZE_ATTENDANCE",

            new_value=json.dumps(
                {
                    "present": present_count,

                    "absent": absent_count,

                    "finalized_at": (
                        session
                        .finalized_at
                        .isoformat()
                    ),
                }
            ),
        )

        db.add(audit)

        db.commit()

        # ======================================================
        # CLEAR LIVE EVIDENCE
        # ======================================================

        AttendanceService._live_evidence.pop(
            session_id,
            None,
        )

        # ======================================================
        # RESPONSE
        # ======================================================

        return {
            "session_id": session.id,

            "status": "FINALIZED",

            "finalized_at": (
                session
                .finalized_at
                .isoformat()
            ),

            "total_students": (
                len(students_review)
            ),

            "present_count": present_count,

            "absent_count": absent_count,

            "message": (
                "Attendance successfully "
                "finalized and recorded."
            ),
        }

    # ==========================================================
    # PROCESS REAL-TIME FRAME
    # ==========================================================

    @classmethod
    def process_live_frame(
        cls,
        db: Session,
        session_id: str,
        image_path,
    ) -> Dict[str, Any]:
        """
        Process one webcam frame.

        The live pipeline intentionally separates:
            1. frame-level recognition
            2. session-level attendance

        A student is NOT marked absent because they disappear from
        a single frame. A student becomes PRESENT only after enough
        positive evidence has been collected.

        Evidence is kept in memory for this MVP. Attendance itself
        is persisted in the database.
        """

        # ======================================================
        # 1. FIND SESSION
        # ======================================================

        session = (
            db.query(AttendanceSession)
            .filter(
                AttendanceSession.id == session_id
            )
            .first()
        )

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found.",
            )

        # ======================================================
        # 2. SESSION STATE
        # ======================================================

        if session.status == SessionStatus.FINALIZED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session is finalized.",
            )

        # ======================================================
        # 3. GET ACTIVE CLASS ROSTER + EMBEDDINGS
        # ======================================================

        enrolled_students = (
            cls.get_enrolled_students_with_embeddings(
                db,
                session.class_id,
            )
        )

        # Students without an embedding cannot be recognized.
        enrolled_students_with_embeddings = [
            student
            for student in enrolled_students
            if student.get("embedding")
        ]

        # ======================================================
        # 4. DETECT FACES
        # ======================================================

        detected_faces = (
            recognition_service.detect_faces_in_photo(
                image_path,
                photo_order=1,
            )
        )

        # ======================================================
        # 5. MATCH AGAINST CLASS ROSTER
        # ======================================================

        match_results = (
            recognition_service.match_faces_against_class_roster(
                detected_faces,
                enrolled_students_with_embeddings,
                photo_order=1,
            )
        )

        # ======================================================
        # 6. SESSION EVIDENCE STORE
        # ======================================================

        session_evidence = cls._live_evidence.setdefault(
            session_id,
            {},
        )

        now = datetime.utcnow()

        evidence_window = timedelta(
            seconds=getattr(
                settings,
                "LIVE_EVIDENCE_WINDOW_SECONDS",
                30,
            )
        )

        max_evidence = max(
            1,
            int(
                getattr(
                    settings,
                    "LIVE_MAX_EVIDENCE_FRAMES",
                    5,
                )
            ),
        )

        confident_threshold = float(
            getattr(
                settings,
                "SIMILARITY_THRESHOLD_CONFIDENT",
                0.55,
            )
        )

        review_threshold = float(
            getattr(
                settings,
                "SIMILARITY_THRESHOLD_REVIEW",
                0.42,
            )
        )

        min_face_quality = float(
            getattr(
                settings,
                "MIN_FACE_QUALITY",
                0.35,
            )
        )

        newly_present = []

        # ======================================================
        # 7. PROCESS CONFIDENT MATCHES
        # ======================================================

        for match in match_results.get(
            "confident",
            [],
        ):

            student_id = match.get(
                "student_id"
            )

            if not student_id:
                continue

            confidence = float(
                match.get(
                    "confidence_score",
                    0.0,
                )
            )

            # ----------------------------------------------
            # Find quality for this matched face
            # ----------------------------------------------

            detected_face = next(
                (
                    face
                    for face in detected_faces
                    if (
                        f"Face #{face['face_index']}"
                        == match.get("face_id")
                    )
                ),
                None,
            )

            quality = float(
                detected_face.get(
                    "quality_score",
                    0.0,
                )
                if detected_face
                else 0.0
            )

            # ----------------------------------------------
            # Get evidence list
            # ----------------------------------------------

            evidence_list = session_evidence.setdefault(
                student_id,
                [],
            )

            # Remove stale observations.
            evidence_list[:] = [
                evidence
                for evidence in evidence_list
                if (
                    now - evidence["timestamp"]
                ) <= evidence_window
            ]

            # ----------------------------------------------
            # Add current observation
            # ----------------------------------------------

            evidence_list.append(
                {
                    "timestamp": now,
                    "confidence": confidence,
                    "quality": quality,
                }
            )

            if len(evidence_list) > max_evidence:
                del evidence_list[:-max_evidence]

            # ----------------------------------------------
            # Check if already present in DB
            # ----------------------------------------------

            existing_record = (
                db.query(AttendanceRecord)
                .filter(
                    AttendanceRecord.session_id == session_id,
                    AttendanceRecord.student_id == student_id,
                )
                .first()
            )

            if existing_record:
                continue

            # ----------------------------------------------
            # Recent evidence
            # ----------------------------------------------

            recent_observations = [
                item
                for item in evidence_list
                if (
                    now - item["timestamp"]
                ) <= evidence_window
            ]

            # At least two good observations are preferred.
            # A single exceptionally strong, high-quality frame
            # may also be accepted.
            good_observations = [
                item
                for item in recent_observations
                if (
                    item["confidence"] >= review_threshold
                    and item["quality"] >= min_face_quality
                )
            ]

            strong_single_match = (
                confidence >= confident_threshold
                and quality >= min_face_quality
            )

            repeated_match = (
                len(good_observations) >= 2
            )

            if not (
                strong_single_match
                or repeated_match
            ):
                continue

            # ----------------------------------------------
            # Persist PRESENT attendance
            # ----------------------------------------------

            attendance_record = AttendanceRecord(
                session_id=session_id,
                student_id=student_id,
                final_status=FinalAttendanceStatus.PRESENT,
                source=AttendanceSource.AI,
                reviewed_by=None,
                reviewed_at=None,
            )

            db.add(attendance_record)

            newly_present.append(
                {
                    "student_id": student_id,
                    "name": match.get(
                        "name",
                        "Student",
                    ),
                    "student_number": match.get(
                        "student_number"
                    ),
                    "confidence": match.get(
                        "confidence",
                        f"{int(confidence * 100)}%",
                    ),
                    "confidence_score": confidence,
                    "quality_score": quality,
                    "evidence_count": len(
                        good_observations
                    ),
                }
            )

        # ======================================================
        # 8. COMMIT NEW ATTENDANCE
        # ======================================================

        if newly_present:
            db.commit()

        # ======================================================
        # 9. FETCH COMPLETE PRESENT LIST
        # ======================================================

        present_records = (
            db.query(AttendanceRecord)
            .filter(
                AttendanceRecord.session_id == session_id,
                AttendanceRecord.final_status
                == FinalAttendanceStatus.PRESENT,
            )
            .all()
        )

        present_ids = {
            record.student_id
            for record in present_records
        }

        # Build a lookup so the frontend can keep showing all
        # students confirmed during this session.
        roster_by_id = {
            student["id"]: student
            for student in enrolled_students
        }

        present_students = []

        for student_id in present_ids:

            student = roster_by_id.get(
                student_id
            )

            if not student:
                continue

            # Latest evidence for display.
            evidence_list = session_evidence.get(
                student_id,
                [],
            )

            latest = (
                evidence_list[-1]
                if evidence_list
                else None
            )

            latest_confidence = (
                latest["confidence"]
                if latest
                else None
            )

            present_students.append(
                {
                    "student_id": student_id,
                    "id": student_id,
                    "name": student["name"],
                    "student_number": student[
                        "student_number"
                    ],
                    "confidence_score": (
                        latest_confidence
                    ),
                    "confidence": (
                        f"{int(latest_confidence * 100)}%"
                        if latest_confidence is not None
                        else "Confirmed"
                    ),
                    "evidence_count": len(
                        evidence_list
                    ),
                    "status": "PRESENT",
                }
            )

        # ======================================================
        # 10. CURRENT FRAME CONFIDENT MATCHES
        # ======================================================

        current_confident = []

        for match in match_results.get(
            "confident",
            [],
        ):

            student_id = match.get(
                "student_id"
            )

            if not student_id:
                continue

            current_confident.append(
                {
                    "student_id": student_id,
                    "id": student_id,
                    "name": match.get(
                        "name",
                        "Student",
                    ),
                    "student_number": match.get(
                        "student_number"
                    ),
                    "confidence_score": match.get(
                        "confidence_score",
                        0.0,
                    ),
                    "confidence": match.get(
                        "confidence",
                        "Matched",
                    ),
                    "status": (
                        "PRESENT"
                        if student_id in present_ids
                        else "OBSERVED"
                    ),
                }
            )

        # ======================================================
        # 11. RETURN LIVE RESPONSE
        # ======================================================

        return {
            "session_id": session_id,

            # Current frame information.
            "detected_faces": len(
                detected_faces
            ),

            # Students that became present during
            # THIS frame.
            "newly_present": newly_present,

            # All students confirmed present in
            # THIS attendance session.
            "present": present_students,

            # Current frame confident matches.
            "confident": current_confident,

            "present_count": len(
                present_ids
            ),

            "total_enrolled": len(
                enrolled_students
            ),

            # Faces that need teacher review.
            "review": match_results.get(
                "review",
                [],
            ),

            # Faces with no acceptable candidate.
            "unknown": match_results.get(
                "unknown",
                [],
            ),
        }


# ==============================================================
# SERVICE INSTANCE
# ==============================================================

attendance_service = AttendanceService()