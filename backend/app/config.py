import os
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    BASE_DIR: Path = BASE_DIR
    PROJECT_NAME: str = "FaceMark API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Security & JWT
    SECRET_KEY: str = "facemark-super-secret-jwt-key-2026-production-ready"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
   # Database (SQLite default for effortless local run, PostgreSQL / Supabase supported)
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'facemark.db'}"
    # Storage
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    ENROLLMENT_DIR: Path = BASE_DIR / "uploads" / "enrollments"
    ATTENDANCE_DIR: Path = BASE_DIR / "uploads" / "attendance"
    MAX_UPLOAD_SIZE_MB: int = 15
    ALLOWED_IMAGE_TYPES: list[str] = ["image/jpeg", "image/png", "image/jpg", "image/webp"]
    
    # Recognition Thresholds (Calibrated cosine similarity)
    SIMILARITY_THRESHOLD_CONFIDENT: float = 0.55
    SIMILARITY_THRESHOLD_REVIEW: float = 0.42
    MIN_FACE_QUALITY: float = 0.35

    # InsightFace / ArcFace
    INSIGHTFACE_MODEL: str = "buffalo_l"
    INSIGHTFACE_PROVIDER: str = "CPU"  # Set CUDA when NVIDIA CUDA is available
    
    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
        "*"
    ]

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()

# Ensure upload directories exist
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.ENROLLMENT_DIR.mkdir(parents=True, exist_ok=True)
settings.ATTENDANCE_DIR.mkdir(parents=True, exist_ok=True)
