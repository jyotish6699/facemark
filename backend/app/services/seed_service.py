from sqlalchemy.orm import Session

from app.models.user import User, UserRole, UserStatus
from app.models.teacher import Teacher, TeacherClass
from app.models.classroom import Classroom, Subject
from app.models.student import Student, ClassMembership
from app.models.enrollment import FaceEnrollment, FaceEmbedding
from app.models.session import AttendanceSession
from app.models.attendance import AttendanceRecord, DetectedFace, RecognitionResult
from app.models.audit import AuditLog
from app.services.auth_service import get_password_hash

def seed_database(db: Session):
    """
    Initializes clean system accounts (Teacher and Admin).
    Does NOT seed dummy students, dummy sessions, or dummy records,
    allowing users to enter their own real students, registration numbers, and subjects.
    """
    # Create Admin account if not present
    if not db.query(User).filter(User.email == "admin@facemark.demo").first():
        admin_user = User(
            email="admin@facemark.demo",
            password_hash=get_password_hash("admin123"),
            full_name="System Administrator",
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE
        )
        db.add(admin_user)

    # Create Teacher account if not present
    teacher_user = db.query(User).filter(User.email == "teacher@facemark.demo").first()
    if not teacher_user:
        teacher_user = User(
            email="teacher@facemark.demo",
            password_hash=get_password_hash("demo123"),
            full_name="Teacher",
            role=UserRole.TEACHER,
            status=UserStatus.ACTIVE
        )
        db.add(teacher_user)
        db.flush()

        teacher_profile = Teacher(
            user_id=teacher_user.id, 
            employee_number="TCH-001", 
            department="Academic Department"
        )
        db.add(teacher_profile)

    db.commit()
    print("[+] Clean database ready for custom data entry.")

def reset_all_dummy_data(db: Session):
    """Wipes all student records, memberships, face enrollments, attendance sessions and records."""
    db.query(AttendanceRecord).delete()
    db.query(RecognitionResult).delete()
    db.query(DetectedFace).delete()
    db.query(AttendanceSession).delete()
    db.query(FaceEmbedding).delete()
    db.query(FaceEnrollment).delete()
    db.query(ClassMembership).delete()
    db.query(Student).delete()
    db.query(TeacherClass).delete()
    db.query(Classroom).delete()
    db.query(Subject).delete()
    db.commit()
    print("[+] All dummy data successfully wiped.")
