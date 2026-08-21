-- =============================================================================
-- Migration: 0004_users_and_auth.sql
-- Description: Core users and credential authentication table (TRADLY_SRS v1.0 §5.1, FG-6)
-- =============================================================================

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(128) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(32) NOT NULL DEFAULT 'authenticated',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);

-- Seed master admin account
INSERT INTO users (id, email, name, hashed_password, role)
VALUES (
    '9dca1422-efd3-4f9f-a96f-b9a34d6b4ccd',
    'princepatel01258@gmail.com',
    'Prince Patel',
    '$pbkdf2-sha256$29000$S2kNQQjhvNd6b.3dm1MqZQ$fQqeEouO7.BVdqa3ebhB4rwlATku3Lv3lxATr2Akq4k',
    'admin'
)
ON CONFLICT (email) DO UPDATE SET
    hashed_password = EXCLUDED.hashed_password,
    role = 'admin',
    name = EXCLUDED.name;
