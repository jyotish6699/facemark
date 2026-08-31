import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum
from app.database import Base

class SessionStatus(str, enum.Enum):
    OPEN = "OPEN"
    PROCESSING = "PROCESSING"
    REVIEW = "REVIEW"
    FINALIZED = "FINALIZED"
    CANCELLED = "CANCELLED"

class AttendanceSession(Base):
    __tablename__ = "attendance_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    class_id = Column(String(36), ForeignKey("classes.id", ondelete="CASCADE"), nullable=False)
    subject_id = Column(String(36), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    teacher_id = Column(String(36), ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False)
    session_date = Column(String(10), nullable=False) # "YYYY-MM-DD"
    status = Column(SQLEnum(SessionStatus), default=SessionStatus.OPEN, nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    finalized_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    classroom = relationship("Classroom", back_populates="attendance_sessions")
    subject = relationship("Subject", back_populates="attendance_sessions")
    teacher = relationship("Teacher", back_populates="attendance_sessions")
    photos = relationship("AttendancePhoto", back_populates="session", cascade="all, delete-orphan", order_by="AttendancePhoto.photo_order")
    recognition_results = relationship("RecognitionResult", back_populates="session", cascade="all, delete-orphan")
    attendance_records = relationship("AttendanceRecord", back_populates="session", cascade="all, delete-orphan")

class AttendancePhoto(Base):
    __tablename__ = "attendance_photos"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("attendance_sessions.id", ondelete="CASCADE"), nullable=False)
    storage_key = Column(String(512), nullable=False)
    original_filename = Column(String(255), nullable=True)
    mime_type = Column(String(64), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_hash = Column(String(64), nullable=True) # SHA-256 hash for duplicate check
    photo_order = Column(Integer, default=1, nullable=False) # 1 = initial, 2 = resolution
    processing_status = Column(String(32), default="COMPLETED", nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    session = relationship("AttendanceSession", back_populates="photos")
    detected_faces = relationship("DetectedFace", back_populates="photo", cascade="all, delete-orphan")
    recognition_results = relationship("RecognitionResult", back_populates="photo", cascade="all, delete-orphan")
