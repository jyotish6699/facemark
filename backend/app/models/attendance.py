import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, UniqueConstraint, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship
import enum
from app.database import Base

class RecognitionStatus(str, enum.Enum):
    CONFIDENT_MATCH = "CONFIDENT_MATCH"
    UNCERTAIN = "UNCERTAIN"
    UNKNOWN = "UNKNOWN"
    NOT_DETECTED = "NOT_DETECTED"

class FinalAttendanceStatus(str, enum.Enum):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    REVIEW = "REVIEW"

class AttendanceSource(str, enum.Enum):
    AI = "AI"
    TEACHER = "TEACHER"

class DetectedFace(Base):
    __tablename__ = "detected_faces"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    photo_id = Column(String(36), ForeignKey("attendance_photos.id", ondelete="CASCADE"), nullable=False)
    face_index = Column(Integer, nullable=False)
    bounding_box_json = Column(Text, nullable=True) # { "x": 0, "y": 0, "w": 0, "h": 0 }
    quality_score = Column(Float, default=1.0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    photo = relationship("AttendancePhoto", back_populates="detected_faces")
    recognition_results = relationship("RecognitionResult", back_populates="detected_face", cascade="all, delete-orphan")

class RecognitionResult(Base):
    __tablename__ = "recognition_results"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("attendance_sessions.id", ondelete="CASCADE"), nullable=False)
    photo_id = Column(String(36), ForeignKey("attendance_photos.id", ondelete="CASCADE"), nullable=True)
    detected_face_id = Column(String(36), ForeignKey("detected_faces.id", ondelete="SET NULL"), nullable=True)
    candidate_student_id = Column(String(36), ForeignKey("students.id", ondelete="SET NULL"), nullable=True)
    confidence_score = Column(Float, nullable=True)
    recognition_status = Column(SQLEnum(RecognitionStatus), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    session = relationship("AttendanceSession", back_populates="recognition_results")
    photo = relationship("AttendancePhoto", back_populates="recognition_results")
    detected_face = relationship("DetectedFace", back_populates="recognition_results")
    candidate_student = relationship("Student", back_populates="recognition_results")

class AttendanceRecord(Base):
    __tablename__ = "attendance_records"
    __table_args__ = (
        UniqueConstraint("session_id", "student_id", name="uq_session_student_attendance"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("attendance_sessions.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(String(36), ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    final_status = Column(SQLEnum(FinalAttendanceStatus), default=FinalAttendanceStatus.PRESENT, nullable=False)
    source = Column(SQLEnum(AttendanceSource), default=AttendanceSource.AI, nullable=False)
    reviewed_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    session = relationship("AttendanceSession", back_populates="attendance_records")
    student = relationship("Student", back_populates="attendance_records")
