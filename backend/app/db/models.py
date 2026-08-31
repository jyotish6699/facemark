import uuid

from sqlalchemy import Boolean, Date, Double, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Teacher(Base):
    __tablename__ = "teachers"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    teacher_id: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, default="teacher")
    assigned_section_id: Mapped[str | None] = mapped_column(String, nullable=True)


class Section(Base):
    __tablename__ = "sections"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    section_id: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    section_name: Mapped[str] = mapped_column(String, nullable=False)
    department: Mapped[str] = mapped_column(String, nullable=False)
    semester: Mapped[str] = mapped_column(String, nullable=False)
    academic_year: Mapped[str] = mapped_column(String, nullable=False)


class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    subject_id: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    subject_name: Mapped[str] = mapped_column(String, nullable=False)
    schedule_day: Mapped[str | None] = mapped_column(String, nullable=True)
    room: Mapped[str | None] = mapped_column(String, nullable=True)


class SectionSubject(Base):
    __tablename__ = "section_subjects"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    section_id: Mapped[str] = mapped_column(String, ForeignKey("sections.section_id"), nullable=False)
    subject_id: Mapped[str] = mapped_column(String, ForeignKey("subjects.subject_id"), nullable=False)


class Student(Base):
    __tablename__ = "students"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    roll_number: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    email: Mapped[str | None] = mapped_column(String, unique=True, nullable=True)
    section_id: Mapped[str] = mapped_column(String, ForeignKey("sections.section_id"), nullable=False)
    status: Mapped[str] = mapped_column(String, default="active")
    enrollment_image_url: Mapped[str | None] = mapped_column(String, nullable=True)
    face_embedding: Mapped[str | None] = mapped_column(Text, nullable=True)


class AttendanceSession(Base):
    __tablename__ = "attendance_sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    teacher_id: Mapped[str] = mapped_column(String, ForeignKey("teachers.teacher_id"), nullable=False)
    section_id: Mapped[str] = mapped_column(String, ForeignKey("sections.section_id"), nullable=False)
    subject_id: Mapped[str] = mapped_column(String, ForeignKey("subjects.subject_id"), nullable=False)
    session_date: Mapped[str] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String, default="in_progress")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    attendance_id: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    session_id: Mapped[str] = mapped_column(String, ForeignKey("attendance_sessions.session_id"), nullable=False)
    student_id: Mapped[str] = mapped_column(String, ForeignKey("students.student_id"), nullable=False)
    recognition_status: Mapped[str] = mapped_column(String, nullable=False)
    confidence_score: Mapped[float | None] = mapped_column(Double, nullable=True)
    final_status: Mapped[str | None] = mapped_column(String, nullable=True)
    source_photo: Mapped[str | None] = mapped_column(String, nullable=True)
    is_teacher_override: Mapped[bool] = mapped_column(Boolean, default=False)


class ReviewLog(Base):
    __tablename__ = "review_logs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    attendance_id: Mapped[str] = mapped_column(String, nullable=False)
    teacher_id: Mapped[str] = mapped_column(String, nullable=False)
    old_status: Mapped[str | None] = mapped_column(String, nullable=True)
    new_status: Mapped[str | None] = mapped_column(String, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class UploadedImage(Base):
    __tablename__ = "uploaded_images"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    image_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    session_id: Mapped[str] = mapped_column(String, ForeignKey("attendance_sessions.session_id"), nullable=False)
    image_type: Mapped[str] = mapped_column(String, nullable=False)
    storage_url: Mapped[str] = mapped_column(String, nullable=False)
    uploaded_by: Mapped[str] = mapped_column(String, nullable=False)
