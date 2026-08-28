# FaceMark Workflow, Features, and Decisions

## 1. Product summary

FaceMark is a classroom attendance system where a teacher uploads a classroom photo, the backend detects faces, matches them against students in the selected class, and the teacher reviews the recognition results before final attendance is submitted.

The core product rule is:

AI performs repetitive recognition; the teacher makes the final attendance decision.

This project is built for a hackathon demo and prioritizes a reliable end-to-end workflow over perfect AI performance.

---

## 2. Final decisions that were resolved

### Frontend
- Frontend stack: HTML + CSS + JavaScript
- No React/Vite/Next.js for this MVP
- Responsive web app for desktop and mobile browser use
- Plain JavaScript state management, no framework needed

### Backend
- Backend stack: FastAPI + Python
- API style: REST
- Async/background processing: Yes
- Demo concurrency: low, about 1–5 simultaneous users

### Database and storage
- Database: PostgreSQL via Supabase
- Storage: Supabase Storage
- Attendance photos are not kept after finalization for the demo
- Enrollment data is retained for the demo/project and can be deleted if required

### Authentication
- Method: Email/password
- Session: JWT stored in secure HTTP-only cookie
- Admin seed data is used for the MVP
- Teacher can manage many classes, but not student portal in this demo

### Face recognition
- Face detection: InsightFace
- Embedding model: ArcFace
- Similarity metric: cosine similarity
- Threshold: configurable, tuned using actual demo images
- Local CPU inference is acceptable for demo

### Deployment
- Local Docker Compose for the demo
- Supabase PostgreSQL + Supabase Storage for data and files
- No production-scale infrastructure for the hackathon

### Privacy/security
- Biometric consent is required as a simple demo acknowledgment
- Admin-only enrollment access
- Teacher manual edits are audit logged
- No embeddings or raw sensitive values are logged
- Attendance photos are deleted after processing/finalization unless explicitly retained for debugging/demo

---

## 3. Full working workflow of the application

### Step 1: Teacher login
- Teacher opens the web app
- Teacher enters email and password
- Frontend verifies valid input and logs in to the dashboard

### Step 2: Teacher dashboard
- Teacher sees assigned classes
- Teacher sees recent attendance sessions
- Teacher can start a new attendance workflow

### Step 3: Class selection
- Teacher chooses the target class
- Example: CSE-A, Operating Systems
- The class is selected before attendance begins

### Step 4: Attendance session creation
- Teacher starts an attendance session
- Session details include:
  - class name
  - subject
  - date
  - student count
- The app enters a session state ready for photo upload

### Step 5: Photo upload
- Teacher selects a classroom image from the browser
- It is uploaded to the frontend demo workflow
- The app displays a processing state

### Step 6: First recognition pass
- The app simulates detection of multiple faces in the classroom photo
- It groups results into:
  - confidently recognized students
  - uncertain matches needing review
  - unknown faces
  - not detected students
- This matches the product requirement: the system should clearly separate confident, uncertain, unknown, and not-detected states

### Step 7: Second photo workflow
- If the teacher sees uncertain or unknown faces, they can take another photo
- The second photo is not a replacement for the first result
- It is used to resolve missing or weak recognition evidence
- The second photo is merged with the first result

### Step 8: Merge logic
- The app keeps the first photo as the base result
- It supplements or resolves uncertain/unknown students with the second photo
- Duplicate student recognition does not create a second attendance count

### Step 9: Teacher review and correction
- Teacher sees every student with recognition status and final status
- The teacher can:
  - confirm present students
  - change a result to absent
  - keep something under review
  - mark unknown or uncertain students manually when needed
- This is the required teacher authority stage before finalization

### Step 10: Final attendance freeze
- Teacher clicks finalize attendance
- The final attendance session is treated as complete
- No additional normal photo uploads are allowed for the session in the final-product logic

### Step 11: Attendance history
- Teacher can view recent finalized attendance records
- The UI shows counts, session date, class, and subject

---

## 4. Features implemented in the frontend demo

