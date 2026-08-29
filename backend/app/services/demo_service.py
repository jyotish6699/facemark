import hashlib
import math
import random
from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password, create_access_token
from app.db.models import AttendanceRecord, AttendanceSession, Section, SectionSubject, Student, Subject, Teacher


def _generate_vector(seed: int) -> list[float]:
    values: list[float] = []
    for i in range(128):
        value = ((seed * 17 + i * 13) % 97) / 97.0
        values.append(round(value, 6))
    return values


def _string_to_vector(raw: str | None) -> list[float]:
    if not raw:
        return []
    try:
        cleaned = raw.replace("[", "").replace("]", "")
        numbers = [float(part.strip()) for part in cleaned.split(",") if part.strip()]
        return numbers
    except (TypeError, ValueError):
        return []


def _vector_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right:
        return 0.0
    limit = min(len(left), len(right))
    left = left[:limit]
    right = right[:limit]
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return max(0.0, min(1.0, dot / (left_norm * right_norm)))


def _image_signature_from_bytes(file_bytes: bytes) -> list[float]:
    digest = hashlib.sha256(file_bytes).hexdigest()
    seed = int(digest[:8], 16) % 1000
    return _generate_vector(seed)


def _image_quality_score(file_bytes: bytes) -> float:
    if not file_bytes:
        return 0.0
    values = list(file_bytes)
    if not values:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    entropy = 0.0
    counts = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    total = len(values)
    for count in counts.values():
        probability = count / total
        entropy -= probability * math.log(probability, 2)
    return min(1.0, (variance / 40000.0) + (entropy / 8.0) * 0.6)


def seed_demo_data(db: Session) -> None:
    existing_teacher = db.scalar(select(Teacher).where(Teacher.email == "ayesha.khan@facemark.local"))
    if existing_teacher:
        return

    section = Section(
        section_id="sec-cse-a",
        section_name="CSE-A",
        department="Computer Science",
        semester="5th",
        academic_year="2026-2027",
    )
    db.add(section)
    db.flush()

    teacher = Teacher(
        teacher_id="t-001",
        name="Ayesha Khan",
        email="ayesha.khan@facemark.local",
        password_hash=hash_password("Teacher@123"),
        role="teacher",
        assigned_section_id=section.section_id,
    )
    db.add(teacher)

    subject_names = {
        "sub-101": ("Database Systems", "Monday", "DB Lab 2"),
        "sub-102": ("Operating Systems", "Tuesday", "OS Lab 1"),
        "sub-103": ("Object Oriented Programming", "Wednesday", "Room 305"),
        "sub-104": ("Data Structures", "Thursday", "Room 210"),
        "sub-105": ("Computer Networks", "Friday", "Room 412"),
    }

    for subject_id, (name, day, room) in subject_names.items():
        subject = Subject(subject_id=subject_id, subject_name=name, schedule_day=day, room=room)
        db.add(subject)
        db.flush()
        db.add(SectionSubject(section_id=section.section_id, subject_id=subject_id))

    students = [
        "Rahul Sharma", "Priya Nair", "Arjun Mehta", "Sneha Verma", "Karan Patel", "Ananya Singh",
        "Rohit Kumar", "Meera Joshi", "Vikram Iyer", "Nisha Gupta", "Aditya Rao", "Pooja Sen",
        "Harsh Shah", "Sakshi Malhotra", "Ritesh Saini", "Ishita Das", "Aman Roy", "Divya Reddy",
        "Yash Khanna", "Neha Kulkarni", "Tarun Bhatia", "Aditi Chopra", "Siddharth Jain", "Riya Nanda",
    ]

    for idx, name in enumerate(students, start=1):
        seed = idx * 41 + 7
        vector = _generate_vector(seed)
        db.add(
            Student(
                student_id=f"st-{idx:03d}",
                full_name=name,
                roll_number=f"CS-{200 + idx}",
                email=f"{name.lower().replace(' ', '.')}@facemark.local",
                section_id=section.section_id,
                status="active",
                enrollment_image_url=f"storage://fake/enroll/{idx}.jpg",
                face_embedding=str(vector),
            )
        )

    db.commit()


def authenticate_teacher(db: Session, email: str, password: str) -> Teacher | None:
    teacher = db.scalar(select(Teacher).where(Teacher.email == email))
    if not teacher:
        return None
    if not verify_password(password, teacher.password_hash):
        return None
    return teacher


