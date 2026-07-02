from pathlib import Path

from database.db import get_connection, init_db
from services.generate import get_generation


def test_get_generation_returns_saved_record(tmp_path, monkeypatch):
    storage_dir = tmp_path / "storage"
    monkeypatch.setenv("STORAGE_BASE_DIR", str(storage_dir))
    db_path = storage_dir / "gpt-writer.db"
    schema_path = Path(__file__).resolve().parent.parent / "database" / "init.sql"
    init_db(db_path, schema_path)
    conn = get_connection(db_path)
    conn.execute(
        "INSERT INTO styles (id, name, created_at, updated_at) VALUES (?, ?, ?, ?)",
        ("style-1", "Example Style", "2026-06-30T00:00:00+00:00", "2026-06-30T00:00:00+00:00"),
    )
    conn.execute(
        "INSERT INTO generations (id, style_id, prompt, generated_text, provider_used, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        ("existing-id", "style-1", "Write something", "Generated output", "ollama", "2026-06-30T00:00:00+00:00"),
    )
    conn.commit()
    conn.close()

    generation = get_generation("existing-id")

    assert generation["id"] == "existing-id"
