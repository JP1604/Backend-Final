-- Migration to fix courses table schema
-- This aligns the database schema with the CourseModel in models.py

-- Drop table and recreate with correct schema
DROP TABLE IF EXISTS courses CASCADE;

CREATE TABLE courses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    teacher_id UUID NOT NULL REFERENCES users(id),
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    start_date TIMESTAMP WITH TIME ZONE,
    end_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for teacher_id
CREATE INDEX ix_courses_teacher_id ON courses(teacher_id);

-- Recreate dependent tables that were dropped due to CASCADE

-- Course Students junction table
CREATE TABLE IF NOT EXISTS course_students (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    enrolled_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(course_id, user_id)
);

CREATE INDEX ix_course_students_course_id ON course_students(course_id);
CREATE INDEX ix_course_students_user_id ON course_students(user_id);

-- Course Challenges junction table
CREATE TABLE IF NOT EXISTS course_challenges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    challenge_id UUID NOT NULL REFERENCES challenges(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    due_date TIMESTAMP WITH TIME ZONE,
    UNIQUE(course_id, challenge_id)
);

CREATE INDEX ix_course_challenges_course_id ON course_challenges(course_id);
CREATE INDEX ix_course_challenges_challenge_id ON course_challenges(challenge_id);

-- Recreate exams table foreign key (if needed)
-- Note: The exams table should already exist with the correct schema
-- This is just to ensure the foreign key exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'exams_course_id_fkey'
    ) THEN
        ALTER TABLE exams ADD CONSTRAINT exams_course_id_fkey 
            FOREIGN KEY (course_id) REFERENCES courses(id);
    END IF;
END $$;
