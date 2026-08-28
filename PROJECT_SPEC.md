# FaceMark — Project Specification

> **Project:** FaceMark — AI-Powered Classroom Attendance  
> **Repository:** `facemark`  
> **Document:** `PROJECT_SPEC.md`  
> **Status:** Pre-development specification  
> **Purpose:** Single source of truth for the frontend, backend, database, AI pipeline, testing, and agent-driven implementation.

---

## 1. Executive Summary

FaceMark is a classroom attendance system where a teacher takes a high-quality photograph of the entire class and uploads it. The backend detects every visible face, compares each face with the registered students of the selected class, and produces attendance candidates.

The frontend clearly separates:

- Confidently recognized students
- Uncertain matches
- Unknown/unmatched faces
- Students not yet detected

If some faces are uncertain or unknown, the teacher takes another photograph specifically to improve recognition. The second photograph is merged with the first result. **The second photograph is used to resolve/retry uncertain or unknown students rather than replacing the first attendance result.**

The teacher remains the final authority and can manually correct recognition results before attendance is finalized.

---

# 2. Core Product Principle

> **AI performs repetitive recognition; the teacher makes the final attendance decision.**

The system must never silently turn an unrecognized face into an absent student.

Important distinction:

- `PRESENT` = confidently recognized or teacher-confirmed
- `REVIEW` = detected face but recognition is uncertain
- `UNKNOWN` = detected face but no suitable student match
- `NOT_DETECTED` = expected class student whose face has not been identified in the submitted photos
- `ABSENT` = final teacher/system attendance decision after the recognition/review workflow

---

# 3. Problem

Manual classroom attendance is:

- Time-consuming
- Repetitive
- Prone to counting mistakes
- Disruptive to class time
- Difficult to maintain accurately over many sessions

FaceMark reduces the repetitive work by processing one or more classroom photographs.

---

# 4. Goals

## 4.1 Primary Goals

1. Allow a teacher to select a class and attendance session.
2. Allow the teacher to upload a classroom photograph.
3. Detect multiple faces from one photograph.
4. Match detected faces against students enrolled in the selected class.
5. Display recognition confidence/results to the teacher.
6. Allow a second photograph when recognition is uncertain.
7. Merge recognition results from multiple photographs for the same session.
8. Allow teacher correction.
9. Finalize and store attendance.
10. Provide attendance history.

## 4.2 Secondary Goals

- Good error handling
- Secure authentication and authorization
- Auditable attendance changes
- Clear AI confidence handling
- Responsive teacher dashboard
- Deployment-ready architecture

---

# 5. Non-Goals for MVP

The MVP will NOT attempt to solve every possible computer-vision problem.

The teacher is responsible for:

- Ensuring every student is inside the photograph.
- Positioning smaller/farther students so faces are sufficiently visible.
- Using a phone/camera with adequate image quality.
- Retaking the photograph when the overall image is clearly unsuitable.

The MVP does not require:

- Continuous classroom video monitoring
- Automatic surveillance
- Perfect recognition under extreme conditions
- Advanced anti-spoofing/liveness detection
- Automatic attendance from a student's phone
- Voice-based attendance
- Hardware/camera installation in classrooms

Advanced features may be added later.

---

# 6. Users and Roles

## 6.1 Admin

Responsibilities:

- Manage teachers
- Manage students
- Manage classes
- Assign students to classes
- Manage teacher/class relationships
- Configure system settings
- View system-wide attendance where authorized

## 6.2 Teacher

Responsibilities:

- View assigned classes
- Start attendance session
- Upload classroom photographs
- Review recognition results
- Resolve uncertain/unknown faces
- Manually correct attendance
- Finalize attendance
- View attendance history for authorized classes

## 6.3 Student

Student functionality is optional for MVP.

If included:

- View own attendance history
- View attendance percentage
- No ability to modify attendance

---

# 7. High-Level Architecture

```text
                    ┌──────────────────────┐
                    │      Teacher UI      │
                    │   Web/Mobile Web     │
                    └──────────┬───────────┘
                               │ HTTPS
                               ▼
                    ┌──────────────────────┐
                    │      Backend API     │
                    │ Authentication       │
                    │ Classes              │
                    │ Attendance Sessions  │
                    │ Uploads              │
                    │ Recognition Results  │
                    └──────┬─────────┬─────┘
                           │         │
                 ┌─────────┘         └──────────┐
                 ▼                              ▼
        ┌─────────────────┐            ┌──────────────────┐
        │    Database     │            │ Face Recognition │
        │ PostgreSQL      │            │ Service/Model    │
        └─────────────────┘            └────────┬─────────┘
                                                │
                                                ▼
                                      Face Detection +
                                      Embeddings +
                                      Matching
```

---

# 8. Sequential End-to-End Process

## Phase A — Initial System Setup

### Step A1 — Admin creates organization/system

Create the initial application environment.

### Step A2 — Admin creates teacher account

Store:

- Teacher ID
- Name
- Email/login identity
- Role
- Account status

### Step A3 — Admin creates students

For each student:

- Student ID
- Name
- Enrollment/roll number
- Optional metadata
- Face enrollment images
- Face embedding(s)

