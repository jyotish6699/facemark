# FaceMark

FaceMark is a hackathon-ready classroom attendance system that helps teachers quickly identify students from a classroom photo, review uncertain matches, and finalize attendance with teacher approval.

The product workflow is intentionally simple and reliable:

1. Teacher logs in
2. Selects a class and session
3. Uploads a classroom photo
4. Backend detects multiple faces
5. AI matches detected faces against enrolled students in that class
6. Teacher reviews confidently recognized, uncertain, and unknown results
7. Teacher can upload a second photo to resolve uncertain/unknown cases
8. Results are merged without duplicate counting
9. Teacher reviews and finalizes attendance
10. Attendance history is available for the selected class

## Project purpose

This project follows the core product principle from the project specification:

AI performs repetitive recognition; the teacher makes the final attendance decision.

FaceMark is designed to reduce manual attendance effort while keeping teacher oversight central.

## Core workflow

```text
Login
  ↓
Select class
  ↓
Start attendance session
  ↓
Upload class photo
  ↓
Face detection & recognition
  ↓
Review confident / uncertain / unknown results
  ↓
Take second photo for unresolved cases
  ↓
Merge results with first pass
  ↓
Teacher review and corrections
  ↓
Finalize attendance
  ↓
View attendance history
```

## Key rules

- The system only compares detected faces against students in the selected class.
- A student is counted only once in one attendance session.
- Uncertain and unknown results are shown to the teacher for review.
- Not detected is not treated as absent automatically.
- Teacher final review is required before attendance is finalized.
- Manual corrections are auditable.

## Tech stack

### Frontend
- HTML
- CSS
- JavaScript
- Responsive web UI
- No frontend framework required for this hackathon MVP

### Backend
- FastAPI
- Python
- REST API
- Background processing for recognition tasks

### Database and storage
- PostgreSQL via Supabase
- Supabase Storage for uploaded images

### Face recognition
- InsightFace for face detection
- ArcFace embeddings
- Cosine similarity matching
- Local CPU inference for the demo

## Demo architecture

```text
Browser
  ↓
HTML + CSS + JS Frontend
  ↓
FastAPI Backend
  ├── Face detection + recognition pipeline
  ├── PostgreSQL (Supabase)
  └── Supabase Storage
```

## MVP scope

This project is built for a hackathon demo and supports:

- Admin management for classes and students
- Teacher login and class assignment
- Attendance session creation
- Photo upload from browser
- Face detection and recognition
- Multi-face handling in class images
- Review of confident, uncertain, and unknown matches
- Second-photo workflow for unresolved cases
- Result merging
- Teacher correction and final attendance
- Attendance history

## Repository structure

```text
facemark/
├── PROJECT_SPEC.md
├── FACEMARK_IMPLEMENTATION_DECISIONS.md
├── README.md
├── frontend/
├── backend/
├── database/
├── docs/
├── tests/
├── docker-compose.yml
├── .env.example
├── .gitignore
└── ...
```

## Local development plan

The repo is intended to be run locally with Docker Compose for the demo environment, while PostgreSQL and object storage use Supabase-managed services.

### Requirements
- Linux environment
- Docker and Docker Compose
- Python 3.11+
- A browser for the frontend
- Access to Supabase project credentials

### Environment variables

A `.env.example` file will be created during implementation with placeholders for:
- database URL
- Supabase URL
- Supabase keys
- JWT secret
- file storage config
- recognition threshold settings

## Security and privacy

The implementation follows the project specification requirements:

- Secure authentication
- Role-based authorization
- No secrets stored in source code
- No biometric embeddings logged
- Enrollment data restricted to admin access
- Uploaded attendance photos deleted after processing/finalization unless retained for debugging/demo
- Audit logging for teacher attendance changes

## Demo priority

This app is optimized for a reliable demo experience rather than production-scale complexity.

Priority order:
1. End-to-end working demo
2. Recognition quality on demo images
3. Convincing UI/UX
4. Correct workflow and finalization
5. Basic security and privacy

## Notes

This repository contains the project specification and architecture decisions before implementation begins.

The next steps are:
1. Frontend implementation
2. Backend and database implementation
3. Face recognition and final workflow integration

## License

This project is for hackathon/demo use unless otherwise specified.
