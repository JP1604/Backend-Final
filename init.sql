-- ============================================
-- Online Judge Platform - Complete Database Setup
-- Version: 2.0 (With Course and Exam System)
-- ============================================

-- Create database if not exists
SELECT 'CREATE DATABASE online_judge'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'online_judge')\gexec

-- Use the database
\c online_judge;

-- ============================================
-- CORE TABLES
-- ============================================

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'STUDENT',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Challenges table
CREATE TABLE IF NOT EXISTS challenges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    difficulty VARCHAR(20) NOT NULL,
    tags TEXT[] NOT NULL,
    time_limit INTEGER NOT NULL,
    memory_limit INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    created_by UUID NOT NULL REFERENCES users(id),
    course_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Test cases table
CREATE TABLE IF NOT EXISTS test_cases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    challenge_id UUID NOT NULL REFERENCES challenges(id) ON DELETE CASCADE,
    input TEXT NOT NULL,
    expected_output TEXT NOT NULL,
    is_hidden BOOLEAN DEFAULT FALSE,
    order_index INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Submissions table
CREATE TABLE IF NOT EXISTS submissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    challenge_id UUID NOT NULL REFERENCES challenges(id),
    language VARCHAR(20) NOT NULL,
    code TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'QUEUED',
    score INTEGER DEFAULT 0,
    time_ms_total INTEGER DEFAULT 0,
    cases JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- COURSE SYSTEM TABLES
-- ============================================

-- Courses table
CREATE TABLE IF NOT EXISTS courses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    teacher_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    start_date TIMESTAMP WITH TIME ZONE,
    end_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Course students (many-to-many)
CREATE TABLE IF NOT EXISTS course_students (
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    enrolled_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (course_id, user_id)
);

-- Course challenges (many-to-many)
CREATE TABLE IF NOT EXISTS course_challenges (
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    challenge_id UUID NOT NULL REFERENCES challenges(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    order_index INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (course_id, challenge_id)
);

-- ============================================
-- EXAM SYSTEM TABLES
-- ============================================

-- Exams table
CREATE TABLE IF NOT EXISTS exams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    duration_minutes INTEGER NOT NULL,
    max_attempts INTEGER NOT NULL DEFAULT 1,
    passing_score INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
);

-- Exam challenges (many-to-many with points)
CREATE TABLE IF NOT EXISTS exam_challenges (
    exam_id UUID NOT NULL REFERENCES exams(id) ON DELETE CASCADE,
    challenge_id UUID NOT NULL REFERENCES challenges(id) ON DELETE CASCADE,
    points INTEGER NOT NULL DEFAULT 100,
    order_index INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (exam_id, challenge_id)
);

