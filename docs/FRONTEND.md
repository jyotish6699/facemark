# FaceMark Frontend Guide

This frontend is a demo-focused UI for the FaceMark attendance workflow. It runs on a local browser without a database or backend API and is designed to simulate the full teacher workflow for a hackathon presentation.

## Local run

From the repository root:

```bash
cd frontend
python3 -m http.server 8000
```

Then open:

```text
http://localhost:8000
```

## Included screens

- Login screen
- Teacher dashboard
- Class selection
- Attendance setup
- Photo upload
- Recognition review
- Second photo workflow
- Final review and attendance finalize
- Attendance history

## User flow

1. Login with any valid-looking email/password pair.
2. Choose a class.
3. Start an attendance session.
4. Upload a classroom photo.
5. Review AI results (confident, uncertain, unknown, not detected).
6. Upload a second photo to resolve uncertain or unknown faces.
7. Review final student attendance.
8. Finalize the session and view history.

## Notes

- This is a static mock frontend for demo purposes only.
- It demonstrates the UI and complete workflow without a live backend.
- Real recognition and persistence are implemented in the backend phase.

## Files

- `frontend/index.html` — app shell
- `frontend/styles.css` — styling
- `frontend/app.js` — UI logic and demo workflow