### Step A4 — Face enrollment

For each student:

```text
Enrollment image(s)
        ↓
Validate image
        ↓
Detect face
        ↓
Ensure suitable face
        ↓
Generate face embedding
        ↓
Store embedding securely
```

A student should have enough good enrollment data to improve recognition reliability.

### Step A5 — Admin creates class

Example:

```text
CSE-A
Semester: 5
Academic Year: 2026-27
```

### Step A6 — Admin assigns students to class

The system creates class membership records.

### Step A7 — Admin assigns teacher to class

Teacher can now conduct attendance for that class.

---

# 9. Attendance Session Workflow

## Step B1 — Teacher logs in

Frontend authenticates the teacher.

Backend verifies identity and role.

## Step B2 — Teacher selects class

Example:

```text
Class: CSE-A
Subject: Operating Systems
Date: 2026-08-29
```

The backend verifies that the teacher is authorized for that class.

## Step B3 — Teacher starts attendance session

Backend creates:

```text
Attendance Session
status = PROCESSING / OPEN
class_id
teacher_id
subject
date/time
```

The session gets a unique ID.

## Step B4 — Teacher takes first class photograph

Teacher ensures:

- Everyone is inside the frame
- Faces are visible
- Smaller/farther students are positioned appropriately
- Camera quality is adequate

## Step B5 — Frontend uploads photograph

The frontend:

1. Validates file type.
2. Validates file size.
3. Shows upload progress.
4. Sends image to backend.
5. Receives processing status.

## Step B6 — Backend validates photograph

Validate:

- File type
- File size
- Image can be decoded
- Image dimensions
- Basic image quality
- Request authorization
- Session is still open

If invalid:

```text
Upload rejected
Reason shown to teacher
Teacher can upload another image
```

## Step B7 — Backend detects faces

```text
Class photograph
      ↓
Face detector
      ↓
Face 1
Face 2
Face 3
...
Face N
```

For each detected face, store a temporary processing result.

## Step B8 — Generate face embeddings

For every usable detected face:

```text
Detected face
      ↓
Preprocessing/alignment
      ↓
Face embedding model
      ↓
Embedding vector
```

## Step B9 — Restrict candidate database

Do NOT compare against every student in the entire system.

Only compare against:

```text
Students enrolled in selected class
```

This improves:

- Performance
- Accuracy
- Privacy
- Explainability

## Step B10 — Match faces

For each detected face:

```text
Detected embedding
        ↓
Compare with class student embeddings
        ↓
Find best candidate
        ↓
Apply configured matching threshold
        ↓
Result
```

Possible result:

```text
CONFIDENT_MATCH
UNCERTAIN_MATCH
UNKNOWN
```

The exact threshold must be configurable and validated experimentally.

## Step B11 — First result returned to frontend

Example:

```text
55 students enrolled

48 confident matches
4 uncertain matches
2 unknown faces
1 not yet detected
```

The frontend displays the results visually.

---

# 10. Recognition Result UI

The teacher should see something similar to:

```text
Attendance Review

✅ Confidently Recognized
--------------------------------
Rahul     98%
Aman      96%
Priya     94%
...

⚠️ Needs Review
--------------------------------
Face #12  → Rahul? 67%
Face #18  → Priya? 63%

❓ Unknown
--------------------------------
Face #23

👤 Not Detected
--------------------------------
Student 42
Student 51

[Take Another Photo]
[Review Attendance]
```

The exact visual design can change, but the information hierarchy must remain.

---

# 11. Second Photograph Workflow

## Step C1 — Teacher reviews uncertain/unknown faces

Frontend highlights faces requiring additional evidence.

## Step C2 — Teacher takes another photograph

Teacher positions relevant students appropriately and takes another image.

## Step C3 — Teacher uploads second photograph

The second image belongs to the **same attendance session**.

## Step C4 — Backend processes second photograph

Repeat:

```text
Validate
  ↓
Detect
  ↓
Embed
  ↓
Match
```

## Step C5 — Merge with first result

The second photograph does NOT replace the first result.

Instead:

```text
First photo results
        +
Second photo results
        ↓
Merged session result
```

Recognition is counted once per student.

Example:

```text
Photo 1:
Rahul → Present
Aman  → Present
Priya → Uncertain

Photo 2:
Priya → Confident

Final:
Rahul → Present
Aman  → Present
Priya → Present
```

If the second photograph contains an already recognized student, do not create duplicate attendance.

---

# 12. Teacher Verification

After processing all required photographs:

```text
AI Results
    ↓
Teacher Review
    ↓
Corrections if required
    ↓
Final Attendance
```

Teacher must be able to:

- Confirm a recognized student
- Change an incorrect match
- Assign an unknown face to a student where appropriate
- Mark a student present manually
- Mark a student absent
- Resolve uncertain results
- See which photograph produced evidence for a recognition result

All manual changes should be auditable.

---

# 13. Final Attendance Rules

Recommended final states:

```text
PRESENT
ABSENT
EXCUSED (optional)
```

Recognition pipeline states:

```text
CONFIDENT_MATCH
UNCERTAIN
UNKNOWN
NOT_DETECTED
```