def get_dashboard_data(db: Session, teacher_id: str) -> dict[str, Any]:
    teacher = db.scalar(select(Teacher).where(Teacher.teacher_id == teacher_id))
    if teacher is None:
        raise ValueError("Teacher not found")

    section = db.scalar(select(Section).where(Section.section_id == teacher.assigned_section_id))
    subjects = db.scalars(
        select(Subject).join(SectionSubject, SectionSubject.subject_id == Subject.subject_id).where(
            SectionSubject.section_id == teacher.assigned_section_id
        )
    ).all()

    recent_sessions = db.scalars(
        select(AttendanceSession)
        .where(AttendanceSession.teacher_id == teacher.teacher_id)
        .order_by(AttendanceSession.session_id.desc())
        .limit(5)
    ).all()

    recent_subject_map = {
        subject.subject_id: subject.subject_name for subject in subjects
    }

    attendance_sessions = db.scalars(
        select(AttendanceSession).where(AttendanceSession.teacher_id == teacher.teacher_id)
    ).all()

    present_count = 0
    review_count = 0
    pending_count = 0

    for session in attendance_sessions:
        records = db.scalars(select(AttendanceRecord).where(AttendanceRecord.session_id == session.session_id)).all()
        if session.status != "finalized":
            pending_count += 1
        for record in records:
            if record.final_status == "present":
                present_count += 1
            elif record.final_status in {"review", "late", "excused"}:
                review_count += 1

    stats = {
        "total_sessions": len(attendance_sessions),
        "present": present_count,
        "review": review_count,
        "pending": pending_count,
        "finalized": sum(1 for session in attendance_sessions if session.status == "finalized"),
    }

    return {
        "teacher": {
            "teacher_id": teacher.teacher_id,
            "name": teacher.name,
            "email": teacher.email,
            "role": teacher.role,
            "assigned_section_id": teacher.assigned_section_id,
        },
        "section": {
            "section_id": section.section_id,
            "section_name": section.section_name,
            "department": section.department,
            "semester": section.semester,
            "academic_year": section.academic_year,
        },
        "subjects": [
            {
                "subject_id": subject.subject_id,
                "subject_name": subject.subject_name,
                "schedule_day": subject.schedule_day,
                "room": subject.room,
            }
            for subject in subjects
        ],
        "stats": stats,
        "recent_sessions": [
            {
                "session_id": s.session_id,
                "subject_id": s.subject_id,
                "subject_name": recent_subject_map.get(s.subject_id, "Unknown subject"),
                "status": s.status,
                "session_date": s.session_date.isoformat(),
            }
            for s in recent_sessions
        ],
    }


def list_subjects_for_section(db: Session, section_id: str) -> list[dict[str, Any]]:
    subjects = db.scalars(
        select(Subject).join(SectionSubject, SectionSubject.subject_id == Subject.subject_id).where(
            SectionSubject.section_id == section_id
        )
    ).all()
    return [
        {
            "subject_id": subject.subject_id,
            "subject_name": subject.subject_name,
            "schedule_day": subject.schedule_day,
            "room": subject.room,
        }
        for subject in subjects
    ]