### Login screen
- Email field
- Password field
- Demo login flow
- Validation for input
- Error state for invalid credentials

### Teacher dashboard
- Assigned classes overview
- KPI cards
- Recent sessions list
- Quick start attendance action

### Class selection
- Class cards for multiple classes
- Selected class highlight
- Start attendance session button

### Attendance setup
- Selected class summary
- Subject field
- Date field
- Continue button to photo upload

### Upload workflow
- Upload area with image guidance
- Image file selection
- Simulated processing state
- Demo recognition trigger

### Recognition review screen
- Confidently recognized list
- Uncertain/needs-review list
- Unknown face list
- Not detected list
- Clear grouping for teacher action

### Second photo flow
- Separate screen for resolving uncertain/unknown faces
- second photo upload area
- merge mindset and flow description

### Final review table
- Every class student is shown
- Recognition status
- Final status dropdown
- Confirm button for each row
- Finalize button

### Attendance history
- Recent list of sessions
- Class, subject, date, and counts displayed

---

## 5. Benefits of the workflow

### For teachers
- Faster attendance than manual roll calls
- Clear visual separation between confident and uncertain results
- Reduces repeated classroom effort
- Gives teacher final authority instead of fully automated decisions

### For the classroom
- Less disruption to teaching time
- Cleaner and quicker attendance handling
- More reliable than manual counting with large classes

### For the product
- Clear AI-human workflow
- Better trust because uncertain cases are visible and reviewable
- Prevents silent false absences from unrecognized faces
- Keeps final attendance under human approval

### For hackathon demo quality
- Demo is understandable to judges and users
- End-to-end visible flow from login to history
- Easy to explain in a short presentation

---

## 6. Questions answered and solved

This project resolved the key implementation questions before the backend began:

- Frontend should be plain HTML + CSS + JavaScript
- Backend should be FastAPI + Python
- Database uses Supabase PostgreSQL
- Object storage uses Supabase Storage
- Authentication is email/password with JWT in HTTP-only cookie
- Local CPU inference is acceptable for demo
- Recognition model uses InsightFace + ArcFace
- Similarity metric is cosine similarity
- Demo deployment target is local Docker Compose + Supabase services
- Student portal is not required for the MVP
- Admin and teacher roles are enough for the first version
- Second photo is meant to resolve uncertain/unknown results only
- Teacher review is always required before finalization
- Attendance photos are not retained after processing/finalization in the demo
- Manual changes are audit logged

---

## 7. Scope status

### Completed in this session
- Project specification read
- Architecture decisions confirmed
- Frontend UI built for the full demo flow
- Local static app served at http://localhost:8000
- Frontend committed and pushed to GitHub

### Not started yet
- FastAPI backend
- PostgreSQL schema and migrations
- Supabase integration
- Authentication APIs
- Real file upload API
- Real face detection and recognition
- Final backend attendance persistence

---

## 8. Current stop point for backend continuation

The implementation is currently paused after the complete frontend prototype. The exact stop point is:

Frontend is complete and working locally. The static demo UI supports the entire teacher workflow, but it is not connected to a real backend or real face-recognition pipeline yet.

The next phase must start from the architecture and decisions in this document, then build:

1. backend foundation
2. database schema and migrations
3. auth and authorization
4. student/class management
5. enrollment flow
6. upload API
7. face detection and recognition
8. attendance session logic
9. result merging
10. review and finalization
11. history and audit logic

---

## 9. Important implementation notes for the next agent

- Do not replace the UI workflow with a different logical flow
- Keep the same teacher-first attendance model
- Do not silently convert unknown or not-detected to absent
- Require teacher review before finalization
- Keep candidate matching limited to the selected class
- Use Supabase PostgreSQL and Supabase Storage for real backend integration
- The frontend is a mock-only prototype until the real backend is introduced

---

## 10. Final status

Status: Frontend complete for demo.
Backend not started.
This project is ready for the next phase of backend implementation using the architecture decisions and workflow described above.
