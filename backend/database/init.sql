CREATE TABLE IF NOT EXISTS styles (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    style_id TEXT NOT NULL,
    filename TEXT NOT NULL,
    original_path TEXT NOT NULL,
    extracted_path TEXT NOT NULL,
    content_type TEXT,
    file_size INTEGER,
    created_at TEXT NOT NULL,
    FOREIGN KEY (style_id) REFERENCES styles(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS generations (
    id TEXT PRIMARY KEY,
    style_id TEXT NOT NULL,
    prompt TEXT NOT NULL,
    generated_text TEXT NOT NULL,
    provider_used TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT,
    FOREIGN KEY (style_id) REFERENCES styles(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS writing_samples (
    id TEXT PRIMARY KEY,
    style_id TEXT NOT NULL,
    text TEXT NOT NULL,
    document_type TEXT NOT NULL,
    tone_tags TEXT,
    style_tags TEXT,
    style_description TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (style_id) REFERENCES styles(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_styles_updated ON styles(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_generations_style ON generations(style_id, created_at DESC);