Do not confuse recognition state with final attendance state.

Example:

```text
Recognition:
UNKNOWN

Teacher:
Identifies student manually

Final attendance:
PRESENT
```

---

# 14. Duplicate Recognition Rule

If a student appears in multiple photographs:

```text
Photo 1 → Rahul
Photo 2 → Rahul
Photo 3 → Rahul
```

Final attendance:

```text
Rahul → PRESENT
```

Never count the same student more than once in a session.

---

# 15. Unknown Face Rule

If a face is detected but cannot confidently match any student:

```text
UNKNOWN
```

Do NOT automatically mark any student absent because of this.

Teacher can:

- Take another photograph
- Manually identify the student
- Leave it unresolved

---

# 16. Uncertain Match Rule

Example:

```text
Face → Rahul
Confidence → 65%
```

If below the configured confident threshold:

```text
UNCERTAIN
```

Teacher should be prompted to provide another photograph or manually resolve the result.

---

# 17. Not Detected Rule

A student can remain:

```text
NOT_DETECTED
```

when their face has not been sufficiently identified across the submitted photographs.

The system must not automatically convert this state into `ABSENT` before the teacher's final review.

---

# 18. Wrong Match Correction

Example:

```text
AI:
Face #4 → Rahul

Teacher:
Actually → Rohit
```

Teacher changes the candidate.

The system records:

```text
original_prediction = Rahul
final_decision = Rohit
changed_by = teacher_id
changed_at = timestamp
```

---

# 19. Attendance Finalization

Teacher selects:

```text
[Finalize Attendance]
```

Backend checks:

- Teacher is authorized
- Session exists
- Session belongs to selected class
- All required review decisions are handled according to policy
- No duplicate final attendance records
- Final result is internally consistent

Then:

```text
Session status = FINALIZED
```

After finalization, normal teacher editing should be disabled or require an explicit correction/reopen workflow.

---

# 20. Attendance History

Teachers should be able to view:

```text
Class
Date
Subject
Present count
Absent count
Attendance percentage
Session status
```

For an individual student:

```text
Date | Subject | Status
-------------------------
Aug 01 | OS | Present
Aug 03 | OS | Absent
Aug 05 | OS | Present
```

---

# 21. Backend Responsibilities

The backend owns:

- Authentication verification
- Authorization
- User management
- Class management
- Student management
- Face enrollment
- Image upload handling
- Image validation
- Recognition orchestration
- Attendance session state
- Recognition result persistence
- Result merging
- Teacher corrections
- Attendance finalization
- Attendance history
- Audit logs
- Error handling
- Security controls

The frontend must NOT be trusted to decide authorization or final attendance persistence.

---

# 22. Frontend Responsibilities

The frontend owns:

- Login UI
- Dashboard
- Class selection
- Attendance session creation UI
- Image upload UI
- Upload progress
- Processing status
- Recognition result visualization
- Face/result review
- Second-photo workflow
- Manual correction UI
- Final confirmation UI
- Attendance history
- Error messages
- Loading states
- Responsive design

The frontend should never contain secrets such as database credentials or private API keys.

---

# 23. Frontend Screens

## Screen 1 — Login

Fields:

- Email/username
- Password or configured authentication method

States:

- Loading
- Invalid credentials
- Account disabled
- Network error

## Screen 2 — Teacher Dashboard

Display:

- Assigned classes
- Recent attendance sessions
- Quick action to start attendance

## Screen 3 — Select Class

Display:

- Class
- Subject
- Student count

## Screen 4 — Attendance Setup

Display:

- Selected class
- Subject
- Date
- Student count
- Start session button

## Screen 5 — Photo Upload

Display:

- Upload area
- Supported format
- File size guidance
- Upload progress
- Processing status

## Screen 6 — Recognition Results

Display:

- Confident matches
- Uncertain matches
- Unknown faces
- Not detected students
- Confidence information where appropriate
- Second photo action

## Screen 7 — Second Photo

Display:

- Faces needing additional evidence
- Upload/take another photo action
- Processing state

## Screen 8 — Final Review

Display every class student:

```text
Student | Recognition | Final Status | Action
```

Actions:

- Confirm
- Change student
- Present
- Absent

## Screen 9 — Attendance History

Display:

- Session list
- Date
- Class
- Subject
- Counts

## Screen 10 — Student Attendance

Optional MVP screen.

---

# 24. Backend API Requirements

The exact API style can be REST or another documented approach. The implementation agent must choose one consistently.

Suggested REST endpoints:

## Authentication

```text
POST   /api/auth/login
POST   /api/auth/logout
GET    /api/auth/me
```

## Classes

```text
GET    /api/classes
GET    /api/classes/:classId
GET    /api/classes/:classId/students
```

## Students

```text
POST   /api/students
GET    /api/students/:studentId
PATCH  /api/students/:studentId
DELETE /api/students/:studentId
```

## Enrollment

```text
POST   /api/students/:studentId/face-enrollment
GET    /api/students/:studentId/face-enrollment
DELETE /api/students/:studentId/face-enrollment/:enrollmentId
```

## Attendance Sessions

