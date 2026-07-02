import os
from pathlib import Path
import sqlite3
import sqlite_vec


class DBManager:
    def __init__(self, db_path: str | Path | None = None):
        self.db_path = Path(db_path) if db_path is not None else Path(os.getenv("STORAGE_BASE_DIR", "./storage")) / "gpt-writer.db"

    def connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def init_db(self, schema_path: str | Path):
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        conn = self.connect()
        conn.executescript(Path(schema_path).read_text(encoding="utf-8"))
        conn.commit()
        conn.close()


    def init_vector_tables(self):
        conn = self.connect()
        conn.enable_load_extension(True)
        sqlite_vec.load(conn)

        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS writing_samples_embeddings using vec0(
                    sample_id TEXT PRIMARY KEY,
                    content_embedding FLOAT[384],
                    style_embedding FLOAT[384]
                    )
            """)
        conn.commit()
        conn.close()


#v1 workaround; will need to refactor again manually
def get_connection(db_path: str | Path | None = None):
    return DBManager(db_path).connect()

#v1 workaround; will need to refactor again manually
def init_db(db_path_or_schema_path: str | Path, schema_path: str | Path | None = None):
    if schema_path is None:
        DBManager().init_db(db_path_or_schema_path)
        return

    DBManager(db_path_or_schema_path).init_db(schema_path)