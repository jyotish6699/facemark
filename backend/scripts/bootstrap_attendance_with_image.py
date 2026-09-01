#!/usr/bin/env python3
import argparse
import hashlib
import json
import shutil
import sys
import uuid
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import app.models  # noqa: F401
from app.config import settings
from app.database import Base, SessionLocal, engine
from app.models.attendance import FinalAttendanceStatus
from app.models.classroom import Classroom, Subject
from app.models.enrollment import FaceEmbedding, FaceEnrollment
from app.models.session import AttendanceSession, SessionStatus
from app.models.student import ClassMembership, Student
from app.models.teacher import TeacherClass
from app.models.user import User, UserRole
from app.services.attendance_service import attendance_service
from app.services.recognition_service import recognition_service
from app.services.seed_service import seed_database


def create_unique_subject_code(db, subject_name: str) -> str:
    base = "".join(ch for ch in subject_name.upper() if ch.isalnum())[:6] or "GEN"
    candidate = base
    suffix = 1
    while db.query(Subject).filter(Subject.code == candidate).first() is not None:
        candidate = f"{base[:4]}{suffix:02d}"
        suffix += 1
    return candidate


def copy_image_to_dir(source: Path, destination_dir: Path) -> tuple[str, int, str]:
    content = source.read_bytes()
    file_hash = hashlib.sha256(content).hexdigest()
    suffix = source.suffix.lower() if source.suffix else ".jpg"
    filename = f"{uuid.uuid4()}{suffix}"
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination_path = destination_dir / filename
    shutil.copy2(source, destination_path)
    storage_key = str(destination_path.relative_to(settings.BASE_DIR)).replace("\\", "/")
    return storage_key, len(content), file_hash


def guess_mime_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".png":
        return "image/png"
    if suffix == ".webp":
        return "image/webp"
    return "image/jpeg"