-- Exam attempts tracking
CREATE TABLE IF NOT EXISTS exam_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    exam_id UUID NOT NULL REFERENCES exams(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    submitted_at TIMESTAMP WITH TIME ZONE,
    score INTEGER NOT NULL DEFAULT 0,
    passed BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- INDEXES FOR PERFORMANCE
-- ============================================

-- Core indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

CREATE INDEX IF NOT EXISTS idx_challenges_status ON challenges(status);
CREATE INDEX IF NOT EXISTS idx_challenges_created_by ON challenges(created_by);
CREATE INDEX IF NOT EXISTS idx_challenges_course_id ON challenges(course_id);

CREATE INDEX IF NOT EXISTS idx_submissions_user_id ON submissions(user_id);
CREATE INDEX IF NOT EXISTS idx_submissions_challenge_id ON submissions(challenge_id);
CREATE INDEX IF NOT EXISTS idx_submissions_status ON submissions(status);

CREATE INDEX IF NOT EXISTS idx_test_cases_challenge_id ON test_cases(challenge_id);

-- Course indexes
CREATE INDEX IF NOT EXISTS idx_courses_teacher ON courses(teacher_id);
CREATE INDEX IF NOT EXISTS idx_courses_status ON courses(status);
CREATE INDEX IF NOT EXISTS idx_course_students_user ON course_students(user_id);
CREATE INDEX IF NOT EXISTS idx_course_students_course ON course_students(course_id);
CREATE INDEX IF NOT EXISTS idx_course_challenges_course ON course_challenges(course_id);
CREATE INDEX IF NOT EXISTS idx_course_challenges_challenge ON course_challenges(challenge_id);

-- Exam indexes
CREATE INDEX IF NOT EXISTS idx_exams_course ON exams(course_id);
CREATE INDEX IF NOT EXISTS idx_exams_status ON exams(status);
CREATE INDEX IF NOT EXISTS idx_exams_start_time ON exams(start_time);
CREATE INDEX IF NOT EXISTS idx_exam_challenges_exam ON exam_challenges(exam_id);
CREATE INDEX IF NOT EXISTS idx_exam_challenges_challenge ON exam_challenges(challenge_id);
CREATE INDEX IF NOT EXISTS idx_exam_attempts_exam ON exam_attempts(exam_id);
CREATE INDEX IF NOT EXISTS idx_exam_attempts_user ON exam_attempts(user_id);
CREATE INDEX IF NOT EXISTS idx_exam_attempts_active ON exam_attempts(is_active);

-- ============================================
-- TRIGGERS FOR AUTO TIMESTAMPS
-- ============================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_users_updated_at ON users;
DROP TRIGGER IF EXISTS update_challenges_updated_at ON challenges;
DROP TRIGGER IF EXISTS update_submissions_updated_at ON submissions;
DROP TRIGGER IF EXISTS update_courses_updated_at ON courses;
DROP TRIGGER IF EXISTS update_exams_updated_at ON exams;
DROP TRIGGER IF EXISTS update_exam_attempts_updated_at ON exam_attempts;

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_challenges_updated_at BEFORE UPDATE ON challenges FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_submissions_updated_at BEFORE UPDATE ON submissions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_courses_updated_at BEFORE UPDATE ON courses FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_exams_updated_at BEFORE UPDATE ON exams FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_exam_attempts_updated_at BEFORE UPDATE ON exam_attempts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- MOCK DATA FOR TESTING
-- ============================================

-- Clear existing data (optional - comment out if you want to keep existing data)
TRUNCATE TABLE exam_attempts, exam_challenges, exams, course_challenges, course_students, courses, submissions, test_cases, challenges, users CASCADE;

-- Insert Users (password = "password" for all)
INSERT INTO users (id, email, password, first_name, last_name, role) VALUES
('00000000-0000-0000-0000-000000000001', 'admin@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/8KzKz2K', 'Admin', 'User', 'ADMIN'),
('00000000-0000-0000-0000-000000000002', 'prof1@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/8KzKz2K', 'Professor', 'Smith', 'PROFESSOR'),
('00000000-0000-0000-0000-000000000003', 'prof2@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/8KzKz2K', 'Professor', 'Johnson', 'PROFESSOR'),
('00000000-0000-0000-0000-000000000011', 'alice@student.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/8KzKz2K', 'Alice', 'Williams', 'STUDENT'),
('00000000-0000-0000-0000-000000000012', 'bob@student.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/8KzKz2K', 'Bob', 'Brown', 'STUDENT'),
('00000000-0000-0000-0000-000000000013', 'charlie@student.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/8KzKz2K', 'Charlie', 'Davis', 'STUDENT'),
('00000000-0000-0000-0000-000000000014', 'diana@student.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/8KzKz2K', 'Diana', 'Miller', 'STUDENT'),
('00000000-0000-0000-0000-000000000015', 'eve@student.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/8KzKz2K', 'Eve', 'Wilson', 'STUDENT')
ON CONFLICT (id) DO NOTHING;

-- Insert Courses
INSERT INTO courses (id, name, description, teacher_id, status, start_date, end_date) VALUES
('10000000-0000-0000-0000-000000000001', 'Data Structures & Algorithms', 'Learn fundamental data structures and algorithms', '00000000-0000-0000-0000-000000000002', 'active', NOW() - INTERVAL '30 days', NOW() + INTERVAL '90 days'),
('10000000-0000-0000-0000-000000000002', 'Advanced Programming', 'Advanced programming concepts and design patterns', '00000000-0000-0000-0000-000000000002', 'active', NOW() - INTERVAL '15 days', NOW() + INTERVAL '75 days'),
('10000000-0000-0000-0000-000000000003', 'Algorithm Design', 'Design and analysis of algorithms', '00000000-0000-0000-0000-000000000003', 'active', NOW() - INTERVAL '20 days', NOW() + INTERVAL '80 days')
ON CONFLICT (id) DO NOTHING;

-- Enroll Students in Courses
INSERT INTO course_students (course_id, user_id) VALUES
-- Data Structures course
('10000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000011'),
('10000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000012'),
('10000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000013'),
('10000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000014'),
-- Advanced Programming course
('10000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000011'),
('10000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000012'),
('10000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000015'),
-- Algorithm Design course
('10000000-0000-0000-0000-000000000003', '00000000-0000-0000-0000-000000000013'),
('10000000-0000-0000-0000-000000000003', '00000000-0000-0000-0000-000000000014'),
('10000000-0000-0000-0000-000000000003', '00000000-0000-0000-0000-000000000015')
ON CONFLICT (course_id, user_id) DO NOTHING;

-- Insert Challenges
INSERT INTO challenges (id, title, description, difficulty, tags, time_limit, memory_limit, status, created_by) VALUES
('20000000-0000-0000-0000-000000000001', 'Two Sum', 'Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.', 'Easy', ARRAY['arrays', 'hashmap'], 1500, 256, 'published', '00000000-0000-0000-0000-000000000002'),
('20000000-0000-0000-0000-000000000002', 'Reverse String', 'Write a function that reverses a string. The input string is given as an array of characters s.', 'Easy', ARRAY['strings', 'two-pointers'], 1000, 128, 'published', '00000000-0000-0000-0000-000000000002'),
('20000000-0000-0000-0000-000000000003', 'Valid Parentheses', 'Given a string s containing just the characters (, ), {, }, [ and ], determine if the input string is valid.', 'Easy', ARRAY['stack', 'strings'], 1500, 256, 'published', '00000000-0000-0000-0000-000000000002'),
('20000000-0000-0000-0000-000000000004', 'Binary Search', 'Given an array of integers nums which is sorted in ascending order, and an integer target, write a function to search target in nums.', 'Easy', ARRAY['binary-search', 'arrays'], 1000, 128, 'published', '00000000-0000-0000-0000-000000000003'),
('20000000-0000-0000-0000-000000000005', 'Merge Sort', 'Implement merge sort algorithm to sort an array of integers.', 'Medium', ARRAY['sorting', 'divide-conquer'], 2000, 512, 'published', '00000000-0000-0000-0000-000000000003')
ON CONFLICT (id) DO NOTHING;

-- Insert Test Cases for Challenges
INSERT INTO test_cases (challenge_id, input, expected_output, is_hidden, order_index) VALUES
-- Two Sum test cases
('20000000-0000-0000-0000-000000000001', '[2,7,11,15]\n9', '[0,1]', false, 1),
('20000000-0000-0000-0000-000000000001', '[3,2,4]\n6', '[1,2]', false, 2),
('20000000-0000-0000-0000-000000000001', '[3,3]\n6', '[0,1]', true, 3),
-- Reverse String test cases
('20000000-0000-0000-0000-000000000002', 'hello', 'olleh', false, 1),
('20000000-0000-0000-0000-000000000002', 'world', 'dlrow', false, 2),
('20000000-0000-0000-0000-000000000002', 'racecar', 'racecar', true, 3),
-- Valid Parentheses test cases
('20000000-0000-0000-0000-000000000003', '()', 'true', false, 1),
('20000000-0000-0000-0000-000000000003', '()[]{}', 'true', false, 2),
('20000000-0000-0000-0000-000000000003', '(]', 'false', false, 3),
('20000000-0000-0000-0000-000000000003', '([)]', 'false', true, 4)
ON CONFLICT DO NOTHING;

-- Assign Challenges to Courses
INSERT INTO course_challenges (course_id, challenge_id, order_index) VALUES
-- Data Structures course
('10000000-0000-0000-0000-000000000001', '20000000-0000-0000-0000-000000000001', 1),
('10000000-0000-0000-0000-000000000001', '20000000-0000-0000-0000-000000000002', 2),
('10000000-0000-0000-0000-000000000001', '20000000-0000-0000-0000-000000000003', 3),
-- Advanced Programming course
('10000000-0000-0000-0000-000000000002', '20000000-0000-0000-0000-000000000003', 1),
('10000000-0000-0000-0000-000000000002', '20000000-0000-0000-0000-000000000005', 2),
-- Algorithm Design course
('10000000-0000-0000-0000-000000000003', '20000000-0000-0000-0000-000000000004', 1),
('10000000-0000-0000-0000-000000000003', '20000000-0000-0000-0000-000000000005', 2)
ON CONFLICT (course_id, challenge_id) DO NOTHING;

-- Insert Sample Submissions
INSERT INTO submissions (id, user_id, challenge_id, language, code, status, score, time_ms_total) VALUES
('30000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000011', '20000000-0000-0000-0000-000000000001', 'python', 'def twoSum(nums, target):\n    return [0, 1]', 'ACCEPTED', 100, 50),
('30000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000012', '20000000-0000-0000-0000-000000000001', 'python', 'def twoSum(nums, target):\n    return [0, 1]', 'ACCEPTED', 100, 75),
('30000000-0000-0000-0000-000000000003', '00000000-0000-0000-0000-000000000013', '20000000-0000-0000-0000-000000000001', 'python', 'def twoSum(nums, target):\n    return [0, 1]', 'WRONG_ANSWER', 66, 100),
('30000000-0000-0000-0000-000000000004', '00000000-0000-0000-0000-000000000011', '20000000-0000-0000-0000-000000000002', 'python', 'def reverseString(s):\n    return s[::-1]', 'ACCEPTED', 100, 30)
ON CONFLICT (id) DO NOTHING;

-- Insert Exams
INSERT INTO exams (id, course_id, title, description, status, start_time, end_time, duration_minutes, max_attempts, passing_score, created_by) VALUES
('40000000-0000-0000-0000-000000000001', '10000000-0000-0000-0000-000000000001', 'Midterm Exam', 'Data Structures Midterm - Arrays and HashMaps', 'active', NOW() - INTERVAL '7 days', NOW() + INTERVAL '7 days', 90, 2, 70, '00000000-0000-0000-0000-000000000002'),
('40000000-0000-0000-0000-000000000002', '10000000-0000-0000-0000-000000000002', 'Final Exam', 'Advanced Programming Final', 'scheduled', NOW() + INTERVAL '30 days', NOW() + INTERVAL '32 days', 120, 1, 75, '00000000-0000-0000-0000-000000000002'),
('40000000-0000-0000-0000-000000000003', '10000000-0000-0000-0000-000000000003', 'Quiz 1', 'Algorithm Design Quiz', 'completed', NOW() - INTERVAL '14 days', NOW() - INTERVAL '13 days', 60, 1, 60, '00000000-0000-0000-0000-000000000003')
ON CONFLICT (id) DO NOTHING;

-- Assign Challenges to Exams
INSERT INTO exam_challenges (exam_id, challenge_id, points, order_index) VALUES
-- Midterm Exam
('40000000-0000-0000-0000-000000000001', '20000000-0000-0000-0000-000000000001', 50, 1),
('40000000-0000-0000-0000-000000000001', '20000000-0000-0000-0000-000000000003', 50, 2),
-- Final Exam
('40000000-0000-0000-0000-000000000002', '20000000-0000-0000-0000-000000000003', 40, 1),
('40000000-0000-0000-0000-000000000002', '20000000-0000-0000-0000-000000000005', 60, 2),
-- Quiz 1
('40000000-0000-0000-0000-000000000003', '20000000-0000-0000-0000-000000000004', 100, 1)
ON CONFLICT (exam_id, challenge_id) DO NOTHING;

-- Insert Exam Attempts
INSERT INTO exam_attempts (id, exam_id, user_id, started_at, submitted_at, score, passed, is_active) VALUES
('50000000-0000-0000-0000-000000000001', '40000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000011', NOW() - INTERVAL '6 days', NOW() - INTERVAL '6 days' + INTERVAL '1 hour', 85, true, false),
('50000000-0000-0000-0000-000000000002', '40000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000012', NOW() - INTERVAL '5 days', NOW() - INTERVAL '5 days' + INTERVAL '1.5 hours', 72, true, false),
('50000000-0000-0000-0000-000000000003', '40000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000013', NOW() - INTERVAL '4 days', NOW() - INTERVAL '4 days' + INTERVAL '2 hours', 65, false, false),
('50000000-0000-0000-0000-000000000004', '40000000-0000-0000-0000-000000000003', '00000000-0000-0000-0000-000000000014', NOW() - INTERVAL '14 days', NOW() - INTERVAL '14 days' + INTERVAL '50 minutes', 80, true, false)
ON CONFLICT (id) DO NOTHING;

-- ============================================
-- SUMMARY REPORT
-- ============================================

SELECT 'Database initialized successfully!' as status;
SELECT COUNT(*) as user_count FROM users;
SELECT COUNT(*) as course_count FROM courses;
SELECT COUNT(*) as challenge_count FROM challenges;
SELECT COUNT(*) as test_case_count FROM test_cases;
SELECT COUNT(*) as enrollment_count FROM course_students;
SELECT COUNT(*) as assignment_count FROM course_challenges;
SELECT COUNT(*) as exam_count FROM exams;
SELECT COUNT(*) as submission_count FROM submissions;