```text
POST   /api/attendance-sessions
GET    /api/attendance-sessions/:sessionId
POST   /api/attendance-sessions/:sessionId/photos
GET    /api/attendance-sessions/:sessionId/results
POST   /api/attendance-sessions/:sessionId/review
POST   /api/attendance-sessions/:sessionId/finalize
```

## Attendance History

```text
GET /api/classes/:classId/attendance
GET /api/students/:studentId/attendance
```

The implementation agent must document the final API contract before implementation.

---

# 25. API Contract Rules

Every API must define:

- HTTP method
- Path
- Authentication requirement
- Authorization requirement
- Request body
- Query parameters
- Response body
- HTTP status codes
- Validation errors
- Authentication errors
- Authorization errors
- Server errors

Example:

```json
{
  "sessionId": "uuid",
  "status": "PROCESSING"
}
```

Do not leave API response formats undefined during implementation.

---

# 26. Database Requirements

Recommended database: **PostgreSQL**.

The schema must preserve relationships and historical attendance.

Suggested entities:

```text
users
students
teachers
classes
class_memberships
teacher_classes
subjects
attendance_sessions
attendance_photos
detected_faces
face_enrollments
face_embeddings
recognition_results
attendance_records
audit_logs
```

The final implementation may merge or split tables where technically justified, but relationships and data ownership must remain clear.

---

# 27. Suggested Database Schema

## users

```text
id
email
password_hash / auth_provider_id
role
status
created_at
updated_at
```

Roles:

```text
ADMIN
TEACHER
STUDENT (optional)
```

## students

```text
id
user_id (optional)
student_number
full_name
status
created_at
updated_at
```

## teachers

```text
id
user_id
employee_number (optional)
created_at
updated_at
```

## classes

```text
id
name
semester
academic_year
status
created_at
updated_at
```

## subjects

```text
id
name
code
created_at
updated_at
```

## class_memberships

```text
id
class_id
student_id
joined_at
left_at (nullable)
status
```

Historical membership must not be destroyed when a student changes class.

## teacher_classes

```text
id
teacher_id
class_id
assigned_at
status
```

## attendance_sessions

```text
id
class_id
subject_id
teacher_id
session_date
started_at
finalized_at
status
created_at
updated_at
```

Suggested status:

```text
OPEN
PROCESSING
REVIEW
FINALIZED
CANCELLED
```

## attendance_photos

```text
id
attendance_session_id
storage_key
original_filename
mime_type
file_size
width
height
processing_status
uploaded_at
processed_at
```

Do not store large image binaries directly in PostgreSQL unless there is a strong reason. Prefer object/file storage.

## detected_faces

```text
id
attendance_photo_id
face_index
bounding_box
quality_score
detection_status
created_at
```

Bounding box should contain the face location required by the UI.

## face_enrollments

```text
id
student_id
image_storage_key
quality_score
status
created_at
```

## face_embeddings

```text
id
face_enrollment_id
embedding
model_name
model_version
created_at
```

The implementation must choose a storage strategy appropriate for the selected embedding/vector technology.

## recognition_results

```text
id
attendance_session_id
detected_face_id
candidate_student_id
confidence_score
recognition_status
source_photo_id
created_at
updated_at
```

Suggested recognition states:

```text
CONFIDENT_MATCH
UNCERTAIN
UNKNOWN
```

## attendance_records

```text
id
attendance_session_id
student_id
final_status
source
original_recognition_result_id
reviewed_by
reviewed_at
created_at
updated_at
```

Suggested final statuses:

```text
PRESENT
ABSENT
EXCUSED (optional)
```

Suggested sources:

```text
AI
TEACHER
```

A unique constraint should prevent:

```text
attendance_session_id + student_id
```

from being recorded more than once.

## audit_logs

```text
id
actor_user_id
entity_type
entity_id
action
old_value
new_value
created_at
```

Audit logs are important for attendance corrections.

---

# 28. Face Recognition Data Rules

Face data is sensitive biometric information.

The implementation must:

- Minimize stored biometric data
- Use access control
- Encrypt data in transit
- Protect stored data
- Restrict who can access face enrollment data
- Avoid exposing embeddings through normal frontend APIs
- Avoid logging embeddings
- Avoid logging raw face images unnecessarily
- Define retention/deletion behavior
- Obtain appropriate consent according to the deployment context
- Provide an appropriate data deletion process where required

The system must comply with applicable laws, institutional policies, and consent requirements.

---

# 29. Face Recognition Pipeline

```text
Upload image
    ↓
Validate file
    ↓
Decode image
    ↓
Quality checks
    ↓
Face detection
    ↓
Face alignment/preprocessing
    ↓
Generate embedding
    ↓
Load enrolled students for selected class
    ↓
Compare embedding with candidate embeddings
    ↓
Determine best candidate
    ↓
Apply threshold policy
    ↓
CONFIDENT / UNCERTAIN / UNKNOWN
    ↓
Persist result
    ↓
Return frontend result
```

---

# 30. Matching Policy

Do not hard-code a random confidence threshold.

The implementation must:

