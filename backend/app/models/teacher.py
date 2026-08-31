import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Teacher(Base):
    __tablename__ = "teachers"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    employee_number = Column(String(64), unique=True, index=True, nullable=True)
    department = Column(String(128), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="teacher_profile")
    teacher_classes = relationship("TeacherClass", back_populates="teacher", cascade="all, delete-orphan")
    attendance_sessions = relationship("AttendanceSession", back_populates="teacher")

class TeacherClass(Base):
    __tablename__ = "teacher_classes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    teacher_id = Column(String(36), ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False)
    class_id = Column(String(36), ForeignKey("classes.id", ondelete="CASCADE"), nullable=False)
    assigned_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(String(32), default="ACTIVE", nullable=False)

    # Relationships
    teacher = relationship("Teacher", back_populates="teacher_classes")
    classroom = relationship("Classroom", back_populates="teacher_assignments")
