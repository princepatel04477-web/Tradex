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

-- Insert default demo account if not exists
INSERT INTO users (id, email, name, hashed_password, role)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    'demo@tradly.ai',
    'Demo Trader',
    '$pbkdf2-sha256$29000$j5sK.H4b9q2xN8/0lZ3m7Q$XfR9gY2m6Wp0Vq7K8j1Z.Qe3L4u9P8s7D6a5C4b3A2',
    'authenticated'
)
ON CONFLICT (email) DO NOTHING;
