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
        "stats": {
            "present": 18,
            "review": 3,
            "pending": 1,
        },
        "recent_sessions": [
            {
                "session_id": s.session_id,
                "subject_id": s.subject_id,
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
