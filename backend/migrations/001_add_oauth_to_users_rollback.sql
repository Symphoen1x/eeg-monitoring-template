-- Rollback Migration: Remove OAuth support from users table
-- Description: Reverse the OAuth changes
-- Created: 2026-01-28

-- Drop OAuth columns
ALTER TABLE users
DROP COLUMN IF EXISTS oauth_provider,
DROP COLUMN IF EXISTS google_id,
DROP COLUMN IF EXISTS profile_picture;

-- Make hashed_password NOT NULL again
-- WARNING: This will fail if there are users with NULL passwords (OAuth users)
-- ALTER TABLE users ALTER COLUMN hashed_password SET NOT NULL;

-- Drop index
DROP INDEX IF EXISTS idx_users_google_id;
