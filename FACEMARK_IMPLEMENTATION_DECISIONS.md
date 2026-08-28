# FaceMark — Missing Implementation Decisions
## Final Answers for Hackathon Demo

**Status:** Confirmed for hackathon implementation  
**Priority:** Complete, stable end-to-end web demo by tomorrow  
**Core rule:** Do not over-engineer. Build the complete workflow first.

---

## 1) Project and timeline

- Target launch type: **Hackathon demo**
- Target users for first version: **Teacher + Admin**
- Expected demo date: **Tomorrow**
- Expected total project size: **Medium**
- Number of classes to support in MVP: **1–3**
- Number of students per class: **30–60**
- Required local development environment: **Linux**

---

## 2) Frontend stack

- Preferred frontend stack: **HTML + CSS + JavaScript (plain frontend, no React/Vite framework)**
- UI design style: **Modern UI**
- Mobile support: **Responsive web**
- Should we use a component library?: **No**
- State management: **Plain JavaScript modules + local state**

### Important clarification

This is a **simple web application** built with standard HTML, CSS, and JavaScript.

The teacher will use the web application in a browser and upload classroom photographs through the web interface.

No React, Next.js, or other frontend framework is required for the MVP.

This choice keeps the project simpler, faster, and more suitable for a hackathon demo.

---

## 3) Backend stack

- Preferred backend stack: **FastAPI + Python**
- API style: **REST**
- Is async/background processing required for image recognition?: **Yes**
- Expected concurrency: **Low — approximately 1–5 simultaneous users for the demo**

Use a simple background-processing approach. Do not introduce unnecessary distributed infrastructure.

---

## 4) Database and data storage

- Database: **PostgreSQL**
- Database hosting: **Supabase**
- Image/object storage: **Supabase Storage**
- Keep uploaded class photos after finalization?: **No**
- If yes, retention period: **N/A**
- Face enrollment retention policy: **Keep enrollment data for the duration of the demo/project; provide deletion capability for enrolled student data**

### Architecture

```text
HTML + CSS + JS Frontend
      ↓
FastAPI Backend
      ↓
Supabase PostgreSQL
      +
Supabase Storage
```

Face recognition runs locally through the backend.

---

## 5) Authentication and authorization

- Authentication method: **Email/password**
- Session strategy: **JWT in secure HTTP-only cookie**
- Admin creation workflow: **Manual seed data**
- Teacher access model: **One teacher → many classes**
- Should student login be included in MVP?: **No**

### MVP roles

```text
Admin
 ├── Manage students
 ├── Manage classes
 └── Assign teachers

Teacher
 ├── Select class
 ├── Start attendance
 ├── Upload classroom photo
 ├── Review recognition
 ├── Upload second photo when required
 ├── Correct results
 └── Finalize attendance
```

No student portal is required for the hackathon MVP.

---

## 6) Face recognition model decisions

- Face detection library: **InsightFace**
- Face embedding model: **ArcFace**
- Similarity metric: **Cosine similarity**
- Matching threshold policy: **Threshold tuned by dataset**
- Suggested threshold value (temporary only): **Start around 0.40–0.50 cosine similarity and validate using the actual enrollment/demo images**
- Is a GPU available for model inference?: **No**
- Is a local model acceptable for the demo?: **Yes**

### Important threshold rule

Do not assume that one threshold is universally correct.

The implementation must test the selected model with representative demo images and tune the threshold accordingly.

The threshold should be documented and configurable where practical.

### Recognition pipeline

```text
Class Photo
    ↓
InsightFace Face Detection
    ↓
Face Preprocessing/Alignment
    ↓
ArcFace Embedding
    ↓
Compare with selected-class student embeddings
    ↓
Cosine Similarity
    ↓
Threshold Policy
    ↓
CONFIDENT_MATCH / UNCERTAIN / UNKNOWN
```

Only students belonging to the selected class should be considered as recognition candidates.

---

## 7) Matching and result handling

- Are we using a second photograph to resolve only uncertain/unknown faces?: **Yes**
- Should the system automatically mark only confident matches as present during first pass?: **Yes**
- Should teacher review always be required before finalization?: **Yes**
- Do we need manual assignment for unknown faces in the UI?: **Yes**
- Do we need duplicate-photo detection by hash?: **No**
- Should the workflow support reopen/correction after finalization?: **No**

