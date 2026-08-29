# FaceMark Backend

This backend is a demo-focused FastAPI application for the FaceMark classroom attendance workflow.

## Quick start

1. Create a virtual environment
2. Install dependencies
3. Copy `.env.example` to `.env`
4. Run the app

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

## Default behavior

For the hackathon demo, PostgreSQL is the default database. The app is configured to use the PostgreSQL connection string in `.env`.

If no `DATABASE_URL` is configured, it falls back to a local SQLite database only for quick local testing.

## Demo login

Teacher login for the fake demo profile:

- email: `ayesha.khan@facemark.local`
- password: `Teacher@123`

## Routes

- `POST /api/auth/login`
- `GET /api/dashboard/teacher/{teacher_id}`
- `GET /api/sections/{section_id}/subjects`
- `POST /api/attendance/sessions`
- `POST /api/attendance/sessions/{session_id}/upload`
- `POST /api/attendance/sessions/{session_id}/recognize`
- `POST /api/attendance/sessions/{session_id}/resolve`
- `POST /api/attendance/sessions/{session_id}/finalize`
- `GET /api/attendance/history`
