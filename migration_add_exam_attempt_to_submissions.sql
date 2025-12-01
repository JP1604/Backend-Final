-- Migration: Add exam_attempt_id to submissions table
-- This links submissions to exam attempts when submitted during an exam

ALTER TABLE submissions 
ADD COLUMN IF NOT EXISTS exam_attempt_id UUID REFERENCES exam_attempts(id);

CREATE INDEX IF NOT EXISTS idx_submissions_exam_attempt_id ON submissions(exam_attempt_id);

