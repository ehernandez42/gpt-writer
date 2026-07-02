from datetime import UTC, datetime
from pathlib import Path
import os
import uuid

from database.db import get_connection, init_db
from parsers.factory import get_parser
from storage.factory import get_storage

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "database" / "init.sql"


def _db_path() -> Path:
    base_dir = Path(os.getenv("STORAGE_BASE_DIR", "./storage"))
    return base_dir / "gpt-writer.db"


def create_style(name: str, uploads: list) -> dict:
    storage = get_storage()
    db_path = _db_path()
    init_db(db_path, SCHEMA_PATH)
    conn = get_connection(db_path)

    style_id = str(uuid.uuid4())
    now = datetime.now(UTC).isoformat()
    conn.execute(
        "INSERT INTO styles (id, name, created_at, updated_at) VALUES (?, ?, ?, ?)",
        (style_id, name, now, now),
    )

    combined_parts: list[str] = []

    for upload in uploads:
        doc_id = str(uuid.uuid4())
        ext = Path(upload.filename).suffix or ".txt"
        original_path = f"documents/{doc_id}{ext}"
        extracted_path = f"extracted/{doc_id}.txt"
        content = upload.file.read()
        storage.save_file(original_path, content)

        parser = get_parser(upload.content_type)
        temp_path = Path(os.getenv("STORAGE_BASE_DIR", "./storage")) / original_path
        extracted_text = parser.parse(temp_path)
        storage.save_file(extracted_path, extracted_text.encode("utf-8"))
        combined_parts.append(extracted_text)

        conn.execute(
            """
            INSERT INTO documents (
                id, style_id, filename, original_path, extracted_path, content_type, file_size, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                doc_id,
                style_id,
                upload.filename,
                original_path,
                extracted_path,
                upload.content_type,
                len(content),
                now,
            ),
        )

    storage.save_file(
        f"extracted/{style_id}.combined.txt",
        "\n\n".join(combined_parts).encode("utf-8"),
    )
    conn.commit()
    conn.close()

    return {"style_id": style_id, "name": name, "docs_count": len(uploads)}


def list_styles() -> list[dict]:
    db_path = _db_path()
    init_db(db_path, SCHEMA_PATH)
    conn = get_connection(db_path)
    rows = conn.execute(
        "SELECT id, name, created_at, updated_at FROM styles ORDER BY updated_at DESC"
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_style(style_id: str) -> dict | None:
    storage = get_storage()
    db_path = _db_path()
    init_db(db_path, SCHEMA_PATH)
    conn = get_connection(db_path)
    style = conn.execute(
        "SELECT id, name, created_at, updated_at FROM styles WHERE id = ?",
        (style_id,),
    ).fetchone()
    if not style:
        conn.close()
        return None
    documents = conn.execute(
        "SELECT id, filename, extracted_path, content_type, file_size, created_at FROM documents WHERE style_id = ?",
        (style_id,),
    ).fetchall()
    conn.close()
    combined_text = storage.get_file(f"extracted/{style_id}.combined.txt").decode("utf-8")
    return {
        **dict(style),
        "documents": [dict(row) for row in documents],
        "combined_text": combined_text,
    }


def delete_style(style_id: str) -> None:
    storage = get_storage()
    db_path = _db_path()
    init_db(db_path, SCHEMA_PATH)
    conn = get_connection(db_path)
    docs = conn.execute(
        "SELECT original_path, extracted_path FROM documents WHERE style_id = ?",
        (style_id,),
    ).fetchall()
    conn.execute("DELETE FROM styles WHERE id = ?", (style_id,))
    conn.commit()
    conn.close()

    for doc in docs:
        storage.delete_file(doc["original_path"])
        storage.delete_file(doc["extracted_path"])
    storage.delete_file(f"extracted/{style_id}.combined.txt")
