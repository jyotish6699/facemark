# FaceMark Hackathon Project Plan

## 1. Project goal

Build a working backend + database demo for FaceMark using fake university data so the end-to-end flow feels realistic for a hackathon.

This plan keeps the product real enough for demonstration while staying lightweight:

- one teacher
- one class/section
- multiple subjects taught to the same students
- fake student enrollment data
- fake face data and embeddings
- fake login credentials
- real PostgreSQL database
- backend API to handle login, class selection, sessions, photo upload, recognition results, review, finalization, and attendance history

We are not using actual university data. We are creating a realistic demo dataset that behaves like a real app.

---

## 2. Demo scope

### Core persona

- Teacher: "Ayesha Khan"
- Role: teacher assigned to a class section
- Login: email/password
- Uses dashboard to view classes and subjects for the day
- Starts attendance for a subject and marks students present/absent/reviewed

### Section and class model

- Section: "CSE-A"
- Students: 20–30 fake students across one section
- Teacher handles this section only
- Multiple subjects can be taught to the same section

### Example subjects

- Database Systems
- Operating Systems
- Object Oriented Programming
- Data Structures
- Computer Networks

All of these subjects are taught to the same student list in the same section.

---

## 3. Fake data design

### 3.1 Teacher data

Use one teacher for the hackathon:

- teacher_id: `t-001`
- name: `Ayesha Khan`
- email: `ayesha.khan@facemark.local`
- password: `Teacher@123`
- role: `teacher`
- assigned_section_id: `sec-cse-a`

This teacher should be able to:

- login
- see dashboard
- select the section
- see subject-based attendance opportunities
- create attendance sessions
- view attendance history

### 3.2 Section data

- section_id: `sec-cse-a`
- section_name: `CSE-A`
- department: `Computer Science`
- semester: `5th`
- academic_year: `2026-2027`

### 3.3 Subject data

Example subjects for the same section:

| subject_id | subject_name | schedule_day | room |
|---|---|---|---|
| sub-101 | Database Systems | Monday | DB Lab 2 |
| sub-102 | Operating Systems | Tuesday | OS Lab 1 |
| sub-103 | Object Oriented Programming | Wednesday | Room 305 |
| sub-104 | Data Structures | Thursday | Room 210 |
| sub-105 | Computer Networks | Friday | Room 412 |

### 3.4 Student data

Create 20 students in the same section. Example roll numbers:

- CS-201
- CS-202
- CS-203
- ...
- CS-220

Each student record should include:

- student_id
- full_name
- roll_number
- email (fake)
- section_id
- status: active
- face_embedding (128-dimensional vector or JSONB embedding)
- enrollment_image_url (fake placeholder or local sample image path)
- created_at

Example student:

- student_id: `st-001`
- name: `Rahul Sharma`
- roll_number: `CS-201`
- email: `rahul.sharma@facemark.local`
- section_id: `sec-cse-a`

### 3.5 Face embedding design

For each student, store a face embedding so the recognition pipeline can compare uploaded attendance images with known faces.

Recommended approach:

- use PostgreSQL + pgvector extension
- create `student_face_embeddings` table or keep the embedding field in `students`

Example dimensions:

- 128-dim ArcFace-like vector
- stored as `vector(128)` if using pgvector

Example pseudo-data:

```text
[0.021, -0.113, 0.904, ... , 0.771]
```

This is not real biometric data, only a fake demo vector.

### 3.6 Attendance session data

Example attendance sessions:

- session_id: `sess-001`
- teacher_id: `t-001`
- section_id: `sec-cse-a`
- subject_id: `sub-101`
- session_date: `2026-08-29`
- session_status: `draft` / `in_review` / `finalized`
- created_at

Example:

- `Database Systems` session for `2026-08-29`
- `Operating Systems` session for `2026-08-30`

### 3.7 Attendance log data

Each student attendance entry should store:

- attendance_id
- session_id
- student_id
- recognition_status: `confident`, `uncertain`, `unknown`, `not_detected`
- final_status: `present`, `absent`, `late`, `excused`, `review`
- confidence_score
- is_teacher_override: boolean
- source_photo: `first_pass` / `second_pass`
- created_at
- updated_at

---

## 4. Business workflow for the demo

### Step 1: Teacher login

