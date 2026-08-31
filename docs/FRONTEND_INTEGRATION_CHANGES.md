# FaceMark Frontend Integration Changes

## 1. Purpose

This file defines the frontend changes needed to connect the existing HTML/CSS/JS demo to the real backend and database workflow.

The frontend is already working as a demo. We now need to connect it to the backend without changing the overall flow.

---

## 2. What frontend already does

The current frontend already includes:

- login screen
- teacher dashboard
- class/section selection
- subject view
- attendance session start
- upload flow
- recognition review screen
- second photo workflow
- final review and finalize screen
- attendance history

This is the correct product flow for the demo and should remain in place.

---

## 3. What needs to change

The frontend must be updated from static demo behavior to real API-driven behavior.

### 3.1 Replace demo login with real API call

Current behavior:

- demo validation with any email/password entry

New behavior:

- send `POST /api/auth/login`
- body includes email and password
- backend validates against PostgreSQL teacher data
- frontend stores JWT token or cookie
- redirect to dashboard on success

### 3.2 Replace mock dashboard with live data

Current behavior:

- static dashboard cards and sample session list

New behavior:

- call `GET /api/dashboard/teacher/{teacher_id}`
- render assigned section
- render subject cards
- render session summary and attendance stats

### 3.3 Replace static subject selection with real list

Current behavior:

- manual selection from static options

New behavior:

- fetch `GET /api/sections/{section_id}/subjects`
- display subject cards from backend
- allow teacher to choose subject

### 3.4 Replace demo session creation with backend session creation

Current behavior:

- local UI-only session creation

New behavior:

- call `POST /api/attendance/sessions`
- body includes:
  - teacher_id
  - section_id
  - subject_id
  - session_date
  - notes (optional)
- receive session id

### 3.5 Replace photo upload placeholder with real upload API

Current behavior:

- upload is simulated in frontend

New behavior:

- use actual file input
- send file to backend via multipart upload
- `POST /api/attendance/sessions/{session_id}/upload`
- store image metadata in DB and storage

### 3.6 Replace mock recognition result generation with live recognition API

Current behavior:

- static recognition categories and fake values

New behavior:

- call `POST /api/attendance/sessions/{session_id}/recognize`
- render real output values:
  - confident matches
  - uncertain matches
  - unknown faces
  - not detected students

### 3.7 Replace second-photo placeholder with real merge API

Current behavior:

- second photo is a mock screen

New behavior:

- use `POST /api/attendance/sessions/{session_id}/resolve`
- upload second image
- backend merges with first-pass result
- frontend updates the review table without duplication

### 3.8 Replace final review mock table with real attendance records

Current behavior:

- teacher manually changes model values in a demo table

New behavior:

- fetch actual attendance records for the session
- show each student row with:
  - name
  - roll number
  - recognition status
  - confidence
  - dropdown with final_status
- teacher selects final values and finalizes

### 3.9 Replace local history with API-backed history

Current behavior:

- static session history list

New behavior:

- call `GET /api/attendance/history?section_id={...}`
- show finalized sessions and counts

---

## 4. Frontend data contracts

The frontend should expect JSON like these:

### Login response

```json
{
  "teacher": {
    "teacher_id": "t-001",
    "name": "Ayesha Khan",
    "email": "ayesha.khan@facemark.local",
    "role": "teacher",
    "assigned_section_id": "sec-cse-a"
  },
  "token": "jwt-token"
}
```

### Dashboard response

```json
{
  "teacher": {
    "name": "Ayesha Khan"
  },
  "section": {
    "section_id": "sec-cse-a",
    "section_name": "CSE-A"
  },
  "subjects": [
    { "subject_id": "sub-101", "subject_name": "Database Systems" }
  ],
  "stats": {
    "present": 18,
    "review": 3,
    "pending": 1
  },
  "recent_sessions": []
}
```

### Recognition response

```json
{
  "session_id": "sess-001",
  "results": {
    "confident": [
      { "student_id": "st-001", "name": "Rahul Sharma", "confidence": 0.93 }
    ],
    "uncertain": [
      { "student_id": "st-002", "name": "Priya Nair", "confidence": 0.72 }
    ],
    "unknown": [
      { "face_id": "face-003", "status": "unknown" }
    ],
    "not_detected": [
      { "student_id": "st-010", "name": "Student Name" }
    ]
  }
}
```

---

## 5. Minimal frontend file changes

### HTML

Keep the same screens, but assign IDs and data hooks for dynamic rendering.

Add:

- login form action / result container
- dashboard rendering area
- subject list container
- session creation form
- upload input elements
- recognition results containers
- attendance table container
- history list container

### CSS

Keep the demo style simple.

Need only small UI improvements for:

- loading states
- error messages
- empty states
- table layout
- attendance tag colors

### JavaScript

Main change area is `frontend/app.js`.

Add state management for:

- current teacher
- current section
- current subject
- current session
- uploaded image metadata
- recognition results
- final attendance rows

Add functions for:

- `loginTeacher()`
- `fetchDashboard()`
- `fetchSubjects()`
- `createSession()`
- `uploadPhoto()`
- `recognizeAttendance()`
- `resolveUncertainFaces()`
- `finalizeAttendance()`
- `fetchHistory()`

---

## 6. Best implementation approach

Keep the frontend flow unchanged, but swap static sample values with real API-backed values.

This is important because:

- the product workflow is already validated
- the UI is already clear enough for the demo
- backend integration is the real missing step

Do not redesign the interface heavily. The app should be functional and convincing.

---

## 7. Required API integration points

The frontend must integrate with these backend endpoints:

- `POST /api/auth/login`
- `GET /api/dashboard/teacher/{teacher_id}`
- `GET /api/sections/{section_id}/subjects`
- `POST /api/attendance/sessions`
- `POST /api/attendance/sessions/{session_id}/upload`
- `POST /api/attendance/sessions/{session_id}/recognize`
- `POST /api/attendance/sessions/{session_id}/resolve`
- `POST /api/attendance/sessions/{session_id}/finalize`
- `GET /api/attendance/history`

---

## 8. Error handling requirements

The frontend should handle:

- invalid login credentials
- session creation failures
- upload failures
- recognition errors
- no students found
- backend unavailable
- finalization errors

Use clear user-facing messages and disable buttons during loading.

---

## 9. Acceptance criteria for frontend integration

The frontend is considered integrated when:

- teacher can log in with fake credentials
- dashboard loads real section/subject data
- subject selection is dynamic
- attendance session creation works
- uploaded photo reaches backend successfully
- recognition results are displayed from backend output
- second photo update works
- final review saves final attendance statuses
- finalized sessions appear in attendance history

---

## 10. Final note

The frontend does not need a redesign. It needs backend wiring.

The focus should be on:

- correctness
- reliable API flow
- realistic fake data
- clean production-like behavior

Not on visual polish.
