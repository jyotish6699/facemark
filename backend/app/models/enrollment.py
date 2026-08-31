import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Text, JSON
from app.config import settings

try:
    from pgvector.sqlalchemy import VECTOR
except ImportError:
    VECTOR = None

EmbeddingVectorType = VECTOR(512) if VECTOR and settings.DATABASE_URL.startswith("postgresql") else JSON
from sqlalchemy.orm import relationship
from app.database import Base

class FaceEnrollment(Base):
    __tablename__ = "face_enrollments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String(36), ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    image_storage_key = Column(String(512), nullable=False)
    quality_score = Column(Float, default=1.0, nullable=False)
    status = Column(String(32), default="ACTIVE", nullable=False) # ACTIVE, REVOKED, REPLACED
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    student = relationship("Student", back_populates="face_enrollments")
    embeddings = relationship("FaceEmbedding", back_populates="enrollment", cascade="all, delete-orphan")

class FaceEmbedding(Base):
    __tablename__ = "face_embeddings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    enrollment_id = Column(String(36), ForeignKey("face_enrollments.id", ondelete="CASCADE"), nullable=False)
    embedding_json = Column(Text, nullable=False) # Backward-compatible JSON copy
    embedding_vector = Column(EmbeddingVectorType, nullable=True, index=False)
    dimension = Column(String(16), default="512", nullable=False)
    model_name = Column(String(64), default="ArcFace-InsightFace", nullable=False)
    model_version = Column(String(32), default="v1.0", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    enrollment = relationship("FaceEnrollment", back_populates="embeddings")
