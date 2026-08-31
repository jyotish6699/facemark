# FaceMark Backend Architecture

## 1. Purpose

This document defines the final backend architecture for the FaceMark hackathon demo.

The backend must follow the real product flow already decided:

- teacher login
- class/section selection
- subject selection
- attendance session creation
- classroom photo upload
- recognition and review workflow
- second photo merge
- finalization
- history view

The backend is built for a realistic demo using fake university data, not production-scale complexity.

---

## 2. Technology stack

- Python 3.11+
- FastAPI
- PostgreSQL
- pgvector
- SQLAlchemy (or asyncpg + raw SQL if preferred)
- Pydantic
- JWT authentication
- Supabase Storage for uploaded classroom images
- pytest for tests

---

## 3. High-level architecture

```text
Browser / Frontend
        |
        v
FastAPI Backend
  - Auth API
  - Dashboard API
  - Attendance API
  - Section / Subject API
  - Recognition Service
  - Upload / Storage Service
        |
        +---------------------------+
        |                           |
        v                           v
PostgreSQL (facemark_demo)   Supabase Storage
  - teachers                  - first-pass photos
  - sections                  - second-pass photos
  - subjects                  - enrolled images
  - students
  - attendance_sessions
  - attendance_records
  - review_logs
  - uploaded_images
        |
        v
Recognition pipeline
  - face detection
  - feature extraction
  - cosine similarity matching
  - candidate classification
```

---

## 4. Final backend folder structure

```text
backend/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── auth.py
│   │       ├── dashboard.py
│   │       ├── sections.py
│   │       └── attendance.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── security.py
│   │   └── logging.py
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── session.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── teacher.py
│   │   │   ├── section.py
│   │   │   ├── subject.py
│   │   │   ├── student.py
│   │   │   ├── attendance_session.py
│   │   │   ├── attendance_record.py
│   │   │   ├── review_log.py
│   │   │   └── uploaded_image.py
│   │   ├── repositories/
│   │   │   ├── __init__.py
│   │   │   ├── teacher_repo.py
│   │   │   ├── section_repo.py
│   │   │   ├── subject_repo.py
│   │   │   ├── student_repo.py
│   │   │   ├── attendance_repo.py
│   │   │   └── dashboard_repo.py
│   │   └── seed/
│   │       ├── __init__.py
│   │       ├── fake_teachers.py
│   │       ├── fake_sections.py
│   │       ├── fake_subjects.py
│   │       ├── fake_students.py
│   │       └── seed_demo_data.py
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── teacher.py
│   │   ├── section.py
│   │   ├── subject.py
│   │   ├── student.py
│   │   ├── attendance.py
│   │   └── common.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── dashboard_service.py
│   │   ├── attendance_service.py
│   │   ├── recognition_service.py
│   │   ├── storage_service.py
│   │   └── merge_service.py
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── id_utils.py
│   │   ├── fake_embeddings.py
│   │   ├── file_utils.py
│   │   └── response_utils.py
│   │
│   └── main.py
│
├── tests/
│   ├── README.md
│   ├── unit/
│   │   ├── test_auth_service.py
│   │   ├── test_recognition_service.py
│   │   ├── test_merge_service.py
│   │   └── test_attendance_logic.py
│   └── integration/
│       ├── test_login_flow.py
│       ├── test_dashboard_flow.py
│       ├── test_attendance_session_flow.py
│       ├── test_second_photo_merge.py
│       └── test_finalization_flow.py
│
├── requirements.txt
├── .env.example
├── README.md
└── alembic.ini
```

---

## 5. API layer responsibilities

### auth routes

- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/me`

Responsibilities:

- validate email/password
- verify teacher in DB
- create JWT
- return safe teacher info

### dashboard routes

- `GET /api/dashboard/teacher/{teacher_id}`

Responsibilities:

- fetch section details
- fetch subject list for section
- return stats and recent sessions
- return attendance overview for teacher dashboard

### section routes

- `GET /api/sections/{section_id}/subjects`

Responsibilities:

- return all course subjects for a section
- support subject selection UI

### attendance routes

- `POST /api/attendance/sessions`
- `POST /api/attendance/sessions/{session_id}/upload`
- `POST /api/attendance/sessions/{session_id}/recognize`
- `POST /api/attendance/sessions/{session_id}/resolve`
- `POST /api/attendance/sessions/{session_id}/finalize`
- `GET /api/attendance/sessions/{session_id}`
- `GET /api/attendance/history`

Responsibilities:

- start sessions
- store uploaded images
- trigger recognition logic
- store attendance rows
- merge second-pass results
- finalize session
- return history and attendance details

---

## 6. Database responsibilities

The database will hold all state for:

- user identity and auth data
- class and subject metadata
- student roster
- attendance sessions
- attendance output rows
- final teacher review changes
- uploaded image metadata

The DB is not responsible for the recognition model itself. It only stores the output data and the embeddings needed for matching.

---

## 7. Service responsibilities

### auth_service.py

- verify credentials
- hash/compare password
- issue JWT
- decode JWT

### dashboard_service.py

- get teacher profile
- get section summary
- get subject list
- assemble dashboard payload

### attendance_service.py

- create attendance session
- add attendance rows
- finalize attendance
- fetch attendance history

### recognition_service.py

- detect faces
- compute embeddings
- compare embeddings against student vectors
- assign `confident`, `uncertain`, `unknown`, or `not_detected`
- return classification result payload

### merge_service.py

- merge first and second recognition passes
- update uncertain/unknown entries only
- prevent duplicate student counts

### storage_service.py

- upload classroom image to Supabase Storage
- get public/download URL
- store metadata in DB

---

## 8. Demo data strategy

Use fake data for:

- teacher login
- section roster and subjects
- enrolled students
- fake face embeddings
- sample attendance sessions

This is essential for the hackathon flow.

The backend should not depend on an external real university system.

---

## 9. Recognition logic design

For the demo, recognition can be simplified but should still feel realistic.

Implementation approach:

- use a fake vector or generated demo embedding per student
- compare uploaded face vectors to all enrolled student embeddings
- compute cosine similarity
- threshold values:
  - high confidence => `confident`
  - medium => `uncertain`
  - no match => `unknown`

The recognition service should always return structured values that the frontend can display cleanly.

---

## 10. Security plan

- store password hashes, not plaintext
- use JWT tokens for teacher auth
- use HTTP-only cookies or Authorization header
- no secrets in source code
- keep demo credentials in `.env` only

---

## 11. Test strategy

The backend must include:

- unit tests for recognition logic and auth logic
- integration tests for login, session creation, attendance flow, and finalization

We are not aiming for massive test coverage. The goal is to validate the exact hackathon demo flow.

---

## 12. Implementation order

1. Create project structure
2. Configure FastAPI app and environment
3. Set up PostgreSQL connection and models
4. Seed fake data
5. Build auth endpoints
6. Build dashboard endpoints
7. Build attendance session endpoints
8. Build recognition service
9. Build second-pass merge logic
10. Finalize and validate with tests

---

## 13. Final product notes

This backend is intentionally practical and demo-focused.

The design is optimized for:

- realistic flow
- lower implementation complexity
- easy understanding in a hackathon demo
- quick backend + database delivery

It is not designed to be a large enterprise backend.

---

## 14. Final principle

Keep the backend simple, testable, and faithful to the product workflow already decided.
