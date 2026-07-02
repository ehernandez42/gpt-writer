from pathlib import Path

from fastapi.testclient import TestClient

import main
from database.db import get_connection, init_db
from services.styles import SCHEMA_PATH


def seed_generations(tmp_path: Path) -> Path:
    db_path = tmp_path / "gpt-writer.db"
    init_db(db_path, SCHEMA_PATH)
    conn = get_connection(db_path)
    conn.execute(
        "INSERT INTO styles (id, name, created_at, updated_at) VALUES (?, ?, ?, ?)",
        ("style-1", "Test style", "2026-06-30T09:00:00+00:00", "2026-06-30T09:00:00+00:00"),
    )
    conn.execute(
        "INSERT INTO generations (id, style_id, prompt, generated_text, provider_used, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        ("gen-1", "style-1", "First prompt", "First text", "ollama", "2026-06-30T10:00:00+00:00"),
    )
    conn.execute(
        "INSERT INTO generations (id, style_id, prompt, generated_text, provider_used, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        ("gen-2", "style-1", "Second prompt", "Second text", "ollama", "2026-06-30T11:00:00+00:00"),
    )
    conn.commit()
    conn.close()
    return db_path


def test_list_generations_returns_recent_first(tmp_path, monkeypatch):
    seed_generations(tmp_path)
    monkeypatch.setenv("STORAGE_BASE_DIR", str(tmp_path))
    client = TestClient(main.app)

    response = client.get("/generations")

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == ["gen-2", "gen-1"]


def test_patch_generation_updates_text_and_updated_at(tmp_path, monkeypatch):
    db_path = seed_generations(tmp_path)
    monkeypatch.setenv("STORAGE_BASE_DIR", str(tmp_path))
    client = TestClient(main.app)

    response = client.patch("/generations/gen-1", json={"generated_text": "Updated text"})

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == "gen-1"
    assert body["generated_text"] == "Updated text"
    assert body["updated_at"]

    conn = get_connection(db_path)
    row = conn.execute(
        "SELECT generated_text, updated_at FROM generations WHERE id = ?",
        ("gen-1",),
    ).fetchone()
    conn.close()

    assert row["generated_text"] == "Updated text"
    assert row["updated_at"]