def bootstrap(args) -> None:
    image_path = Path(args.image_path).expanduser().resolve()
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)

        teacher_user = (
            db.query(User)
            .filter(User.email == args.teacher_email, User.role == UserRole.TEACHER)
            .first()
        )
        if not teacher_user or not teacher_user.teacher_profile:
            raise RuntimeError(
                f"Teacher '{args.teacher_email}' not found. Seeded default is teacher@facemark.demo."
            )
        teacher_id = teacher_user.teacher_profile.id

        classroom = db.query(Classroom).filter(Classroom.name == args.class_name).first()
        if classroom is None:
            classroom = Classroom(
                name=args.class_name,
                semester=args.semester,
                academic_year=args.academic_year,
                subject=args.subject_name,
                status="ACTIVE",
            )
            db.add(classroom)
            db.flush()

        assignment = (
            db.query(TeacherClass)
            .filter(TeacherClass.teacher_id == teacher_id, TeacherClass.class_id == classroom.id)
            .first()
        )
        if assignment is None:
            db.add(TeacherClass(teacher_id=teacher_id, class_id=classroom.id, status="ACTIVE"))

        student = db.query(Student).filter(Student.student_number == args.student_number).first()
        if student is None:
            student = Student(
                student_number=args.student_number,
                full_name=args.student_name,
                email=args.student_email,
                status="ACTIVE",
            )
            db.add(student)
            db.flush()
        else:
            student.full_name = args.student_name
            student.email = args.student_email
            student.status = "ACTIVE"

        membership = (
            db.query(ClassMembership)
            .filter(ClassMembership.class_id == classroom.id, ClassMembership.student_id == student.id)
            .first()
        )
        if membership is None:
            db.add(ClassMembership(class_id=classroom.id, student_id=student.id, status="ACTIVE"))
        else:
            membership.status = "ACTIVE"

        detected_faces = recognition_service.detect_faces_in_photo(image_path, photo_order=1)
        if len(detected_faces) != 1:
            raise RuntimeError(
                f"Enrollment image must contain exactly one face; detected {len(detected_faces)} faces."
            )

        quality_score = float(detected_faces[0].get("quality_score", 0.0))
        if quality_score < settings.MIN_FACE_QUALITY:
            raise RuntimeError(
                f"Detected face quality {quality_score:.3f} is below threshold {settings.MIN_FACE_QUALITY:.3f}."
            )

        embedding_vec = recognition_service.generate_face_embedding(image_path)
        if len(embedding_vec) != 512:
            raise RuntimeError(f"Expected 512-d embedding, got {len(embedding_vec)}.")

        (
            db.query(FaceEnrollment)
            .filter(FaceEnrollment.student_id == student.id)
            .update({"status": "REPLACED"}, synchronize_session=False)
        )

        enrollment_storage_key, _, _ = copy_image_to_dir(image_path, settings.ENROLLMENT_DIR)
        enrollment = FaceEnrollment(
            student_id=student.id,
            image_storage_key=enrollment_storage_key,
            quality_score=quality_score,
            status="ACTIVE",
        )
        db.add(enrollment)
        db.flush()

        db.add(
            FaceEmbedding(
                enrollment_id=enrollment.id,
                embedding_json=json.dumps(embedding_vec),
                embedding_vector=embedding_vec,
                dimension="512",
                model_name="ArcFace-InsightFace",
                model_version=settings.INSIGHTFACE_MODEL,
            )
        )

        subject = db.query(Subject).filter(Subject.name == args.subject_name).first()
        if subject is None:
            subject = Subject(
                name=args.subject_name,
                code=create_unique_subject_code(db, args.subject_name),
            )
            db.add(subject)
            db.flush()

        session = AttendanceSession(
            class_id=classroom.id,
            subject_id=subject.id,
            teacher_id=teacher_id,
            session_date=datetime.utcnow().strftime("%Y-%m-%d"),
            status=SessionStatus.OPEN,
        )
        db.add(session)
        db.flush()

        attendance_storage_key, attendance_size, attendance_hash = copy_image_to_dir(
            image_path,
            settings.ATTENDANCE_DIR,
        )

        attendance_service.process_session_photo(
            db=db,
            session_id=session.id,
            storage_key=attendance_storage_key,
            original_filename=image_path.name,
            mime_type=guess_mime_type(image_path),
            file_size=attendance_size,
            file_hash=attendance_hash,
        )
        result = attendance_service.get_categorized_session_results(db, session.id)

        present_by_confident = {item["student_id"] for item in result["confident"]}
        if student.id not in present_by_confident:
            raise RuntimeError(
                "E2E check failed: enrolled student not returned as a confident match for attendance image."
            )

        review_table = attendance_service.get_review_table_data(db, session.id)
        final_status = next(
            (row["final_status"] for row in review_table["students"] if row["id"] == student.id),
            FinalAttendanceStatus.ABSENT,
        )
        if final_status != FinalAttendanceStatus.PRESENT:
            raise RuntimeError("E2E check failed: enrolled student is not marked PRESENT in review table.")

        print("SUCCESS")
        print(f"Student: {student.full_name} ({student.student_number})")
        print(f"Class: {classroom.name}")
        print(f"Session ID: {session.id}")
        print(f"Confident count: {len(result['confident'])}")
        print(f"Matched student IDs: {sorted(present_by_confident)}")
    finally:
        db.close()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Enroll one student from image, then verify attendance recognition end-to-end.",
    )
    parser.add_argument("--image-path", required=True, help="Absolute path to the enrollment/attendance image.")
    parser.add_argument("--student-name", default="Jyotish Kumar")
    parser.add_argument("--student-number", default="JYOTISH-001")
    parser.add_argument("--student-email", default="jyotish.kumar@example.com")
    parser.add_argument("--class-name", default="CSE-A")
    parser.add_argument("--subject-name", default="General")
    parser.add_argument("--semester", type=int, default=5)
    parser.add_argument("--academic-year", default="2026-2027")
    parser.add_argument("--teacher-email", default="teacher@facemark.demo")
    return parser.parse_args()


if __name__ == "__main__":
    bootstrap(parse_args())
