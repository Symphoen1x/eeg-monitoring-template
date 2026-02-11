-- Migration: Add OAuth support to users table
-- Description: Add OAuth provider fields and make hashed_password nullable
-- Created: 2026-01-28

-- Add new OAuth columns
ALTER TABLE users
ADD COLUMN oauth_provider VARCHAR(50),
ADD COLUMN google_id VARCHAR(255) UNIQUE,
ADD COLUMN profile_picture VARCHAR(500);

-- Make hashed_password nullable for OAuth users
ALTER TABLE users
ALTER COLUMN hashed_password DROP NOT NULL;

-- Create index on google_id for faster lookups
CREATE INDEX idx_users_google_id ON users(google_id);

-- Add comments for documentation
COMMENT ON COLUMN users.oauth_provider IS 'OAuth provider name (google, github, etc.)';
COMMENT ON COLUMN users.google_id IS 'Unique Google user ID from OAuth';
COMMENT ON COLUMN users.profile_picture IS 'Profile picture URL from OAuth provider';