### Exact attendance workflow

```text
FIRST PHOTO
     ↓
Detect faces
     ↓
Recognize faces
     ↓
Confident matches → Present candidate
Uncertain matches → Review
Unknown faces     → Review
Not detected      → Not detected
     ↓
Teacher sees results
     ↓
Uncertain/unknown?
     ↓
YES
     ↓
SECOND PHOTO
     ↓
Recognize again
     ↓
Merge with first results
     ↓
Teacher review
     ↓
Manual correction if required
     ↓
FINALIZE ATTENDANCE
```

### Critical rule

**NOT_DETECTED ≠ ABSENT**

A student who was not detected must not automatically be marked absent.

The teacher makes the final attendance decision.

---

## 8) Privacy, security, and compliance

- Biometric consent workflow: **Required — simple demo consent/acknowledgment**
- Data retention policy for face embeddings and photos: **Enrollment embeddings retained for the demo/project; attendance photos deleted after processing/finalization unless explicitly retained for debugging/demo**
- Who can access face enrollment data?: **Admin only**
- Are there any institution-specific privacy rules we must follow?: **No**
- Do we need audit logging for all manual edits?: **Yes**

### Minimum security requirements

- HTTPS in production/deployed environments
- Secure authentication
- Backend authorization
- No secrets in source code
- No biometric embeddings in logs
- No unnecessary exposure of enrollment images
- Audit manual attendance changes
- Validate uploaded files
- Protect stored images and biometric data

---

## 9) Deployment

- Deployment target: **Local Docker**
- Frontend deployment target: **Local Docker**
- Backend deployment target: **Local Docker**
- Database deployment target: **Supabase PostgreSQL**
- Storage deployment target: **Supabase Storage**
- Domain / public URL: **TBD / not required for MVP demo**

### Demo architecture

```text
Browser
   ↓
Frontend Container
   ↓
FastAPI Backend Container
   ├── Local InsightFace/ArcFace
   ├── Supabase PostgreSQL
   └── Supabase Storage
```

Do not spend hackathon time building complicated cloud infrastructure.

---

## 10) Environment and setup

- Should the project include Docker Compose for local dev?: **Yes**
- Required operating system for local dev: **Linux**
- Should .env.example be included?: **Yes**
- Should we include seed data?: **Yes**
- Should we include test fixtures for face recognition?: **Yes**

### Seed data

Provide demo-ready seed data such as:

```text
Admin
Teacher
Class: CSE-A
30–40 students
Student enrollment face data
```

The demo must not require manually registering dozens of students immediately before the presentation.

---

## 11) Three-phase build plan

- Phase 1 (Frontend): **Required**
- Phase 2 (Backend + Database): **Required**
- Phase 3 (AI/Recognition + Integration): **Required**
- Should frontend be built first even if backend is empty?: **No**
- Should we mock backend APIs during frontend development?: **No**

### Build strategy

Do NOT build:

```text
Frontend 100%
      ↓
Backend 100%
      ↓
AI 100%
```

Instead, build the complete end-to-end workflow as early as possible:

```text
Database
   ↓
Backend
   ↓
AI
   ↓
Frontend
   ↓
Integration
   ↓
Complete working demo
```

---

# 12) Final required decisions

- Preferred stack for this project (final):

**HTML + CSS + JavaScript + FastAPI + Python + PostgreSQL**

- Final authentication choice:

**Email/password with JWT stored in secure HTTP-only cookie**

- Final database and storage choice:

**Supabase PostgreSQL + Supabase Storage**

- Final recognition model choice:

**InsightFace with ArcFace embeddings, local CPU inference**

- Final deployment target:

**Local Docker Compose for the demo, with Supabase PostgreSQL and Supabase Storage**

- Final privacy/retention policy:

**Admin-only biometric enrollment access; embeddings retained for the demo/project; uploaded attendance photos deleted after processing/finalization unless explicitly retained for debugging/demo; teacher changes are audit logged.**

---

# 13) Hackathon Priority

