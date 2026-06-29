-- Runs automatically on first startup of the Postgres container.
-- Creates the same schema you built manually in Phase 1.

-- ============ USERS ============
CREATE TABLE IF NOT EXISTS users (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email         VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============ LINKS ============
CREATE TABLE IF NOT EXISTS links (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    original_url TEXT NOT NULL,
    short_code   VARCHAR(20) UNIQUE NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    is_active    BOOLEAN NOT NULL DEFAULT TRUE
);

-- ============ CLICKS ============
CREATE TABLE IF NOT EXISTS clicks (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    link_id     UUID NOT NULL REFERENCES links(id) ON DELETE CASCADE,
    clicked_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    country     VARCHAR(2),
    device_type VARCHAR(20),
    referrer    TEXT,
    ip_address  INET
);

-- Helpful indexes for common lookups
CREATE INDEX IF NOT EXISTS idx_links_user_id ON links(user_id);
CREATE INDEX IF NOT EXISTS idx_clicks_link_id ON clicks(link_id);

-- A seed user so you can create links immediately after startup.
INSERT INTO users (email, password_hash)
VALUES ('test@linkpulse.io', 'hashed_password_placeholder')
ON CONFLICT (email) DO NOTHING;