1. Select a recognition model.
2. Understand the model's similarity/distance metric.
3. Define a threshold.
4. Validate the threshold against representative test data.
5. Document false-match and false-non-match tradeoffs.
6. Make the threshold configurable where appropriate.

Important:

> A confidence score must not be presented as a universal probability unless the model actually provides calibrated probabilities.

---

# 31. Candidate Search

Recognition must search only the selected class's enrolled students.

Example:

```text
Selected class = CSE-A

Search candidates:
CSE-A students only
```

Do not perform unrestricted global matching unless a future feature explicitly requires it.

---

# 32. Result Merge Algorithm Requirements

The merge process must be deterministic.

Conceptually:

```text
First photo results
        ↓
Current student result map
        ↓
Second photo
        ↓
Compare evidence
        ↓
Update unresolved/weak results
        ↓
Keep strongest valid evidence
        ↓
Deduplicate student
        ↓
Final recognition candidates
```

Example:

```text
Photo 1:
Rahul = 0.96
Priya = uncertain

Photo 2:
Priya = 0.93

Merged:
Rahul = PRESENT candidate
Priya = PRESENT candidate
```

The implementation must define what happens when two photos produce conflicting confident identities.

Recommended approach:

- Do not silently overwrite conflicting evidence.
- Preserve both recognition events.
- Flag conflict for teacher review.
- Let the teacher make the final decision.

---

# 33. Image Requirements

Teacher is expected to use a suitable camera.

Frontend should communicate guidance:

- Include the entire class
- Keep faces visible
- Avoid extreme blur
- Use adequate lighting
- Avoid blocking faces
- Use sufficient image resolution

Backend should still validate basic technical quality.

The system should not rely solely on the frontend for validation.

---

# 34. File Upload Security

Backend must:

- Allow only supported image MIME types
- Validate actual file content, not only extension
- Enforce file-size limits
- Enforce image-dimension limits
- Generate safe storage names
- Prevent path traversal
- Store uploads outside executable code directories
- Scan/validate files where appropriate
- Avoid trusting original filenames
- Restrict access to stored images

---

# 35. Authentication and Authorization

Every protected backend endpoint must verify authentication.

Authorization examples:

```text
Teacher A
   ↓
Can access assigned Class A

Teacher A
   ↓
Cannot modify Class B
```

Never rely on hidden frontend controls for authorization.

Backend authorization is mandatory.

---

# 36. Error Handling

Frontend must provide useful errors.

Examples:

```text
Image format not supported.
Image is too large.
Image could not be processed.
No faces were detected.
Recognition service is temporarily unavailable.
Session has already been finalized.
You are not authorized to access this class.
```

Backend should return consistent machine-readable errors.

Suggested structure:

```json
{
  "error": {
    "code": "INVALID_IMAGE",
    "message": "The uploaded image could not be processed."
  }
}
```

Do not expose stack traces or internal secrets to users.

---

# 37. Processing States

Photo processing:

```text
UPLOADED
VALIDATING
DETECTING
RECOGNIZING
COMPLETED
FAILED
```

Attendance session:

```text
OPEN
PROCESSING
REVIEW
FINALIZED
CANCELLED
```

Frontend must show appropriate loading and failure states.

---

# 38. Concurrency Rules

The system must handle:

- Teacher double-clicking upload
- Same photo submitted twice
- Multiple requests for same session
- Two browser tabs
- Finalize request repeated

Recommended protections:

- Idempotency where appropriate
- Database uniqueness constraints
- Transactional finalization
- Server-side session state validation

---

# 39. Duplicate Photo Rule

If the same photograph is uploaded twice for the same session:

- Detect duplicate where practical using a file hash/content hash.
- Do not create duplicate attendance.
- Either reuse processing result or inform the teacher.

This is not required to be perfect for MVP but must not create duplicate final attendance records.

---

# 40. Session State Rules

Example:

```text
OPEN
 ↓
Photo uploaded
 ↓
PROCESSING
 ↓
REVIEW
 ↓
Second photo (optional)
 ↓
REVIEW
 ↓
Teacher finalizes
 ↓
FINALIZED
```

After:

```text
FINALIZED
```

new photographs should not be added unless an explicit reopen/correction feature exists.

---

# 41. Security Requirements

Minimum:

- HTTPS in production
- Secure authentication
- Password hashing if passwords are locally managed
- Role-based authorization
- Secure cookies/token handling according to chosen auth architecture
- Input validation
- File validation
- Rate limiting where appropriate
- Secure database credentials
- Secrets stored in environment/secret manager
- No secrets committed to Git
- No biometric embeddings in logs
- Audit logging for attendance changes

---

# 42. Privacy Requirements

The implementation must document:

- What biometric data is stored
- Why it is stored
- Who can access it
- How long it is retained
- How it is deleted
- What happens when a student leaves
- How enrollment consent is handled
- Whether uploaded attendance photographs are retained
- Whether embeddings can be regenerated from enrollment images

These policies must be configurable where practical.

---

# 43. Student Lifecycle

## New student

```text
Create student
 ↓
Enroll face
 ↓
Assign to class
 ↓
Eligible for recognition
```

## Student changes class

Do not delete historical attendance.

