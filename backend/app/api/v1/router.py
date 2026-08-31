from fastapi import APIRouter
from app.api.v1 import auth, classes, students, enrollment, attendance, history, subjects

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(classes.router)
api_router.include_router(subjects.router)
api_router.include_router(students.router)
api_router.include_router(enrollment.router)
api_router.include_router(attendance.router)
api_router.include_router(history.router)
