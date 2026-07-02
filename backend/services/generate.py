from datetime import UTC, datetime
from pathlib import Path
import os
import uuid

# from database.db import get_connection, init_db
from providers.registry import get_provider_chain
from storage.factory import get_storage

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "database" / "init.sql"


def _db_path() -> Path:
    return Path(os.getenv("STORAGE_BASE_DIR", "./storage")) / "gpt-writer.db"


def build_messages(style_text: str, prompt: str) -> list[dict[str, str]]:
    system = f"""You are a writing assistant. The user has provided sample documents
that demonstrate the writing style they want you to emulate. Study the style:
tone, structure, vocabulary, sentence patterns, formatting conventions.

Write new content that matches this style while answering the user's request.

<STYLE_REFERENCE>
{style_text}
</STYLE_REFERENCE>"""
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": prompt},
    ]


async def generate_text(style_id: str, prompt: str) -> dict:
    storage = get_storage()
    db_path = _db_path()
    init_db(db_path, SCHEMA_PATH)
    conn = get_connection(db_path)
    style_text = storage.get_file(f"extracted/{style_id}.combined.txt").decode("utf-8")
    messages = build_messages(style_text, prompt)

    for provider in get_provider_chain():
        if await provider.is_available():
            try:
                text = await provider.generate(messages)
                generation_id = str(uuid.uuid4())
                created_at = datetime.now(UTC).isoformat()
                conn.execute(
                    "INSERT INTO generations (id, style_id, prompt, generated_text, provider_used, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (generation_id, style_id, prompt, text, provider.name, created_at, created_at),
                )
                conn.commit()
                conn.close()
                return {
                    "id": generation_id,
                    "generation_id": generation_id,
                    "style_id": style_id,
                    "prompt": prompt,
                    "generated_text": text,
                    "text": text,
                    "provider_used": provider.name,
                    "created_at": created_at,
                    "updated_at": created_at,
                }
            except Exception:
                continue

    conn.close()
    raise RuntimeError("All providers unavailable")


def list_generations() -> list[dict]:
    db_path = _db_path()
    init_db(db_path, SCHEMA_PATH)
    conn = get_connection(db_path)
    rows = conn.execute(
        "SELECT id, style_id, prompt, generated_text, provider_used, created_at, updated_at FROM generations ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_generation(generation_id: str) -> dict | None:
    db_path = _db_path()
    init_db(db_path, SCHEMA_PATH)
    conn = get_connection(db_path)
    row = conn.execute(
        "SELECT id, style_id, prompt, generated_text, provider_used, created_at, updated_at FROM generations WHERE id = ?",
        (generation_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def update_generation(generation_id: str, generated_text: str) -> dict | None:
    db_path = _db_path()
    init_db(db_path, SCHEMA_PATH)
    conn = get_connection(db_path)
    updated_at = datetime.now(UTC).isoformat()
    cursor = conn.execute(
        "UPDATE generations SET generated_text = ?, updated_at = ? WHERE id = ?",
        (generated_text, updated_at, generation_id),
    )
    if cursor.rowcount == 0:
        conn.close()
        return None
    conn.commit()
    row = conn.execute(
        "SELECT id, style_id, prompt, generated_text, provider_used, created_at, updated_at FROM generations WHERE id = ?",
        (generation_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None