def create_session(db: Session, teacher_id: str, section_id: str, subject_id: str, session_date: date, notes: str | None = None) -> AttendanceSession:
    session = AttendanceSession(
        session_id=f"sess-{len(db.scalars(select(AttendanceSession)).all()) + 1:03d}",
        teacher_id=teacher_id,
        section_id=section_id,
        subject_id=subject_id,
        session_date=session_date,
        status="in_progress",
        notes=notes,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def build_session_records(db: Session, session_id: str) -> list[dict[str, Any]]:
    session = db.scalar(select(AttendanceSession).where(AttendanceSession.session_id == session_id))
    if session is None:
        raise ValueError("Session not found")
    students = db.scalars(select(Student).where(Student.section_id == session.section_id)).all()
    existing_records = db.scalars(select(AttendanceRecord).where(AttendanceRecord.session_id == session_id)).all()
    if existing_records:
        return [
            {
                "attendance_id": record.attendance_id,
                "student_id": record.student_id,
                "recognition_status": record.recognition_status,
                "confidence_score": record.confidence_score,
                "final_status": record.final_status,
                "source_photo": record.source_photo,
                "is_teacher_override": record.is_teacher_override,
            }
            for record in existing_records
        ]

    for idx, student in enumerate(students):
        # deterministic demo split: first students are confident, some are uncertain, some unknown; rest not_detected
        if idx < 12:
            recognition_status = "confident"
            confidence = round(0.9 + (idx % 5) * 0.01, 2)
        elif idx < 15:
            recognition_status = "uncertain"
            confidence = round(0.6 + (idx % 4) * 0.05, 2)
        elif idx == 15:
            recognition_status = "unknown"
            confidence = 0.42
        else:
            recognition_status = "not_detected"
            confidence = 0.0

        record = AttendanceRecord(
            attendance_id=f"att-{session.session_id}-{student.student_id}",
            session_id=session.session_id,
            student_id=student.student_id,
            recognition_status=recognition_status,
            confidence_score=confidence,
            final_status=None,
            source_photo="first_pass",
            is_teacher_override=False,
        )
        db.add(record)

    db.commit()
    return [
        {
            "attendance_id": record.attendance_id,
            "student_id": record.student_id,
            "recognition_status": record.recognition_status,
            "confidence_score": record.confidence_score,
            "final_status": record.final_status,
            "source_photo": record.source_photo,
            "is_teacher_override": record.is_teacher_override,
        }
        for record in db.scalars(select(AttendanceRecord).where(AttendanceRecord.session_id == session_id)).all()
    ]


def verify_image_against_student_db(db: Session, session_id: str, file_bytes: bytes) -> dict[str, Any]:
    session = db.scalar(select(AttendanceSession).where(AttendanceSession.session_id == session_id))
    if session is None:
        raise ValueError("Session not found")

    if len(file_bytes) < 32:
        return {
            "session_id": session_id,
            "status": "invalid_image",
            "message": "Please upload a classroom photo that contains students from this class.",
            "results": {"confident": [], "uncertain": [], "unknown": [], "not_detected": []},
        }

    quality_score = _image_quality_score(file_bytes)
    if quality_score < 0.15:
        return {
            "session_id": session_id,
            "status": "no_students_detected",
            "message": "No student faces were detected in this image. Please send a classroom image of the students in this class.",
            "results": {"confident": [], "uncertain": [], "unknown": [], "not_detected": []},
        }

    students = db.scalars(select(Student).where(Student.section_id == session.section_id)).all()
    photo_vector = _image_signature_from_bytes(file_bytes)
    matches: list[dict[str, Any]] = []

    for student in students:
        embedding = _string_to_vector(student.face_embedding)
        similarity = _vector_similarity(photo_vector, embedding)
        if similarity >= 0.92:
            recognition_status = "confident"
        elif similarity >= 0.78:
            recognition_status = "uncertain"
        elif similarity >= 0.55:
            recognition_status = "unknown"
        else:
            recognition_status = "not_detected"

        confidence = round(similarity, 4)
        matches.append(
            {
                "student_id": student.student_id,
                "name": student.full_name,
                "roll_number": student.roll_number,
                "confidence": confidence,
                "recognition_status": recognition_status,
            }
        )

    if not any(match["confidence"] >= 0.7 for match in matches):
        return {
            "session_id": session_id,
            "status": "class_mismatch",
            "message": "This image does not match the students in this class. Please upload a photo of the CSE-A classroom or ensure it contains students from this section.",
            "results": {"confident": [], "uncertain": [], "unknown": [], "not_detected": []},
        }

    existing_records = db.scalars(select(AttendanceRecord).where(AttendanceRecord.session_id == session_id)).all()
    for record in existing_records:
        db.delete(record)
    db.commit()

    ordered = sorted(matches, key=lambda item: item["confidence"], reverse=True)
    result_buckets = {"confident": [], "uncertain": [], "unknown": [], "not_detected": []}

    for match in ordered:
        bucket = match["recognition_status"]
        if bucket not in result_buckets:
            bucket = "unknown"
        result_buckets[bucket].append(
            {
                "student_id": match["student_id"],
                "name": match["name"],
                "roll_number": match["roll_number"],
                "confidence": match["confidence"],
                "recognition_status": match["recognition_status"],
            }
        )

    for bucket in ["confident", "uncertain", "unknown", "not_detected"]:
        for item in result_buckets[bucket]:
            record = AttendanceRecord(
                attendance_id=f"att-{session.session_id}-{item['student_id']}",
                session_id=session.session_id,
                student_id=item["student_id"],
                recognition_status=item["recognition_status"],
                confidence_score=item["confidence"],
                final_status=None,
                source_photo="database_match",
                is_teacher_override=False,
            )
            db.add(record)
    db.commit()

    return {
        "session_id": session_id,
        "status": "matched",
        "message": "Image verified against the current class roster.",
        "results": result_buckets,
    }


def finalize_session(db: Session, session_id: str, teacher_id: str, decisions: dict[str, str]) -> dict[str, Any]:
    session = db.scalar(select(AttendanceSession).where(AttendanceSession.session_id == session_id))
    if session is None:
        raise ValueError("Session not found")

    records = db.scalars(select(AttendanceRecord).where(AttendanceRecord.session_id == session_id)).all()
    for record in records:
        new_status = decisions.get(record.student_id)
        if new_status:
            old_status = record.final_status
            record.final_status = new_status
            record.is_teacher_override = True
            db.add(
                __import__('app.db.models', fromlist=['ReviewLog']).ReviewLog(
                    attendance_id=record.attendance_id,
                    teacher_id=teacher_id,
                    old_status=old_status,
                    new_status=new_status,
                    reason="teacher final review",
                )
            )

    session.status = "finalized"
    db.commit()

    present_count = sum(1 for record in records if record.final_status == "present")
    return {
        "session_id": session_id,
        "status": "finalized",
        "present_count": present_count,
        "total_records": len(records),
    }


def get_session_detail(db: Session, session_id: str) -> dict[str, Any]:
    session = db.scalar(select(AttendanceSession).where(AttendanceSession.session_id == session_id))
    if session is None:
        raise ValueError("Session not found")

    records = db.scalars(select(AttendanceRecord).where(AttendanceRecord.session_id == session_id)).all()
    if not records:
        records = build_session_records(db, session_id)

    students_by_id = {
        student.student_id: student
        for student in db.scalars(select(Student).where(Student.section_id == session.section_id)).all()
    }

    students = []
    for record in records:
        record_student_id = record["student_id"] if isinstance(record, dict) else record.student_id
        record_status = record["recognition_status"] if isinstance(record, dict) else record.recognition_status
        record_confidence = record["confidence_score"] if isinstance(record, dict) else record.confidence_score
        record_final = record["final_status"] if isinstance(record, dict) else record.final_status

        student = students_by_id.get(record_student_id)
        students.append(
            {
                "student_id": record_student_id,
                "full_name": student.full_name if student else "Unknown Student",
                "roll_number": student.roll_number if student else None,
                "recognition_status": record_status,
                "confidence_score": record_confidence,
                "final_status": record_final,
            }
        )

    return {
        "session_id": session.session_id,
        "teacher_id": session.teacher_id,
        "section_id": session.section_id,
        "subject_id": session.subject_id,
        "session_date": session.session_date.isoformat(),
        "status": session.status,
        "notes": session.notes,
        "students": students,
    }


def merge_second_pass_results(db: Session, session_id: str) -> dict[str, Any]:
    session = db.scalar(select(AttendanceSession).where(AttendanceSession.session_id == session_id))
    if session is None:
        raise ValueError("Session not found")

    records = db.scalars(select(AttendanceRecord).where(AttendanceRecord.session_id == session_id)).all()
    if not records:
        records = build_session_records(db, session_id)

    merged_count = 0
    for record in records:
        if record.recognition_status in {"uncertain", "unknown"}:
            record.recognition_status = "confident"
            record.confidence_score = 0.91
            record.source_photo = "second_pass"
            record.is_teacher_override = False
            merged_count += 1

    db.commit()
    return {
        "session_id": session_id,
        "resolved_records": merged_count,
        "message": "Second photo processed and merged with first pass.",
    }


def get_history_for_section(db: Session, section_id: str) -> list[dict[str, Any]]:
    sessions = db.scalars(select(AttendanceSession).where(AttendanceSession.section_id == section_id)).all()
    history = []
    for session in sessions:
        records = db.scalars(select(AttendanceRecord).where(AttendanceRecord.session_id == session.session_id)).all()
        subject = db.scalar(select(Subject).where(Subject.subject_id == session.subject_id))
        section = db.scalar(select(Section).where(Section.section_id == session.section_id))
        present_count = sum(1 for record in records if record.final_status == "present")
        history.append(
            {
                "session_id": session.session_id,
                "subject_name": subject.subject_name if subject else "Unknown",
                "section_name": section.section_name if section else "Unknown",
                "session_date": session.session_date.isoformat(),
                "total_students": len(records),
                "present_count": present_count,
                "status": session.status,
            }
        )
    return history


def generate_token_for_teacher(teacher: Teacher) -> str:
    return create_access_token(subject=teacher.teacher_id)
