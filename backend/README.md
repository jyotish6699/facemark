# FaceMark Backend

This backend is a demo-focused FastAPI application for the FaceMark classroom attendance workflow.

## Quick start

From the repository root, run:

```bash
./scripts/run-database.sh
./scripts/run-backend.sh
```

The script automatically:
- creates `backend/.env` from `.env.example` (if missing)
- creates `backend/.venv` (if missing)
- installs backend dependencies (if missing)
- starts FastAPI at `http://localhost:8001`

## Default behavior

For the hackathon demo, PostgreSQL is the default database. The app uses the `DATABASE_URL` value in `backend/.env`.

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