Instead:

```text
Old membership → ended
New membership → created
```

Recognition candidate list is based on the class selected for the current attendance session.

## Student leaves institution

Student becomes inactive.

Historical attendance remains available according to retention policy.

---

# 44. Teacher Lifecycle

Teacher can only conduct attendance for assigned/authorized classes.

If assignment is removed:

- Existing historical records remain.
- New attendance sessions cannot be created for that class by that teacher.

---

# 45. Testing Strategy

Testing is mandatory before final deployment.

## Unit tests

Test:

- Authentication logic
- Authorization logic
- Matching threshold logic
- Merge algorithm
- Duplicate prevention
- Attendance finalization
- State transitions
- Validation

## Integration tests

Test:

```text
Upload
 ↓
Recognition
 ↓
Persistence
 ↓
Review
 ↓
Finalization
```

## Frontend tests

Test:

- Login
- Class selection
- Upload
- Loading states
- Recognition result display
- Second photo
- Manual correction
- Finalization
- Error states

## AI evaluation

Use a controlled test dataset to evaluate:

- True matches
- False matches
- False non-matches
- Unknown faces
- Multiple faces
- Different face sizes
- Different poses
- Lighting variation

Never claim 100% accuracy without evidence.

---

# 46. Acceptance Criteria

The MVP is considered complete when:

1. Admin can create/manage students.
2. Students can have face enrollment data.
3. Admin can create classes.
4. Students can be assigned to classes.
5. Teachers can be assigned to classes.
6. Teacher can create an attendance session.
7. Teacher can upload a class photograph.
8. Backend detects multiple faces.
9. Backend compares faces only against students in the selected class.
10. Results are classified as confident, uncertain, or unknown.
11. Frontend displays recognition results.
12. Teacher can upload a second photograph.
13. Second photograph results merge with first results.
14. Duplicate student recognition does not create duplicate attendance.
15. Teacher can manually correct results.
16. Teacher can finalize attendance.
17. Final attendance records are persisted.
18. Attendance history is available.
19. Unauthorized users cannot access protected class/attendance data.
20. Errors are handled without crashing the workflow.
21. Basic biometric privacy/security requirements are implemented.
22. Automated tests cover critical backend logic.
23. The application can be deployed using documented instructions.

---

# 47. MVP Scope

## Must Have

```text
Authentication
Student management
Face enrollment
Class management
Teacher/class assignment
Attendance session
Photo upload
Multi-face detection
Face recognition
Confidence handling
Unknown handling
Second-photo workflow
Result merging
Teacher review
Manual correction
Attendance finalization
Attendance history
Database persistence
Basic security
```

## Should Have

```text
Upload progress
Image quality feedback
Audit logs
Duplicate photo detection
Detailed processing status
Responsive UI
```

## Future

```text
Liveness detection
Multiple-camera support
Mobile native app
Advanced analytics
Automated timetable integration
Notifications
Student portal
Institution-wide reporting
Offline processing
Advanced anti-spoofing
```

---

# 48. Recommended Technology Selection Process

The implementation agent must NOT blindly choose technologies.

Before implementation it must evaluate:

## Frontend

Possible:

```text
React
Next.js
TypeScript
Tailwind CSS
```

## Backend

Possible:

```text
FastAPI + Python
Django
Node.js + TypeScript
```

## Database

Recommended:

```text
PostgreSQL
```

## Object Storage

Possible:

```text
S3-compatible storage
Supabase Storage
Cloud storage
```

## Face Recognition

The agent must evaluate available and legally usable options, including:

- Face detection library/model
- Face embedding model
- Similarity metric
- Vector storage/search approach
- CPU/GPU requirements
- Licensing
- Deployment constraints
- Accuracy tradeoffs

**The agent must document the selected stack and rationale before implementation.**

---

# 49. Local Development Requirements

The final development environment must document:

- Required runtime versions
- Package manager
- Environment variables
- Database setup
- Object storage setup
- AI model setup
- Migration commands
- Seed data
- Development commands
- Test commands
- Build commands

No developer should need to guess setup steps.

---

# 50. Environment Variables

Do not hard-code secrets.

Example categories:

```text
DATABASE_URL
AUTH_SECRET
STORAGE_ENDPOINT
STORAGE_ACCESS_KEY
STORAGE_SECRET_KEY
STORAGE_BUCKET
FACE_MODEL_CONFIG
FACE_MATCH_THRESHOLD
FRONTEND_URL
BACKEND_URL
```

The final names depend on the selected architecture.

Provide:

```text
.env.example
```

with safe placeholder values.

Never commit:

```text
.env
```

or real secrets.

---

# 51. Repository Structure

The final structure should be clear and maintainable.

Possible structure:

```text
facemark/
├── frontend/
├── backend/
├── docs/
├── tests/
├── .env.example
├── .gitignore
├── PROJECT_SPEC.md
├── README.md
└── ...
```

The agent may modify this structure if there is a documented technical reason.

Frontend and backend responsibilities must remain clearly separated.

---

# 52. Documentation Requirements

Before implementation:

```text
PROJECT_SPEC.md
```

After architecture decisions:

