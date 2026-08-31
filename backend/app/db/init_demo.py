from sqlalchemy import select

from app.core.config import get_settings
from app.db.base import Base
from app.db.models import Teacher
from app.db.session import SessionLocal, engine
from app.services.demo_service import seed_demo_data


def initialize_demo_database() -> None:
    settings = get_settings()
    print(f"Initializing demo database for: {settings.database_url}")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        existing = db.scalar(select(Teacher).limit(1))
        if existing is None:
            seed_demo_data(db)
            print("Demo data inserted.")
        else:
            print("Demo data already present.")
    finally:
        db.close()


if __name__ == "__main__":
    initialize_demo_database()
