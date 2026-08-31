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
('CSE-101', 'Database Systems', 'Monday', 'DB Lab 2'),
('CSE-204', 'Operating Systems', 'Tuesday', 'OS Lab 1'),
('INT-345', 'Object Oriented Programming', 'Wednesday', 'Room 305'),
('CSE-220', 'Data Structures', 'Thursday', 'Room 210'),
('NET-412', 'Computer Networks', 'Friday', 'Room 412')
ON CONFLICT (subject_id) DO NOTHING;

INSERT INTO section_subjects (section_id, subject_id) VALUES
('sec-cse-a', 'CSE-101'),
('sec-cse-a', 'CSE-204'),
('sec-cse-a', 'INT-345'),
('sec-cse-a', 'CSE-220'),
('sec-cse-a', 'NET-412')
ON CONFLICT (section_id, subject_id) DO NOTHING;
