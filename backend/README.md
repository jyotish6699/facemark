# FaceMark Backend API

AI-Powered Classroom Attendance System backend built with **FastAPI**, **SQLAlchemy**, and **Python**.

---

## Features

- **JWT Authentication & RBAC**: Secure email/password login with HTTP-only cookies and Bearer tokens for `ADMIN` and `TEACHER` roles.
- **Roster-Scoped Recognition**: Limits face matching candidates strictly to students enrolled in the active session's class.
- **Biometric Face Enrollment**: Stores 512-dimensional normalized embeddings for enrolled students.
- **Multi-Face Detection & Cosine Similarity Matcher**: Evaluates classroom crowd photos and classifies into `Confident`, `Review`, `Unknown`, and `Not Detected`.
- **Deterministic Multi-Photo Merge Engine**: Merges evidence across multiple photos in a single session without duplicate counts.
- **Teacher Review & Transactional Finalization**: Allows teachers to override attendance decisions and freezes the session.
- **Audit Logging**: Logs changes and finalization events.
- **Automatic Seeding**: Seeds teachers, classes, subjects, students, and past attendance sessions on first launch.

---

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Backend
```bash
python run.py
```
- **API Documentation (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)
- **Direct Web App**: [http://localhost:8000/app](http://localhost:8000/app)

---

## Seed Accounts

| Role | Email | Password |
|---|---|---|
| **Teacher** | `teacher@facemark.demo` | `demo123` |
| **Teacher** | `sanjay@facemark.demo` | `demo123` |
| **Admin** | `admin@facemark.demo` | `admin123` |

---

## Running Automated Tests

```bash
pytest tests/ -v
```