This project is being built for a **hackathon demo tomorrow**.

Priority order:

1. Complete end-to-end working demo
2. Recognition reliability on controlled demo images
3. Clean and convincing UI/UX
4. Correct attendance workflow
5. Basic security and privacy
6. Testing of critical functionality
7. Production scalability

### Do NOT over-engineer the MVP.

Do NOT introduce:

- Microservices
- Kubernetes
- Complex event systems
- Distributed queues
- Production-scale infrastructure
- Unnecessary cloud services

unless a real technical requirement makes them necessary.

---

# 14) Required complete demo workflow

The application must demonstrate:

```text
Login
  ↓
Class selection
  ↓
Attendance session
  ↓
Image upload through web browser
  ↓
Face detection
  ↓
Face recognition
  ↓
Confident / uncertain / unknown results
  ↓
Second photograph for uncertain/unknown faces
  ↓
Result merging
  ↓
Teacher review
  ↓
Manual correction if required
  ↓
Attendance finalization
  ↓
Attendance history
```

The project is a **web-based application**.

There is **NO native mobile application** in this MVP.

---

# 15) Photo-taking assumptions

The teacher is responsible for taking a suitable classroom photograph.

Before taking the photograph, the teacher should ensure:

- Everyone is inside the frame.
- Students who are too small/far away move into a better position.
- Faces are sufficiently visible.
- The camera/phone has adequate image quality.
- Lighting is reasonably good.

The system does not need to solve every extreme photography condition for the hackathon MVP.

If the first image produces uncertain/unknown faces, the teacher takes another photograph.

---

# 16) Second-photo rule

The second photograph is specifically used to improve unresolved recognition.

Example:

```text
Photo 1

Rahul → 97% → Confident
Aman  → 95% → Confident
Priya → 63% → Uncertain
```

Teacher takes Photo 2.

```text
Photo 2

Priya → 94% → Confident
```

Merged result:

```text
Rahul → Present
Aman  → Present
Priya → Present
```

The second photograph does **not** replace the first photograph.

A student recognized in both photographs is still counted only once.

---

# 17) Teacher final authority

AI recognition is a recommendation/candidate result.

The teacher must be able to:

- Confirm a recognized student
- Correct an incorrect match
- Assign an unknown face to a student
- Mark a student present
- Mark a student absent
- Resolve uncertain results

The final attendance record is based on the teacher-confirmed result.

---

# 18) Agent pre-implementation gate

Before large-scale implementation, the coding agent MUST:

1. Read `PROJECT_SPEC.md`.
2. Read this decision document.
3. Inspect the complete repository.
4. Check existing code and configuration.
5. Validate the proposed architecture against the specification.
6. Identify genuinely blocking missing information.
7. Confirm the selected frontend/backend/database/AI architecture.
8. Confirm the development and deployment approach.
9. Create an implementation plan.
10. Start implementation only when no critical decision is unresolved.

### The agent must NOT:

- Guess major requirements.
- Replace selected technologies without explanation.
- Build only the frontend.
- Build only a mock AI workflow.
- Automatically convert unknown/not-detected students into absent.
- Add unnecessary production infrastructure.
- Store secrets in source control.
- Claim AI accuracy without testing.

---

# 19) Definition of Done

The hackathon MVP is done when a teacher can successfully demonstrate:

```text
1. Login
2. Select class
3. Start attendance
4. Upload a real classroom image
5. Detect multiple faces
6. Recognize enrolled students
7. See confident matches
8. See uncertain/unknown faces
9. Upload a second image
10. Merge recognition results
11. Correct a result manually
12. Finalize attendance
13. See saved attendance history
```

The entire workflow must work using the real frontend, real backend, real database, and real face-recognition pipeline.

---

# 20) Final implementation instruction

**Build FaceMark as a complete hackathon-ready web application, not as disconnected prototypes.**

The primary objective is:

> **A teacher uploads one classroom photograph, FaceMark recognizes as many students as possible, clearly identifies uncertain/unknown faces, allows a second photograph to resolve them, lets the teacher verify/correct the results, and saves the final attendance.**

Keep the architecture simple, reliable, understandable, and demo-ready.