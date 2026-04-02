-- 005: Add Clerk external ID to users table for OAuth-based auth.
ALTER TABLE users ADD COLUMN IF NOT EXISTS clerk_id TEXT UNIQUE;
ALTER TABLE users ALTER COLUMN email DROP NOT NULL;
CREATE INDEX IF NOT EXISTS idx_users_clerk_id ON users(clerk_id);