- Teacher opens web app
- Enters email and password
- Backend validates login against fake teacher data in PostgreSQL
- JWT session is created and stored in secure HTTP-only cookie

### Step 2: Dashboard

Teacher sees:

- assigned section name
- today’s subjects
- attendance summary cards
- recent sessions
- quick actions

Example dashboard items:

- Section: `CSE-A`
- Today: `Database Systems`, `Operating Systems`
- Attendance rate: `82%`
- Pending review sessions: `1`

### Step 3: Select a subject

Teacher chooses a subject for the day:

- Database Systems
- Operating Systems

The subject is linked to the same section and students.

### Step 4: Start attendance session

Teacher clicks "Start Attendance".

Backend creates:

- new session row
- sets session status to `in_progress`
- all students in section are visible as default attendance candidates

### Step 5: Upload classroom image

Teacher uploads a classroom photo.

Backend processes:

- save image to Supabase Storage or local storage for demo
- detect all faces
- crop detected faces
- compare each detected face to all enrolled student embeddings
- assign recognition candidates

### Step 6: Recognition result categories

The recognition result should clearly separate:

- confident matches
- uncertain matches
- unknown faces
- not detected students

Example:

- Rahul Sharma -> confident
- Priya Nair -> uncertain
- Unknown face -> unknown
- Student not present in the image -> not_detected

### Step 7: Second photo workflow

If some students are uncertain or unknown:

- teacher uploads a second image
- backend re-runs face matching against the same student set
- result is merged with first pass
- duplicates are prevented

Important rule:

- second image does not replace first photo
- it resolves incomplete or uncertain recognition evidence

### Step 8: Teacher review

Teacher sees a review table with:

- student name
- roll number
- recognition status
- confidence
- final status dropdown

Teacher chooses:

- present
- absent
- late
- excused
- review

### Step 9: Finalize attendance

Teacher clicks finalize attendance.

Backend updates:

- session status = `finalized`
- all final attendance records are locked
- attendance history becomes visible

### Step 10: Attendance history

Teacher can see prior sessions for the section and subject.

Example:

- Database Systems — 2026-08-29 — 20/22 present
- Operating Systems — 2026-08-30 — 18/20 present

---

## 5. Recommended PostgreSQL database design

### 5.1 Table: teachers

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
```

### 5.2 Table: sections

```sql
CREATE TABLE sections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    section_id TEXT UNIQUE NOT NULL,
    section_name TEXT NOT NULL,
    department TEXT NOT NULL,
    semester TEXT NOT NULL,
    academic_year TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 5.3 Table: subjects

```sql
CREATE TABLE subjects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subject_id TEXT UNIQUE NOT NULL,
    subject_name TEXT NOT NULL,
    schedule_day TEXT,
    room TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 5.4 Table: section_subjects

```sql
CREATE TABLE section_subjects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    section_id TEXT NOT NULL,
    subject_id TEXT NOT NULL,
    UNIQUE (section_id, subject_id)
);
```

### 5.5 Table: students

```sql
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
```

### 5.6 Table: attendance_sessions

```sql
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
```

### 5.7 Table: attendance_records

```sql
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
```

### 5.8 Table: review_logs

```sql
CREATE TABLE review_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    attendance_id TEXT NOT NULL,
    teacher_id TEXT NOT NULL,
    old_status TEXT,
    new_status TEXT,
    changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    reason TEXT
);
```

### 5.9 Table: uploaded_images

```sql
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

## 6. PostgreSQL setup for this demo

### Install PostgreSQL

On Ubuntu/Debian:

```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
```

### Create database

```bash
sudo -u postgres psql
CREATE DATABASE facemark_demo;
```

### Enable pgvector

```bash
sudo -u postgres psql -d facemark_demo
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS vector;
```

### Create schema / app role

```sql
CREATE USER facemark_app WITH PASSWORD 'facemark123';
GRANT ALL PRIVILEGES ON DATABASE facemark_demo TO facemark_app;
```

Then connect using:

```bash
psql postgresql://facemark_app:facemark123@localhost:5432/facemark_demo
```

---

## 7. Sample fake data

### 7.1 Teacher insert