```text
ARCHITECTURE.md
API.md
DATABASE.md
AI_PIPELINE.md
SECURITY.md
SETUP.md
```

Not every document must be separate if the project remains small, but the information must exist somewhere clearly.

---

# 53. Agent Development Protocol

This section is mandatory.

The coding agent must follow this order:

## Step 1 — Read the specification

Read:

```text
PROJECT_SPEC.md
```

completely before modifying code.

## Step 2 — Inspect repository

Inspect:

- Existing files
- Git status
- Existing branches
- Package files
- Environment files
- Existing applications
- Existing documentation

Do not assume the repository is empty.

## Step 3 — Extract requirements

Create an internal checklist:

```text
Requirement
Source
Implementation area
Dependencies
Acceptance criteria
Status
```

## Step 4 — Identify missing decisions

The agent must explicitly identify:

- Ambiguous requirements
- Missing credentials/configuration
- Missing model decisions
- Missing API contracts
- Missing database decisions
- Missing deployment constraints
- Missing privacy/security decisions

## Step 5 — STOP if critical information is missing

Do not start large-scale implementation when a critical architectural decision is unresolved.

Ask for clarification or present proposed options.

## Step 6 — Propose architecture

Before implementation, provide:

```text
Frontend architecture
Backend architecture
Database architecture
AI pipeline
Storage
Authentication
Deployment
Testing
```

## Step 7 — Validate architecture against PROJECT_SPEC.md

The agent must verify that the architecture satisfies every requirement.

## Step 8 — Create implementation plan

Break work into small sequential tasks.

Example:

```text
1. Repository setup
2. Backend foundation
3. Database schema
4. Authentication
5. Student management
6. Class management
7. Face enrollment
8. Attendance session
9. Upload pipeline
10. Face detection
11. Face recognition
12. Recognition result UI
13. Second-photo merge
14. Teacher review
15. Finalization
16. History
17. Security
18. Testing
19. Deployment
```

## Step 9 — Implement incrementally

After each meaningful phase:

- Run tests
- Check types
- Check lint
- Verify database migrations
- Verify API behavior
- Update documentation

## Step 10 — Never fabricate missing infrastructure

If an external service, credential, model, or configuration is unavailable:

```text
STOP
REPORT
PROPOSE NEXT STEP
```

Do not silently replace it with an unrelated technology.

---

# 54. Definition of Done for Each Feature

A feature is not complete merely because code exists.

Each feature must have:

```text
Implementation
Validation
Error handling
Tests
Documentation
Security review
UI state handling (if frontend)
Database migration (if needed)
API documentation (if applicable)
```

---

# 55. Git Workflow

Use small, meaningful commits.

Recommended format:

```text
feat: add attendance session API
feat: add face enrollment workflow
feat: add recognition result review
fix: prevent duplicate attendance records
test: add recognition merge tests
docs: update API specification
```

Do not combine unrelated features into one commit.

Before committing:

```text
git status
tests
lint
typecheck/build
```

must be checked as applicable.

---

# 56. Observability

The backend should provide safe logs for:

- Request failures
- Processing failures
- Recognition service failures
- Database failures
- Authentication failures
- Important attendance state transitions

Do NOT log:

- Passwords
- Authentication secrets
- Raw embeddings
- Sensitive biometric information
- Private image contents

---

# 57. Performance Considerations

The system should be designed so that:

- Recognition is performed asynchronously if processing takes significant time.
- Large images are handled safely.
- Class candidate sets are limited.
- Repeated recognition of the same student is deduplicated.
- Database queries are indexed appropriately.
- Image files are stored outside the relational database when appropriate.

The implementation must measure performance rather than prematurely optimizing.

---

# 58. Important Edge Cases

The MVP explicitly handles:

### Face partially visible

Result:

```text
UNCERTAIN
```

or detection failure.

Teacher can retake photograph.

### Face too small

Teacher is expected to position students appropriately.

If detection/recognition fails:

```text
NOT_DETECTED / UNKNOWN
```

Teacher can retake.

### Poor image

Backend rejects technically invalid/unusable files where detectable.

### Unknown face

```text
UNKNOWN
```

Do not automatically assign it to a student.

### Low-confidence match

```text
UNCERTAIN
```

### Similar-looking students

If confidence is insufficient or candidates conflict:

```text
REVIEW
```

### Student appears in multiple photos

Count only once.

### Student appears in first and second photos

Merge evidence; do not duplicate attendance.

### Wrong AI match

Teacher can correct it.

### Student absent

Student remains unresolved/not detected and can be marked absent during final teacher review.

### Wrong class selected

Backend authorization and class/student scope must prevent cross-class recognition.

### Teacher uploads same photo twice

Prevent duplicate final attendance.

### Teacher uploads wrong image

Allow replacement/additional photo while session is open; reject/fail images that cannot be processed.

### Recognition service fails

Keep session recoverable:

```text
PROCESSING/FAILED
```

Teacher should be able to retry.

### Database unavailable

Do not claim attendance was saved unless persistence succeeds.

### Session finalized

Prevent normal new-photo uploads after finalization.

---

# 59. Important Product Decisions Already Confirmed

