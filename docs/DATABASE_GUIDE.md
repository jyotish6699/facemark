# FaceMark Database Guide

## 1. Purpose

This file is the low-level database reference for the FaceMark backend implementation.

Use this file only while building the database and backend logic. It is meant to reduce decision fatigue and keep the implementation grounded in the exact demo design.

Do not use this file for high-level product redesign. The product flow is already defined in the main project docs.

---

## 2. Demo database overview

We will use PostgreSQL for the FaceMark hackathon demo.

The database is designed for:

- one teacher
- one section (`CSE-A`)
- multiple subjects in the same section
- fake students enrolled for the section
- teacher login and session management
- attendance sessions and attendance records
- AI recognition results and review flow
- image metadata for uploaded classroom photos

---

## 3. Database name

```text
facemark_demo
```

---

## 4. Database connection

Use this connection string for local development:

```text
postgresql://facemark_app:facemark123@localhost:5432/facemark_demo
```

---

## 5. Required PostgreSQL extensions

```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS vector;
```

These extensions support:

- password hashing / secure IDs
- vector storage for face embeddings

---

## 6. Core entities

### 6.1 Teacher

A teacher can log in and manage attendance for an assigned section.

Required fields:

- id
- teacher_id
- name
- email
- password_hash
- role
- assigned_section_id
- created_at
- updated_at

### 6.2 Section

Represents a class section such as `CSE-A`.

Required fields:

- id
- section_id
- section_name
- department
- semester
- academic_year

### 6.3 Subject

Represents a course taught in that section.

Required fields:

- id
- subject_id
- subject_name
- schedule_day
- room

### 6.4 Student

Represents a student in the section.

Required fields:

- id
- student_id
- full_name
- roll_number
- email
- section_id
- status
- enrollment_image_url
- face_embedding
- created_at
- updated_at

### 6.5 AttendanceSession

Represents one attendance process for one teacher + section + subject + date.

Required fields:

- id
- session_id
- teacher_id
- section_id
- subject_id
- session_date
- status
- notes
- created_at
- updated_at

### 6.6 AttendanceRecord

Stores attendance output for each student in a session.

Required fields:

- id
- attendance_id
- session_id
- student_id
- recognition_status
- confidence_score
- final_status
- source_photo
- is_teacher_override
- created_at
- updated_at

### 6.7 ReviewLog

Stores any teacher changes made during review.

Required fields:

- id
- attendance_id
- teacher_id
- old_status
- new_status
- changed_at
- reason

### 6.8 UploadedImage

Stores metadata for uploaded classroom photos.

Required fields:

- id
- image_id
- session_id
- image_type
- storage_url
- uploaded_by
- created_at

---

## 7. Final schema SQL

```sql
CREATE TABLE teachers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    teacher_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'teacher',
    assigned_section_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE sections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    section_id TEXT UNIQUE NOT NULL,
    section_name TEXT NOT NULL,
    department TEXT NOT NULL,
    semester TEXT NOT NULL,
    academic_year TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE subjects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subject_id TEXT UNIQUE NOT NULL,
    subject_name TEXT NOT NULL,
    schedule_day TEXT,
    room TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE section_subjects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    section_id TEXT NOT NULL,
    subject_id TEXT NOT NULL,
    UNIQUE (section_id, subject_id)
);

CREATE TABLE students (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    roll_number TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE,
    section_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    enrollment_image_url TEXT,
    face_embedding vector(128),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE attendance_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id TEXT UNIQUE NOT NULL,
    teacher_id TEXT NOT NULL,
    section_id TEXT NOT NULL,
    subject_id TEXT NOT NULL,
    session_date DATE NOT NULL,
    status TEXT NOT NULL DEFAULT 'in_progress',
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE attendance_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    attendance_id TEXT UNIQUE NOT NULL,
    session_id TEXT NOT NULL,
    student_id TEXT NOT NULL,
    recognition_status TEXT NOT NULL,
    confidence_score DOUBLE PRECISION,
    final_status TEXT,
    source_photo TEXT,
    is_teacher_override BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE review_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    attendance_id TEXT NOT NULL,
    teacher_id TEXT NOT NULL,
    old_status TEXT,
    new_status TEXT,
    changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    reason TEXT
);

CREATE TABLE uploaded_images (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    image_id TEXT UNIQUE NOT NULL,
    session_id TEXT NOT NULL,
    image_type TEXT NOT NULL CHECK (image_type IN ('first_pass', 'second_pass')),
    storage_url TEXT NOT NULL,
    uploaded_by TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

## 8. Seed data requirements

Seed the following minimal data before backend testing:

### teacher

- `t-001` / `Ayesha Khan`
- email: `ayesha.khan@facemark.local`
- password: `Teacher@123`

### section

- `sec-cse-a` / `CSE-A`

### subjects

- `sub-101` / `Database Systems`
- `sub-102` / `Operating Systems`
- `sub-103` / `Object Oriented Programming`
- `sub-104` / `Data Structures`
- `sub-105` / `Computer Networks`

### students

At least 20 fake students in `CSE-A`.

Use realistic names and roll numbers such as:

- Rahul Sharma / CS-201
- Priya Nair / CS-202
- Arjun Mehta / CS-203
- ...
- 20 students total

---

## 9. Fake face embedding rule

Each student must have a fake embedding field.

The demo does not need a real model for the initial backend implementation.

The backend can use:

- fixed fake vector values for each student
- or a deterministic formula to generate vectors
- or a simple placeholder distance logic for demo matching

The important part is that the app behaves like a real recognition flow during the hackathon demo.

---

## 10. Important demo logic rules

1. One teacher logs in.
2. Teacher sees all subjects of the assigned section.
3. Teacher creates an attendance session for a subject.
4. The system generates attendance rows for all students in the section.
5. The uploaded photo is matched against student embeddings.
6. Recognition result categories are recorded.
7. Second photo is used to resolve uncertain/unknown records.
8. Teacher review finalizes the session.
9. Finalized sessions appear in history.

---

## 11. Notes for backend implementation

Use this database guide as the source of truth while implementing:

- models
- schemas
- repository code
- service logic
- seed scripts
- unit tests
- integration tests

Do not add extra tables or redesign the schema unless the backend task specifically requires a direct product change.

---

## 12. Test folder rule

The backend must include a `tests` folder with:

- `unit/` for isolated logic tests
- `integration/` for API and database flow checks

Example structure:

```text
backend/
  app/
  tests/
    unit/
      test_auth.py
      test_session_logic.py
    integration/
      test_login_flow.py
      test_attendance_flow.py
```

The tests should verify:

- login works with fake teacher credentials
- class/subject loading works
- attendance session creation works
- recognition logic produces confident/uncertain/unknown states
- second photo merge logic prevents duplicates
- finalize flow creates history data

---

## 13. Final implementation reminder

This file is the low-level database reference.

When building the backend, use this as the exact schema and data contract.

Keep the implementation focused on:

- correctness
- demo realism
- testability
- small, reviewable changes

Not on frontend polish or excessive abstraction.