```sql
INSERT INTO teachers (teacher_id, name, email, password_hash, role, assigned_section_id)
VALUES (
  't-001',
  'Ayesha Khan',
  'ayesha.khan@facemark.local',
  '$2b$12$demoHashForTeacherAyesha123',
  'teacher',
  'sec-cse-a'
);
```

### 7.2 Section insert

```sql
INSERT INTO sections (section_id, section_name, department, semester, academic_year)
VALUES ('sec-cse-a', 'CSE-A', 'Computer Science', '5th', '2026-2027');
```

### 7.3 Subjects insert

```sql
INSERT INTO subjects (subject_id, subject_name, schedule_day, room) VALUES
('sub-101', 'Database Systems', 'Monday', 'DB Lab 2'),
('sub-102', 'Operating Systems', 'Tuesday', 'OS Lab 1'),
('sub-103', 'Object Oriented Programming', 'Wednesday', 'Room 305'),
('sub-104', 'Data Structures', 'Thursday', 'Room 210'),
('sub-105', 'Computer Networks', 'Friday', 'Room 412');
```

### 7.4 Section-subject mapping

```sql
INSERT INTO section_subjects (section_id, subject_id) VALUES
('sec-cse-a', 'sub-101'),
('sec-cse-a', 'sub-102'),
('sec-cse-a', 'sub-103'),
('sec-cse-a', 'sub-104'),
('sec-cse-a', 'sub-105');
```

### 7.5 Student insert sample

```sql
INSERT INTO students (
  student_id,
  full_name,
  roll_number,
  email,
  section_id,
  status,
  enrollment_image_url,
  face_embedding
) VALUES
('st-001', 'Rahul Sharma', 'CS-201', 'rahul.sharma@facemark.local', 'sec-cse-a', 'active', 'storage://fake/enroll/rahul.jpg', '[0.021,-0.113,0.904,0.431,0.112,0.882,0.222,0.451,0.999,0.120,0.332,0.501,0.245,0.668,0.741,0.321,0.881,0.421,0.205,0.791,0.610,0.304,0.778,0.645,0.965,0.210,0.537,0.412,0.823,0.315,0.741,0.288,0.541,0.910,0.137,0.600,0.271,0.509,0.897,0.512,0.631,0.112,0.440,0.729,0.614,0.203,0.801,0.327,0.455,0.188,0.790,0.514,0.641,0.219,0.979,0.305,0.534,0.443,0.815,0.299,0.621,0.150,0.322,0.770,0.901,0.274,0.489,0.620,0.198,0.444,0.711,0.952,0.231,0.504,0.611,0.788,0.181,0.500,0.334,0.726,0.803,0.214,0.476,0.631,0.170,0.432,0.780,0.906,0.271,0.317,0.560,0.729,0.184,0.439,0.674,0.800,0.291,0.555,0.612,0.431,0.840,0.261,0.631,0.814,0.345,0.490,0.602,0.716,0.222,0.420,0.802,0.488,0.678,0.219,0.594,0.730,0.351,0.441,0.582]'),
('st-002', 'Priya Nair', 'CS-202', 'priya.nair@facemark.local', 'sec-cse-a', 'active', 'storage://fake/enroll/priya.jpg', '[0.041,-0.103,0.901,0.421,0.176,0.842,0.178,0.499,0.916,0.111,0.301,0.482,0.264,0.690,0.710,0.280,0.875,0.402,0.192,0.761,0.580,0.312,0.769,0.630,0.912,0.204,0.509,0.398,0.807,0.302,0.724,0.271,0.519,0.905,0.144,0.590,0.249,0.493,0.905,0.514,0.600,0.130,0.431,0.745,0.603,0.209,0.798,0.329,0.441,0.181,0.780,0.505,0.632,0.208,0.964,0.291,0.546,0.440,0.826,0.311,0.611,0.160,0.310,0.761,0.881,0.262,0.489,0.614,0.186,0.452,0.701,0.939,0.240,0.487,0.603,0.780,0.173,0.503,0.328,0.711,0.799,0.201,0.489,0.617,0.162,0.426,0.774,0.918,0.250,0.330,0.554,0.714,0.190,0.445,0.661,0.812,0.278,0.548,0.605,0.421,0.834,0.249,0.621,0.801,0.333,0.490,0.592,0.709,0.216,0.424,0.802,0.500,0.665,0.212,0.592,0.708,0.330,0.440,0.576]');
```

