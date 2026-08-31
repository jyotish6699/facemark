import os
import sys
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.config import settings
from app.database import Base, get_db
from app.main import app as fastapi_app
from app.services.seed_service import seed_database
import app.models # Register all models

# Use StaticPool with in-memory SQLite so all connections share the same memory database
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture()
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    fastapi_app.dependency_overrides[get_db] = override_get_db
    with TestClient(fastapi_app) as test_client:
        yield test_client
    fastapi_app.dependency_overrides.clear()

@pytest.fixture()
def teacher_auth_headers(client):
    """Logs in as teacher and returns Bearer auth header."""
    resp = client.post("/api/v1/auth/login", json={
        "email": "teacher@facemark.demo",
        "password": "demo123"
    })
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture()
def admin_auth_headers(client):
    """Logs in as admin and returns Bearer auth header."""
    resp = client.post("/api/v1/auth/login", json={
        "email": "admin@facemark.demo",
        "password": "admin123"
    })
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
