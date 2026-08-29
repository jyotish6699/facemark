INSERT INTO sections (section_id, section_name, department, semester, academic_year)
VALUES ('sec-cse-a', 'CSE-A', 'Computer Science', '5th', '2026-2027')
ON CONFLICT (section_id) DO NOTHING;

INSERT INTO teachers (teacher_id, name, email, password_hash, role, assigned_section_id)
VALUES (
  't-001',
  'Ayesha Khan',
  'ayesha.khan@facemark.local',
  '$2b$12$demoHashForTeacherAyesha123',
  'teacher',
  'sec-cse-a'
)
ON CONFLICT (teacher_id) DO NOTHING;

INSERT INTO subjects (subject_id, subject_name, schedule_day, room) VALUES
('sub-101', 'Database Systems', 'Monday', 'DB Lab 2'),
('sub-102', 'Operating Systems', 'Tuesday', 'OS Lab 1'),
('sub-103', 'Object Oriented Programming', 'Wednesday', 'Room 305'),
('sub-104', 'Data Structures', 'Thursday', 'Room 210'),
('sub-105', 'Computer Networks', 'Friday', 'Room 412')
ON CONFLICT (subject_id) DO NOTHING;

INSERT INTO section_subjects (section_id, subject_id) VALUES
('sec-cse-a', 'sub-101'),
('sec-cse-a', 'sub-102'),
('sec-cse-a', 'sub-103'),
('sec-cse-a', 'sub-104'),
('sec-cse-a', 'sub-105')
ON CONFLICT (section_id, subject_id) DO NOTHING;