Note: For the real implementation, generate or seed all 20–30 student vectors using a script, not manually typed one by one.

---

## 8. Backend API design

### Authentication

- `POST /api/auth/login`
  - body: `{ email, password }`
  - response: teacher profile + JWT token

- `POST /api/auth/logout`
- `GET /api/auth/me`

### Dashboard

- `GET /api/dashboard/teacher/:teacher_id`
  - returns section info, today subjects, stats, recent sessions

### Subjects and classes

- `GET /api/sections/:section_id/subjects`
  - returns all subjects for that section

### Attendance

- `POST /api/attendance/sessions`
  - create a session for a teacher + section + subject + date

- `POST /api/attendance/sessions/:session_id/upload`
  - upload first classroom photo

- `POST /api/attendance/sessions/:session_id/recognize`
  - trigger recognition pipeline

- `POST /api/attendance/sessions/:session_id/resolve`
  - upload second photo for unresolved cases

- `POST /api/attendance/sessions/:session_id/finalize`
  - finalize attendance

- `GET /api/attendance/sessions/:session_id`
  - returns session results and student records

- `GET /api/attendance/history?section_id=...`
  - returns all finalized sessions

---

## 9. Recommended recognition flow

### Input

- classroom photo from teacher
- all enrolled student embeddings from the selected section

### Processing

1. detect faces in uploaded image
2. extract face embeddings
3. compare embeddings with enrolled student vectors
4. compute cosine similarity
5. classify each detected face as:
   - `confident`
   - `uncertain`
   - `unknown`
6. fill `not_detected` for students not found in image
7. store each result in `attendance_records`

### Merge logic

When second image is uploaded:

- do not overwrite original labels blindly
- update uncertain/unknown records only
- keep final attendance unique per student
- prevent double counting

---

## 10. Frontend expectations for this hackathon demo

The frontend should stay simple and functional. We are prioritizing software quality and workflow correctness over a polished interface.

Minimal UI should include:

- login screen
- teacher dashboard
- section details
- subject cards
- attendance session creator
- file upload area
- recognition results screen
- second photo resolution screen
- final attendance review table
- attendance history

No heavy styling work is required. A clean and functional interface is enough.

---

## 11. Implementation order

### Phase 1: Setup and schema

- install PostgreSQL
- create database `facemark_demo`
- enable `pgcrypto` and `vector`
- create tables
- seed fake teacher, section, subject, student data

### Phase 2: Backend foundation

- FastAPI app
- environment variables
- database connection
- auth helpers
- route structure

### Phase 3: Auth and dashboard APIs

- login API
- teacher profile API
- dashboard stats API
- subject listing API

### Phase 4: Attendance workflow APIs

- session creation
- photo upload
- recognition pipeline
- second photo merge
- finalize endpoint

### Phase 5: Review and history

- view attendance details
- allow teacher status edits
- store review logs
- calculate summary stats

### Phase 6: Demo validation

- login with fake teacher credentials
- view dashboard
- select subject
- start session
- upload sample image
- get recognition result categories
- finalize attendance
- confirm history is visible

---

## 12. Example demo credentials

Teacher login:

- email: `ayesha.khan@facemark.local`
- password: `Teacher@123`

Section:

- `CSE-A`

Subjects:

- Database Systems
- Operating Systems
- Object Oriented Programming
- Data Structures
- Computer Networks

Students:

- 20+ fake students under `CSE-A`
- one class section with repeated subject attendance sessions

---

## 13. Important product rules

1. The teacher is the final authority.
2. AI must not silently mark a student absent without teacher review.
3. Uncertain and unknown faces must remain visible for review.
4. Every student in the selected section must be considered for attendance, even if not found in the photo.
5. The same student cannot be counted twice in the same session.
6. The second photo is a resolution step, not a replacement.
7. Database data must be fake but realistic enough to feel like a real demo.

---

## 14. Final note

This is the correct hackathon-scale setup for the backend and database phase:

- realistic fake data
- one teacher and one section
- multiple subjects under the same student set
- working PostgreSQL schema
- correct product flow from login to attendance finalization
- quality over heavy frontend polish

This plan is the base for implementation and should be used before building the backend code and database scripts.
