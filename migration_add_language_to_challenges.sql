-- Migration: Add language column to challenges table
-- This migration adds the programming_language column to the challenges table
-- and sets a default value for existing challenges

-- Add language column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'challenges' 
        AND column_name = 'language'
    ) THEN
        -- Add the column with a default value
        ALTER TABLE challenges 
        ADD COLUMN language VARCHAR(20) NOT NULL DEFAULT 'python';
        
        -- Update existing challenges to have python as default
        UPDATE challenges 
        SET language = 'python' 
        WHERE language IS NULL;
        
        RAISE NOTICE 'Column language added to challenges table';
    ELSE
        RAISE NOTICE 'Column language already exists in challenges table';
    END IF;
END $$;

