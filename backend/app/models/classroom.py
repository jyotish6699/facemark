import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.orm import relationship
from app.database import Base

class Classroom(Base):
    __tablename__ = "classes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(128), unique=True, index=True, nullable=False) # e.g. "CSE-A"
    semester = Column(Integer, nullable=True, default=5)
    academic_year = Column(String(32), nullable=True, default="2026-2027")
    status = Column(String(32), default="ACTIVE", nullable=False)
    subject = Column(String(128), default="General", nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    teacher_assignments = relationship("TeacherClass", back_populates="classroom", cascade="all, delete-orphan")
    memberships = relationship("ClassMembership", back_populates="classroom", cascade="all, delete-orphan")
    attendance_sessions = relationship("AttendanceSession", back_populates="classroom")

class Subject(Base):
    __tablename__ = "subjects"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(128), index=True, nullable=False) # e.g. "Operating Systems"
    code = Column(String(32), unique=True, index=True, nullable=False) # e.g. "CS501"
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    attendance_sessions = relationship("AttendanceSession", back_populates="subject")
