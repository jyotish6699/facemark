FaceMark — Missing Implementation Decisions

Status: Waiting for user answers before implementation.
Rule: No large-scale build starts until these questions are answered and the architecture is validated against PROJECT_SPEC.md.

1) Project and timeline
- Target launch type: [ ] Hackathon demo / [ ] Real product / [ ] Both
- Target users for first version: [ ] Teacher only / [ ] Teacher + Admin / [ ] Teacher + Student
- Expected demo date: ______________________
- Expected total project size: [ ] Small / [ ] Medium / [ ] Large
- Number of classes to support in MVP: ______________________
- Number of students per class: ______________________
- Required local development environment: [ ] Windows / [ ] Mac / [ ] Linux

2) Frontend stack
- Preferred frontend stack: [ ] React + TypeScript + Vite (recommended) / [ ] Next.js / [ ] Another: ______________________
- UI design style: [ ] Simple dashboard / [ ] Modern UI / [ ] Another: ______________________
- Mobile support: [ ] Desktop only / [ ] Responsive web / [ ] Mobile-first
- Should we use a component library? [ ] Yes: ______________________ / [ ] No
- State management: [ ] Context + hooks / [ ] Redux Toolkit / [ ] Zustand / [ ] Another: ______________________

3) Backend stack
- Preferred backend stack: [ ] FastAPI + Python (recommended) / [ ] Node.js + TypeScript / [ ] Django / [ ] Another: ______________________
- API style: [ ] REST (recommended) / [ ] GraphQL / [ ] Another: ______________________
- Is async/background processing required for image recognition? [ ] Yes / [ ] No
- Expected concurrency: ______________________

4) Database and data storage
- Database: [ ] PostgreSQL (recommended) / [ ] Other: ______________________
- Database hosting: [ ] Local Docker / [ ] Supabase / [ ] Railway / [ ] Render / [ ] Fly.io / [ ] AWS / [ ] Azure / [ ] GCP / [ ] Other: ______________________
- Image/object storage: [ ] Local disk / [ ] Supabase Storage / [ ] S3-compatible / [ ] Other: ______________________
- Keep uploaded class photos after finalization? [ ] Yes / [ ] No
- If yes, retention period: ______________________
- Face enrollment retention policy: ______________________

5) Authentication and authorization
- Authentication method: [ ] Email/password / [ ] OAuth / [ ] SSO / [ ] Another: ______________________
- Session strategy: [ ] JWT in secure HTTP-only cookie / [ ] Session-based / [ ] Another: ______________________
- Admin creation workflow: [ ] Manual seed data / [ ] Admin management UI / [ ] Another: ______________________
- Teacher access model: [ ] One teacher -> many classes / [ ] One class -> many teachers / [ ] Both
- Should student login be included in MVP? [ ] Yes / [ ] No

6) Face recognition model decisions
- Face detection library: [ ] OpenCV Haar / [ ] MediaPipe / [ ] InsightFace / [ ] MTCNN / [ ] Another: ______________________
- Face embedding model: [ ] FaceNet / [ ] ArcFace / [ ] VGGFace / [ ] Another: ______________________
- Similarity metric: [ ] Cosine similarity / [ ] Euclidean distance / [ ] Another: ______________________
- Matching threshold policy: [ ] Fixed threshold / [ ] Configurable threshold / [ ] Threshold tuned by dataset
- Suggested threshold value (temporary only): ______________________
- Is a GPU available for model inference? [ ] Yes / [ ] No
- Is a local model acceptable for the demo? [ ] Yes / [ ] No

7) Matching and result handling
- Are we using a second photograph to resolve only uncertain/unknown faces? [ ] Yes / [ ] No
- Should the system automatically mark only confident matches as present during first pass? [ ] Yes / [ ] No
- Should teacher review always be required before finalization? [ ] Yes / [ ] No
- Do we need manual assignment for unknown faces in the UI? [ ] Yes / [ ] No
- Do we need duplicate-photo detection by hash? [ ] Yes / [ ] No
- Should the workflow support reopen/correction after finalization? [ ] Yes / [ ] No

8) Privacy, security, and compliance
- Biometric consent workflow: [ ] Required / [ ] Not needed for demo / [ ] Another: ______________________
- Data retention policy for face embeddings and photos: ______________________
- Who can access face enrollment data? [ ] Admin only / [ ] Teacher only / [ ] Both / [ ] Another: ______________________
- Are there any institution-specific privacy rules we must follow? [ ] Yes: ______________________ / [ ] No
- Do we need audit logging for all manual edits? [ ] Yes / [ ] No

9) Deployment
- Deployment target: [ ] Local Docker / [ ] Vercel / [ ] Render / [ ] Railway / [ ] AWS / [ ] Azure / [ ] GCP / [ ] Other: ______________________
- Frontend deployment target: ______________________
- Backend deployment target: ______________________
- Database deployment target: ______________________
- Storage deployment target: ______________________
- Domain / public URL: ______________________

10) Environment and setup
- Should the project include Docker Compose for local dev? [ ] Yes / [ ] No
- Required operating system for local dev: [ ] Linux / [ ] Mac / [ ] Windows (WSL) / [ ] Any
- Should .env.example be included? [ ] Yes / [ ] No
- Should we include seed data? [ ] Yes / [ ] No
- Should we include test fixtures for face recognition? [ ] Yes / [ ] No

11) Three-phase build plan
- Phase 1 (Frontend): [ ] Required / [ ] Optional
- Phase 2 (Backend + Database): [ ] Required / [ ] Optional
- Phase 3 (AI/Recognition + Integration): [ ] Required / [ ] Optional
- Should frontend be built first even if backend is empty? [ ] Yes / [ ] No
- Should we mock backend APIs during frontend development? [ ] Yes / [ ] No

12) Final required decisions for implementation
- Preferred stack for this project (final): _____________________________________________________
- Final authentication choice: _______________________________________________________________
- Final database and storage choice: ________________________________________________________
- Final recognition model choice: ___________________________________________________________
- Final deployment target: _________________________________________________________________
- Final privacy/retention policy: ___________________________________________________________

Instructions for the user
- Fill in every blank in this file before implementation begins.
- For each question, answer with either a definite value or a clear preference.
- If a requirement is not known yet, write "TBD" and explain what is needed.
- Once filled, send this file back and we will proceed with the implementation in three parts: Frontend first, then Backend + Database, then AI integration and final workflow.
- We will not start large-scale implementation until these answers are confirmed.

Example final completion format:
- Frontend: React + TypeScript + Vite
- Backend: FastAPI + Python
- Database: PostgreSQL
- Storage: Supabase Storage
- Auth: JWT in HTTP-only cookie
- AI: InsightFace + ArcFace
- Deployment: Render + Supabase + local Docker