These decisions are locked unless explicitly changed later:

1. Teacher takes a photograph of the whole class.
2. Teacher ensures students are visible before taking the photograph.
3. Camera quality is the teacher's responsibility.
4. The system supports multiple faces in one image.
5. The first image is the primary recognition pass.
6. Frontend shows uncertain/unknown results.
7. Teacher can take a second photograph.
8. The second photograph is used to resolve/retry uncertain/unknown cases.
9. The second photograph is merged with the first.
10. The second photograph does not replace the first result.
11. A student is counted only once per attendance session.
12. Teacher can manually correct AI results.
13. Teacher has final authority over attendance.
14. `Not recognized` must NOT automatically mean `Absent`.
15. Recognition candidates are limited to the selected class.
16. Attendance is finalized only after teacher review.

---

# 60. Decisions Requiring Validation Before Implementation

The coding agent must explicitly validate these before significant implementation:

- Exact frontend framework
- Exact backend framework
- Authentication approach
- Face detection model/library
- Face embedding model
- Similarity metric
- Recognition threshold
- Vector storage/search approach
- Image/object storage
- Database hosting
- Deployment target
- Biometric data retention policy
- Consent workflow
- Whether student-facing UI is MVP
- Exact subject/timetable model
- Exact admin workflow

These must not be guessed silently.

---

# 61. Build Order

The recommended sequential implementation order is:

```text
PHASE 0
Specification validation
        ↓
PHASE 1
Repository + development environment
        ↓
PHASE 2
Database + migrations
        ↓
PHASE 3
Authentication + authorization
        ↓
PHASE 4
Admin/student/class management
        ↓
PHASE 5
Face enrollment
        ↓
PHASE 6
Teacher dashboard
        ↓
PHASE 7
Attendance session creation
        ↓
PHASE 8
Photo upload/storage
        ↓
PHASE 9
Face detection
        ↓
PHASE 10
Face embeddings + matching
        ↓
PHASE 11
Recognition results API
        ↓
PHASE 12
Recognition result UI
        ↓
PHASE 13
Second-photo workflow
        ↓
PHASE 14
Result merging
        ↓
PHASE 15
Teacher review/correction
        ↓
PHASE 16
Attendance finalization
        ↓
PHASE 17
Attendance history
        ↓
PHASE 18
Audit/security hardening
        ↓
PHASE 19
Testing
        ↓
PHASE 20
Deployment
        ↓
PHASE 21
Demo preparation
```

---

# 62. Hackathon Demo Flow

The final demo should be simple and reliable:

```text
1. Teacher logs in
        ↓
2. Selects CSE-A
        ↓
3. Starts attendance
        ↓
4. Uploads class photo
        ↓
5. AI detects multiple students
        ↓
6. Dashboard shows recognized + uncertain faces
        ↓
7. Teacher takes second photo
        ↓
8. Second result resolves uncertain faces
        ↓
9. Results merge
        ↓
10. Teacher reviews/corrects
        ↓
11. Clicks Finalize
        ↓
12. Attendance saved
        ↓
13. Attendance history displayed
```

The demo must not depend on claiming perfect AI accuracy.

---

# 63. Final Engineering Principle

Build the system so that:

```text
Reliable workflow
        >
Perfect AI claim
```

The application should remain useful even when recognition is imperfect.

The strongest product behavior is:

```text
AI recognizes what it can
        ↓
AI clearly reports uncertainty
        ↓
Teacher provides additional evidence
        ↓
Teacher corrects if necessary
        ↓
System records an auditable final decision
```

---

# 64. Pre-Implementation Gate

**NO LARGE-SCALE IMPLEMENTATION SHOULD START UNTIL THIS CHECK PASSES.**

The agent must report:

```text
[ ] PROJECT_SPEC.md read
[ ] Repository inspected
[ ] Existing code understood
[ ] Frontend architecture selected
[ ] Backend architecture selected
[ ] Database design validated
[ ] Authentication selected
[ ] Storage selected
[ ] Face detection selected
[ ] Face embedding model selected
[ ] Matching metric selected
[ ] Matching threshold strategy defined
[ ] API contract defined
[ ] Privacy/security requirements defined
[ ] Deployment target defined
[ ] Environment variables defined
[ ] Testing strategy defined
[ ] Implementation plan created
[ ] Critical ambiguities resolved
```

Only then:

```text
SPECIFICATION STATUS: READY
IMPLEMENTATION STATUS: READY TO START
```

---

# 65. Final Status

This document defines the current product requirements and engineering direction for FaceMark.

Any change to a locked product decision should be documented before implementation.

**Current status:**

```text
Product concept:        DEFINED
Core workflow:          DEFINED
Second-photo workflow:  DEFINED
Frontend scope:         DEFINED
Backend scope:          DEFINED
Database direction:     DEFINED
AI workflow:            DEFINED
Security direction:     DEFINED
Edge cases:             DEFINED
Implementation stack:   TO BE VALIDATED
AI model/threshold:     TO BE VALIDATED
Deployment:             TO BE VALIDATED
```

**Next action:** Validate the unresolved technology and deployment decisions, then create the final implementation plan before coding.