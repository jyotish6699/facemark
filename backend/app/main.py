from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.attendance import router as attendance_router
from app.api.routes.auth import router as auth_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.sections import router as sections_router
from app.db.base import Base
from app.db.session import engine

app = FastAPI(title="FaceMark API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(sections_router)
app.include_router(attendance_router)


@app.on_event("startup")
def startup_event() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
