-- Adds the custom_slug column + a unique index for fast redirect lookups.
ALTER TABLE links ADD COLUMN IF NOT EXISTS custom_slug VARCHAR(50);
CREATE UNIQUE INDEX IF NOT EXISTS uq_links_custom_slug ON links(custom_slug);
