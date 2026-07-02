# Style-Matching Writing Generator Implementation Plan

> **REQUIRED SUB-SKILL:** Use the executing-plans skill to implement this plan task-by-task.

**Goal:** Build the initial full-stack scaffold for a style-matching writing generator with document upload, style profile creation, LLM-backed generation, editable output, and PDF/DOCX export.

**Architecture:** Build the backend first as a thin-router FastAPI app with service, provider, parser, and storage layers, then connect a Vite/React frontend through a small API client and TanStack Query hooks. Keep storage local and auth-free for the first slice, and use prompt-based style matching by passing bounded combined extracted text into the generation prompt at request time. For this MVP, use Python `sqlite3` directly instead of SQLAlchemy, and treat style creation as atomic: if any uploaded file fails validation or parsing, abort the whole request and persist nothing.

**Tech Stack:** FastAPI, Python, sqlite3, httpx, anthropic, pypdf, python-docx, reportlab, Vite, React, TypeScript, React Router, TanStack Query, Zustand, Tiptap, Tailwind CSS, sonner, Vitest, Testing Library

---

## Preconditions

- Work in a dedicated git worktree.
- Read `docs/plans/2026-06-30-style-matching-generator-design.md` before starting.
- Use TDD for every task.
- Prefer the smallest passing implementation.
- Commit after each task.
- Keep the v1 prompt context bounded: cap combined extracted text at a fixed limit such as 20,000 characters and truncate deterministically if needed.
- Reject unsupported file types, empty uploads, and oversized files before creating a style.
- Treat `POST /styles` as atomic: if one file fails, rollback database writes and delete any saved files from that request.

## Suggested commit rhythm

- `chore: scaffold backend app structure`
- `feat: add local storage and database bootstrap`
- `feat: add document parsers and style creation service`
- `feat: add style query and delete endpoints`
- `feat: add provider chain and generation flow`
- `feat: add export service and endpoint`
- `chore: scaffold frontend app shell`
- `feat: add styles studio UI`
- `feat: add generator workspace UI`
- `docs: add project readme and wiki scaffold`

### Task 1: Scaffold backend application shell

**Files:**
- Create: `backend/main.py`
- Create: `backend/requirements.txt`
- Create: `backend/.env.example`
- Create: `backend/routers/__init__.py`
- Create: `backend/routers/styles.py`
- Create: `backend/routers/generate.py`
- Create: `backend/routers/export.py`
- Create: `backend/tests/test_health.py`

**Step 1: Write the failing test**

```python
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health_returns_ok_payload():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_health.py -v`
Expected: FAIL with `ModuleNotFoundError` or missing `app`

**Step 3: Write minimal implementation**

```python
# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

```python
# backend/routers/styles.py
from fastapi import APIRouter

router = APIRouter(prefix="/styles", tags=["styles"])
```

```python
# backend/routers/generate.py
from fastapi import APIRouter

router = APIRouter(tags=["generate"])
```

```python
# backend/routers/export.py
from fastapi import APIRouter

router = APIRouter(tags=["export"])
```

```text
# backend/requirements.txt
fastapi
uvicorn[standard]
pytest
httpx
python-multipart
```

```bash
# backend/.env.example
OLLAMA_API_KEY=
ANTHROPIC_API_KEY=
OLLAMA_MODEL=llama3.1
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
STORAGE_TYPE=local
STORAGE_BASE_DIR=./storage
DATABASE_URL=sqlite:///./storage/gpt-writer.db
```

**Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_health.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/main.py backend/requirements.txt backend/.env.example backend/routers/__init__.py backend/routers/styles.py backend/routers/generate.py backend/routers/export.py backend/tests/test_health.py
git commit -m "chore: scaffold backend app structure"
```

### Task 2: Add database bootstrap and local storage abstraction

**Files:**
- Create: `backend/database/init.sql`
- Create: `backend/database/__init__.py`
- Create: `backend/database/db.py`
- Create: `backend/storage/__init__.py`
- Create: `backend/storage/base.py`
- Create: `backend/storage/local.py`
- Create: `backend/storage/factory.py`
- Create: `backend/tests/test_storage_local.py`
- Modify: `backend/requirements.txt`

**Step 1: Write the failing test**

```python
from pathlib import Path

from storage.local import LocalStorage


def test_local_storage_can_save_read_list_and_delete(tmp_path: Path):
    storage = LocalStorage(tmp_path)

    saved_path = storage.save_file("documents/example.txt", b"hello")

    assert saved_path == "documents/example.txt"
    assert storage.get_file("documents/example.txt") == b"hello"
    assert storage.list_files("documents") == ["documents/example.txt"]

    storage.delete_file("documents/example.txt")

    assert storage.list_files("documents") == []
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_storage_local.py -v`
Expected: FAIL with missing `LocalStorage`

**Step 3: Write minimal implementation**

```python
# backend/storage/base.py
from abc import ABC, abstractmethod


class StorageBackend(ABC):
    @abstractmethod
    def save_file(self, path: str, content: bytes) -> str: ...

    @abstractmethod
    def get_file(self, path: str) -> bytes: ...

    @abstractmethod
    def delete_file(self, path: str) -> None: ...

    @abstractmethod
    def list_files(self, prefix: str) -> list[str]: ...
```

```python
# backend/storage/local.py
from pathlib import Path

from storage.base import StorageBackend


class LocalStorage(StorageBackend):
    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save_file(self, path: str, content: bytes) -> str:
        full_path = self.base_dir / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_bytes(content)
        return path

    def get_file(self, path: str) -> bytes:
        return (self.base_dir / path).read_bytes()

    def delete_file(self, path: str) -> None:
        full_path = self.base_dir / path
        if full_path.exists():
            full_path.unlink()

    def list_files(self, prefix: str) -> list[str]:
        root = self.base_dir / prefix
        if not root.exists():
            return []
        return sorted(
            str(path.relative_to(self.base_dir)).replace('\\', '/')
            for path in root.rglob('*')
            if path.is_file()
        )
```

```python
# backend/storage/factory.py
import os

from storage.local import LocalStorage


def get_storage() -> LocalStorage:
    return LocalStorage(os.getenv("STORAGE_BASE_DIR", "./storage"))
```

```python
# backend/database/db.py
from pathlib import Path
import sqlite3


def get_connection(db_path: str | Path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: str | Path, schema_path: str | Path) -> None:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = get_connection(db_path)
    conn.executescript(Path(schema_path).read_text(encoding="utf-8"))
    conn.commit()
    conn.close()
```

```sql
-- backend/database/init.sql
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
    FOREIGN KEY (style_id) REFERENCES styles(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_styles_updated ON styles(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_generations_style ON generations(style_id, created_at DESC);
```

**Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_storage_local.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/database/init.sql backend/database/__init__.py backend/database/db.py backend/storage/__init__.py backend/storage/base.py backend/storage/local.py backend/storage/factory.py backend/tests/test_storage_local.py backend/requirements.txt
git commit -m "feat: add local storage and database bootstrap"
```

### Task 3: Add plain text and markdown parser support

**Files:**
- Create: `backend/parsers/__init__.py`
- Create: `backend/parsers/base.py`
- Create: `backend/parsers/text.py`
- Create: `backend/parsers/factory.py`
- Create: `backend/tests/test_parsers_text.py`

**Step 1: Write the failing test**

```python
from pathlib import Path

from parsers.factory import get_parser


def test_text_parser_reads_utf8_file(tmp_path: Path):
    file_path = tmp_path / "sample.txt"
    file_path.write_text("hello world", encoding="utf-8")

    parser = get_parser("text/plain")

    assert parser.parse(file_path) == "hello world"
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_parsers_text.py -v`
Expected: FAIL with missing parser modules

**Step 3: Write minimal implementation**

```python
# backend/parsers/base.py
from abc import ABC, abstractmethod
from pathlib import Path


class Parser(ABC):
    @abstractmethod
    def parse(self, file_path: Path) -> str: ...
```

```python
# backend/parsers/text.py
from pathlib import Path

from parsers.base import Parser


class TextParser(Parser):
    def parse(self, file_path: Path) -> str:
        return file_path.read_text(encoding="utf-8")
```

```python
# backend/parsers/factory.py
from parsers.text import TextParser


def get_parser(content_type: str):
    if content_type in ("text/plain", "text/markdown"):
        return TextParser()
    raise ValueError(f"Unsupported content type: {content_type}")
```

**Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_parsers_text.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/parsers/__init__.py backend/parsers/base.py backend/parsers/text.py backend/parsers/factory.py backend/tests/test_parsers_text.py
git commit -m "feat: add text parser support"
```

### Task 4: Add PDF and DOCX parser support

**Files:**
- Create: `backend/parsers/pdf.py`
- Create: `backend/parsers/docx.py`
- Modify: `backend/parsers/factory.py`
- Modify: `backend/requirements.txt`
- Create: `backend/tests/test_parsers_factory.py`

**Step 1: Write the failing test**

```python
import pytest

from parsers.factory import get_parser
from parsers.docx import DocxParser
from parsers.pdf import PDFParser
from parsers.text import TextParser


def test_factory_returns_expected_parser_types():
    assert isinstance(get_parser("text/plain"), TextParser)
    assert isinstance(get_parser("text/markdown"), TextParser)
    assert isinstance(get_parser("application/pdf"), PDFParser)
    assert isinstance(
        get_parser("application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
        DocxParser,
    )


def test_factory_rejects_unsupported_types():
    with pytest.raises(ValueError):
        get_parser("image/png")
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_parsers_factory.py -v`
Expected: FAIL with missing parser classes

**Step 3: Write minimal implementation**

```python
# backend/parsers/pdf.py
from pathlib import Path

from pypdf import PdfReader

from parsers.base import Parser


class PDFParser(Parser):
    def parse(self, file_path: Path) -> str:
        reader = PdfReader(str(file_path))
        return "\n".join((page.extract_text() or "") for page in reader.pages).strip()
```

```python
# backend/parsers/docx.py
from pathlib import Path

from docx import Document

from parsers.base import Parser


class DocxParser(Parser):
    def parse(self, file_path: Path) -> str:
        document = Document(file_path)
        return "\n".join(p.text for p in document.paragraphs).strip()
```

```python
# backend/parsers/factory.py
from parsers.docx import DocxParser
from parsers.pdf import PDFParser
from parsers.text import TextParser


def get_parser(content_type: str):
    if content_type in ("text/plain", "text/markdown"):
        return TextParser()
    if content_type == "application/pdf":
        return PDFParser()
    if content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return DocxParser()
    raise ValueError(f"Unsupported content type: {content_type}")
```

```text
# append to backend/requirements.txt
pypdf
python-docx
```

**Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_parsers_factory.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/parsers/pdf.py backend/parsers/docx.py backend/parsers/factory.py backend/requirements.txt backend/tests/test_parsers_factory.py
git commit -m "feat: add pdf and docx parser support"
```

### Task 5: Implement style creation service and POST /styles endpoint

**Implementation notes:**
- Do not assume future blob support in this task; local filesystem storage is the only supported runtime for parsing in this MVP.
- Keep the storage interface in place, but make the local-storage assumption explicit in code comments so the later blob migration is a planned refactor, not an accidental abstraction leak.
- Validate uploads before inserting the style row whenever possible.

**Files:**
- Create: `backend/services/__init__.py`
- Create: `backend/services/styles.py`
- Modify: `backend/routers/styles.py`
- Modify: `backend/main.py`
- Create: `backend/tests/test_create_style.py`

**Step 1: Write the failing test**

```python
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_create_style_from_uploaded_text_file(tmp_path, monkeypatch):
    monkeypatch.setenv("STORAGE_BASE_DIR", str(tmp_path / "storage"))
    response = client.post(
        "/styles",
        data={"name": "Formal Memo"},
        files=[("files", ("sample.txt", b"Line one", "text/plain"))],
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Formal Memo"
    assert body["docs_count"] == 1
    assert body["style_id"]
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_create_style.py -v`
Expected: FAIL with 404 or missing service code

**Step 3: Write minimal implementation**

```python
# backend/services/styles.py
from datetime import datetime, UTC
from pathlib import Path
import os
import sqlite3
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
        # MVP note: parsing currently depends on local filesystem paths.
        # Blob-backed parsing is a later refactor.
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
```

```python
# backend/routers/styles.py
from fastapi import APIRouter, File, Form, UploadFile

from services.styles import create_style

router = APIRouter(prefix="/styles", tags=["styles"])


@router.post("", status_code=201)
def create_style_endpoint(name: str = Form(...), files: list[UploadFile] = File(...)):
    return create_style(name, files)
```

```python
# add in backend/main.py
from routers.styles import router as styles_router

app.include_router(styles_router)
```

**Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_create_style.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/services/__init__.py backend/services/styles.py backend/routers/styles.py backend/main.py backend/tests/test_create_style.py
git commit -m "feat: add style creation endpoint"
```

### Task 6: Implement list, detail, and delete style flows

**Implementation notes:**
- `get_style()` must return `None` when the style row does not exist.
- The router should be responsible for turning `None` into HTTP 404.

**Files:**
- Modify: `backend/services/styles.py`
- Modify: `backend/routers/styles.py`
- Create: `backend/tests/test_style_queries.py`

**Step 1: Write the failing test**

```python
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_style_can_be_listed_read_and_deleted(tmp_path, monkeypatch):
    monkeypatch.setenv("STORAGE_BASE_DIR", str(tmp_path / "storage"))
    created = client.post(
        "/styles",
        data={"name": "Board Report"},
        files=[("files", ("sample.txt", b"alpha beta", "text/plain"))],
    ).json()
    style_id = created["style_id"]

    list_response = client.get("/styles")
    assert list_response.status_code == 200
    assert list_response.json()[0]["id"] == style_id

    detail_response = client.get(f"/styles/{style_id}")
    assert detail_response.status_code == 200
    assert detail_response.json()["name"] == "Board Report"
    assert "alpha beta" in detail_response.json()["combined_text"]

    delete_response = client.delete(f"/styles/{style_id}")
    assert delete_response.status_code == 204
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_style_queries.py -v`
Expected: FAIL with 405 or 404 for one or more routes

**Step 3: Write minimal implementation**

Add these functions in `backend/services/styles.py`:

```python
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
```

Add these routes in `backend/routers/styles.py`:

```python
from fastapi import HTTPException
from starlette.status import HTTP_204_NO_CONTENT

from services.styles import create_style, delete_style, get_style, list_styles


@router.get("")
def list_styles_endpoint():
    return list_styles()


@router.get("/{style_id}")
def get_style_endpoint(style_id: str):
    style = get_style(style_id)
    if not style:
        raise HTTPException(status_code=404, detail="Style not found")
    return style


@router.delete("/{style_id}", status_code=HTTP_204_NO_CONTENT)
def delete_style_endpoint(style_id: str):
    delete_style(style_id)
```

**Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_style_queries.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/services/styles.py backend/routers/styles.py backend/tests/test_style_queries.py
git commit -m "feat: add style query and delete endpoints"
```

### Task 7: Add provider interface and Ollama provider

**Files:**
- Create: `backend/providers/__init__.py`
- Create: `backend/providers/base.py`
- Create: `backend/providers/ollama.py`
- Create: `backend/tests/test_ollama_provider.py`
- Modify: `backend/requirements.txt`

**Step 1: Write the failing test**

```python
import pytest

from providers.ollama import OllamaProvider


@pytest.mark.asyncio
async def test_ollama_unavailable_without_api_key(monkeypatch):
    monkeypatch.delenv("OLLAMA_API_KEY", raising=False)
    provider = OllamaProvider()

    assert await provider.is_available() is False
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_ollama_provider.py -v`
Expected: FAIL with missing provider module

**Step 3: Write minimal implementation**

```python
# backend/providers/base.py
from abc import ABC, abstractmethod


class LLMProvider(ABC):
    name: str

    @abstractmethod
    async def generate(self, messages: list[dict], **kwargs) -> str: ...

    @abstractmethod
    async def is_available(self) -> bool: ...
```

```python
# backend/providers/ollama.py
import os

import httpx

from providers.base import LLMProvider


class OllamaProvider(LLMProvider):
    name = "ollama"

    def __init__(self):
        self.base_url = "https://api.ollama.com/v1"
        self.model = os.getenv("OLLAMA_MODEL", "llama3.1")
        self.api_key = os.getenv("OLLAMA_API_KEY")

    async def generate(self, messages: list[dict], **kwargs) -> str:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": self.model, "messages": messages, **kwargs},
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]

    async def is_available(self) -> bool:
        if not self.api_key:
            return False
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{self.base_url}/models",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                return response.is_success
        except Exception:
            return False
```

```text
# append to backend/requirements.txt
pytest-asyncio
```

**Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_ollama_provider.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/providers/__init__.py backend/providers/base.py backend/providers/ollama.py backend/tests/test_ollama_provider.py backend/requirements.txt
git commit -m "feat: add ollama provider"
```

### Task 8: Add Anthropic provider and provider registry

**Files:**
- Create: `backend/providers/anthropic.py`
- Create: `backend/providers/registry.py`
- Create: `backend/tests/test_provider_registry.py`
- Modify: `backend/requirements.txt`

**Step 1: Write the failing test**

```python
from providers.registry import get_provider_chain


def test_provider_chain_prefers_ollama_then_anthropic():
    chain = get_provider_chain()

    assert [provider.name for provider in chain] == ["ollama", "anthropic"]
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_provider_registry.py -v`
Expected: FAIL with missing registry or provider

**Step 3: Write minimal implementation**

```python
# backend/providers/anthropic.py
import os

from anthropic import AsyncAnthropic

from providers.base import LLMProvider


class AnthropicProvider(LLMProvider):
    name = "anthropic"

    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
        self.client = AsyncAnthropic(api_key=self.api_key) if self.api_key else None

    async def generate(self, messages: list[dict], **kwargs) -> str:
        system_messages = [m["content"] for m in messages if m["role"] == "system"]
        user_messages = [{"role": m["role"], "content": m["content"]} for m in messages if m["role"] != "system"]
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", 1000),
            system="\n\n".join(system_messages),
            messages=user_messages,
        )
        return "".join(block.text for block in response.content if block.type == "text")

    async def is_available(self) -> bool:
        return self.client is not None
```

```python
# backend/providers/registry.py
from providers.anthropic import AnthropicProvider
from providers.ollama import OllamaProvider


def get_provider_chain():
    return [OllamaProvider(), AnthropicProvider()]
```

```text
# append to backend/requirements.txt
anthropic
```

**Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_provider_registry.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/providers/anthropic.py backend/providers/registry.py backend/tests/test_provider_registry.py backend/requirements.txt
git commit -m "feat: add anthropic provider fallback"
```

### Task 9: Implement generation service and POST /generate endpoint

**Files:**
- Create: `backend/services/generate.py`
- Modify: `backend/routers/generate.py`
- Modify: `backend/main.py`
- Create: `backend/tests/test_generate_service.py`

**Step 1: Write the failing test**

```python
import pytest

from services.generate import build_messages


def test_build_messages_embeds_style_reference_and_prompt():
    messages = build_messages("formal style sample", "Write an update")

    assert messages[0]["role"] == "system"
    assert "formal style sample" in messages[0]["content"]
    assert messages[1] == {"role": "user", "content": "Write an update"}
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_generate_service.py -v`
Expected: FAIL with missing generation service

**Step 3: Write minimal implementation**

```python
# backend/services/generate.py
from datetime import datetime, UTC
from pathlib import Path
import os
import uuid

from database.db import get_connection
from providers.registry import get_provider_chain
from storage.factory import get_storage


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
    conn = get_connection(_db_path())
    style_text = storage.get_file(f"extracted/{style_id}.combined.txt").decode("utf-8")
    messages = build_messages(style_text, prompt)

    for provider in get_provider_chain():
        if await provider.is_available():
            try:
                text = await provider.generate(messages)
                generation_id = str(uuid.uuid4())
                created_at = datetime.now(UTC).isoformat()
                conn.execute(
                    "INSERT INTO generations (id, style_id, prompt, generated_text, provider_used, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (generation_id, style_id, prompt, text, provider.name, created_at),
                )
                conn.commit()
                conn.close()
                return {
                    "generation_id": generation_id,
                    "text": text,
                    "provider_used": provider.name,
                    "created_at": created_at,
                }
            except Exception:
                continue

    conn.close()
    raise RuntimeError("All providers unavailable")
```

```python
# backend/routers/generate.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.generate import generate_text

router = APIRouter(tags=["generate"])


class GenerateRequest(BaseModel):
    style_id: str
    prompt: str


@router.post("/generate")
async def generate_endpoint(payload: GenerateRequest):
    try:
        return await generate_text(payload.style_id, payload.prompt)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
```

```python
# add in backend/main.py
from routers.generate import router as generate_router

app.include_router(generate_router)
```

**Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_generate_service.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/services/generate.py backend/routers/generate.py backend/main.py backend/tests/test_generate_service.py
git commit -m "feat: add generation service and endpoint"
```

### Task 10: Add GET /generations/{id} endpoint

**Implementation notes:**
- Unlike the earlier draft, the test in this task must include its own row setup so it is runnable without interpretation.

**Files:**
- Modify: `backend/services/generate.py`
- Modify: `backend/routers/generate.py`
- Create: `backend/tests/test_generation_lookup.py`

**Step 1: Write the failing test**

```python
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
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_generation_lookup.py -v`
Expected: FAIL with missing function

**Step 3: Write minimal implementation**

Add this function to `backend/services/generate.py`:

```python
def get_generation(generation_id: str) -> dict | None:
    conn = get_connection(_db_path())
    row = conn.execute(
        "SELECT id, style_id, prompt, generated_text, provider_used, created_at FROM generations WHERE id = ?",
        (generation_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None
```

Add this route to `backend/routers/generate.py`:

```python
@router.get("/generations/{generation_id}")
def get_generation_endpoint(generation_id: str):
    generation = get_generation(generation_id)
    if not generation:
        raise HTTPException(status_code=404, detail="Generation not found")
    return generation
```

**Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_generation_lookup.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/services/generate.py backend/routers/generate.py backend/tests/test_generation_lookup.py
git commit -m "feat: add generation lookup endpoint"
```

### Task 11: Implement export service and POST /export endpoint

**Implementation notes:**
- Keep the request shape consistent across backend and frontend: `POST /export` with JSON body `{ text, format }`.
- Do not put `format` in the query string.

**Files:**
- Create: `backend/services/export.py`
- Modify: `backend/routers/export.py`
- Modify: `backend/main.py`
- Create: `backend/tests/test_export_service.py`

**Step 1: Write the failing test**

```python
from services.export import export_text


def test_export_docx_returns_bytes_and_content_type():
    payload = export_text("hello world", "docx")

    assert payload["filename"] == "generated.docx"
    assert payload["content_type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    assert isinstance(payload["content"], bytes)
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_export_service.py -v`
Expected: FAIL with missing export service

**Step 3: Write minimal implementation**

```python
# backend/services/export.py
from io import BytesIO

from docx import Document
from reportlab.pdfgen import canvas


DOCX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
PDF_CONTENT_TYPE = "application/pdf"


def export_text(text: str, format: str) -> dict:
    if format == "docx":
        buffer = BytesIO()
        document = Document()
        document.add_paragraph(text)
        document.save(buffer)
        return {
            "filename": "generated.docx",
            "content_type": DOCX_CONTENT_TYPE,
            "content": buffer.getvalue(),
        }

    if format == "pdf":
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer)
        pdf.drawString(72, 800, text[:1000])
        pdf.save()
        return {
            "filename": "generated.pdf",
            "content_type": PDF_CONTENT_TYPE,
            "content": buffer.getvalue(),
        }

    raise ValueError("Unsupported export format")
```

```python
# backend/routers/export.py
from io import BytesIO

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from services.export import export_text

router = APIRouter(tags=["export"])


class ExportRequest(BaseModel):
    text: str
    format: str


@router.post("/export")
def export_endpoint(payload: ExportRequest):
    try:
        file_data = export_text(payload.text, payload.format)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return StreamingResponse(
        BytesIO(file_data["content"]),
        media_type=file_data["content_type"],
        headers={"Content-Disposition": f"attachment; filename={file_data['filename']}"},
    )
```

```python
# add in backend/main.py
from routers.export import router as export_router

app.include_router(export_router)
```

**Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_export_service.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/services/export.py backend/routers/export.py backend/main.py backend/tests/test_export_service.py
git commit -m "feat: add export service and endpoint"
```

### Task 12: Add backend integration test for core happy path

**Files:**
- Create: `backend/tests/test_api_happy_path.py`

**Step 1: Write the failing test**

```python
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health_and_style_creation_happy_path(tmp_path, monkeypatch):
    monkeypatch.setenv("STORAGE_BASE_DIR", str(tmp_path / "storage"))

    health = client.get("/health")
    create = client.post(
        "/styles",
        data={"name": "Policy Style"},
        files=[("files", ("sample.txt", b"clear short declarative writing", "text/plain"))],
    )
    styles = client.get("/styles")

    assert health.status_code == 200
    assert create.status_code == 201
    assert styles.status_code == 200
    assert styles.json()[0]["name"] == "Policy Style"
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_api_happy_path.py -v`
Expected: FAIL if app wiring is incomplete

**Step 3: Write minimal implementation**

Do not add new production code unless the test reveals missing app wiring. Fix only the missing wiring.

**Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_api_happy_path.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/tests/test_api_happy_path.py backend/main.py backend/routers backend/services
git commit -m "test: add backend happy path integration coverage"
```

### Task 13: Scaffold frontend app shell

**Implementation notes:**
- Use Vitest, not Jest.
- Add exact scripts in `frontend/package.json`: `dev`, `build`, `test`.
- Include `src/test/setup.ts` and wire Testing Library matchers there.

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/tsconfig.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/index.html`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/routes/StylesPage.tsx`
- Create: `frontend/src/routes/GeneratePage.tsx`
- Create: `frontend/src/components/Layout.tsx`
- Create: `frontend/src/test/App.test.tsx`

**Step 1: Write the failing test**

```tsx
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

import App from '../App'


test('renders app navigation', () => {
  render(
    <MemoryRouter>
      <App />
    </MemoryRouter>
  )

  expect(screen.getByText(/styles/i)).toBeInTheDocument()
  expect(screen.getByText(/generate/i)).toBeInTheDocument()
})
```

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- --runInBand`
Expected: FAIL with missing app files or test setup

**Step 3: Write minimal implementation**

Use this route layout:

```tsx
// frontend/src/App.tsx
import { Navigate, Route, Routes } from 'react-router-dom'

import { Layout } from './components/Layout'
import { GeneratePage } from './routes/GeneratePage'
import { StylesPage } from './routes/StylesPage'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Navigate to="/styles" replace />} />
        <Route path="/styles" element={<StylesPage />} />
        <Route path="/generate" element={<GeneratePage />} />
      </Route>
    </Routes>
  )
}
```

```tsx
// frontend/src/components/Layout.tsx
import { NavLink, Outlet } from 'react-router-dom'

export function Layout() {
  return (
    <div>
      <nav>
        <NavLink to="/styles">Styles</NavLink>
        <NavLink to="/generate">Generate</NavLink>
      </nav>
      <main>
        <Outlet />
      </main>
    </div>
  )
}
```

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- --runInBand`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/package.json frontend/tsconfig.json frontend/vite.config.ts frontend/index.html frontend/src/main.tsx frontend/src/App.tsx frontend/src/routes/StylesPage.tsx frontend/src/routes/GeneratePage.tsx frontend/src/components/Layout.tsx frontend/src/test/App.test.tsx
git commit -m "chore: scaffold frontend app shell"
```

### Task 14: Add frontend API client and style query hooks

**Implementation notes:**
- The frontend `/export` client must send `{ text, format }` in the JSON body to match the backend contract.
- If `FormData` is used, do not force `Content-Type: application/json`.

**Files:**
- Create: `frontend/src/lib/api.ts`
- Create: `frontend/src/queries/hooks/useStyles.ts`
- Create: `frontend/src/lib/queryClient.ts`
- Modify: `frontend/src/main.tsx`
- Create: `frontend/src/test/api.test.ts`

**Step 1: Write the failing test**

```ts
import { APIError } from '../lib/api'


test('api error preserves status code', () => {
  const error = new APIError(503, 'All providers unavailable')

  expect(error.status).toBe(503)
  expect(error.message).toBe('All providers unavailable')
})
```

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- --runInBand`
Expected: FAIL with missing api module

**Step 3: Write minimal implementation**

Implement the API client exactly as designed in `frontend/src/lib/api.ts` and create these hooks:

```ts
export function useStyles() {
  return useQuery({ queryKey: ['styles'], queryFn: () => api.get('/styles') })
}

export function useStyle(id: string) {
  return useQuery({ queryKey: ['styles', id], queryFn: () => api.get(`/styles/${id}`) })
}

export function useCreateStyle() {
  return useMutation({ mutationFn: (data: FormData) => api.request('/styles', { method: 'POST', body: data }) })
}
```

Wrap the app in `QueryClientProvider` in `frontend/src/main.tsx`.

Use this exact export client shape:

```ts
async export(text: string, format: 'pdf' | 'docx'): Promise<Blob> {
  const url = `${API_BASE}/export`
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, format }),
  })

  if (!response.ok) throw new APIError(response.status, await response.text())
  return response.blob()
}
```

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- --runInBand`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/lib/api.ts frontend/src/queries/hooks/useStyles.ts frontend/src/lib/queryClient.ts frontend/src/main.tsx frontend/src/test/api.test.ts
git commit -m "feat: add frontend api client and style hooks"
```

### Task 15: Build Style Studio upload flow

**Files:**
- Create: `frontend/src/components/FileUploader.tsx`
- Create: `frontend/src/components/StyleForm.tsx`
- Create: `frontend/src/components/StyleList.tsx`
- Create: `frontend/src/components/StyleCard.tsx`
- Modify: `frontend/src/routes/StylesPage.tsx`
- Create: `frontend/src/test/StyleForm.test.tsx`

**Step 1: Write the failing test**

```tsx
import { fireEvent, render, screen } from '@testing-library/react'

import { StyleForm } from '../components/StyleForm'


test('requires a name before submit', async () => {
  render(<StyleForm />)

  fireEvent.click(screen.getByRole('button', { name: /create style/i }))

  expect(await screen.findByText(/name is required/i)).toBeInTheDocument()
})
```

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- --runInBand`
Expected: FAIL with missing form component

**Step 3: Write minimal implementation**

Create a simple form with:
- text input named `name`
- file input accepting `.txt,.md,.pdf,.docx`
- submit button labeled `Create Style`
- inline validation for missing name and missing files
- mutation success path invalidates `['styles']`

Use `FormData` with this exact payload shape:
- `name` field once
- `files` field once per selected file

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- --runInBand`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/components/FileUploader.tsx frontend/src/components/StyleForm.tsx frontend/src/components/StyleList.tsx frontend/src/components/StyleCard.tsx frontend/src/routes/StylesPage.tsx frontend/src/test/StyleForm.test.tsx
git commit -m "feat: add styles studio upload flow"
```

### Task 16: Build Generator workspace with provider badge and prompt form

**Files:**
- Create: `frontend/src/queries/hooks/useGeneration.ts`
- Create: `frontend/src/components/GeneratorForm.tsx`
- Create: `frontend/src/components/ProviderBadge.tsx`
- Modify: `frontend/src/routes/GeneratePage.tsx`
- Create: `frontend/src/test/ProviderBadge.test.tsx`

**Step 1: Write the failing test**

```tsx
import { render, screen } from '@testing-library/react'

import { ProviderBadge } from '../components/ProviderBadge'


test('renders provider label', () => {
  render(<ProviderBadge provider="ollama" />)

  expect(screen.getByText(/ollama/i)).toBeInTheDocument()
})
```

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- --runInBand`
Expected: FAIL with missing badge component

**Step 3: Write minimal implementation**

Implement:

```ts
export function useGenerate() {
  return useMutation({
    mutationFn: ({ styleId, prompt }: { styleId: string; prompt: string }) =>
      api.post('/generate', { style_id: styleId, prompt }),
  })
}
```

Generator page requirements:
- style dropdown loaded from `useStyles()`
- prompt textarea
- generate button
- render provider badge from response `provider_used`
- show inline warning for 503 errors

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- --runInBand`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/queries/hooks/useGeneration.ts frontend/src/components/GeneratorForm.tsx frontend/src/components/ProviderBadge.tsx frontend/src/routes/GeneratePage.tsx frontend/src/test/ProviderBadge.test.tsx
git commit -m "feat: add generator workspace form"
```

### Task 17: Add editable generation preview with export actions

**Files:**
- Create: `frontend/src/components/GenerationEditor.tsx`
- Modify: `frontend/src/routes/GeneratePage.tsx`
- Create: `frontend/src/test/GenerationEditor.test.tsx`

**Step 1: Write the failing test**

```tsx
import { render, screen } from '@testing-library/react'

import { GenerationEditor } from '../components/GenerationEditor'


test('renders export buttons', () => {
  render(<GenerationEditor generatedText="hello" />)

  expect(screen.getByRole('button', { name: /export pdf/i })).toBeInTheDocument()
  expect(screen.getByRole('button', { name: /export docx/i })).toBeInTheDocument()
})
```

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- --runInBand`
Expected: FAIL with missing editor component

**Step 3: Write minimal implementation**

Implement `GenerationEditor` with:
- `@tiptap/react`
- `@tiptap/starter-kit`
- initial content from `generatedText`
- editable area
- `Export PDF` and `Export DOCX` buttons
- export handlers call `api.export(editor?.getText() || '', 'pdf' | 'docx')`
- downloaded blob is saved via `URL.createObjectURL`

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- --runInBand`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/components/GenerationEditor.tsx frontend/src/routes/GeneratePage.tsx frontend/src/test/GenerationEditor.test.tsx
git commit -m "feat: add editable generation preview and export"
```

### Task 18: Add global error boundary and toast notifications

**Files:**
- Create: `frontend/src/components/ErrorBoundary.tsx`
- Modify: `frontend/src/main.tsx`
- Modify: `frontend/src/routes/StylesPage.tsx`
- Modify: `frontend/src/routes/GeneratePage.tsx`
- Create: `frontend/src/test/ErrorBoundary.test.tsx`

**Step 1: Write the failing test**

```tsx
import { render, screen } from '@testing-library/react'

import { ErrorBoundary } from '../components/ErrorBoundary'

function Boom() {
  throw new Error('boom')
}

test('renders fallback ui on render error', () => {
  render(
    <ErrorBoundary>
      <Boom />
    </ErrorBoundary>
  )

  expect(screen.getByText(/something went wrong/i)).toBeInTheDocument()
})
```

**Step 2: Run test to verify it fails**

Run: `cd frontend && npm test -- --runInBand`
Expected: FAIL with missing boundary component

**Step 3: Write minimal implementation**

Implement:
- class-based `ErrorBoundary`
- fallback text `Something went wrong`
- add `<Toaster />` from `sonner` in `main.tsx`
- mutation failures show `toast.error(...)`
- query failures render inline message in page components

**Step 4: Run test to verify it passes**

Run: `cd frontend && npm test -- --runInBand`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/components/ErrorBoundary.tsx frontend/src/main.tsx frontend/src/routes/StylesPage.tsx frontend/src/routes/GeneratePage.tsx frontend/src/test/ErrorBoundary.test.tsx
git commit -m "feat: add frontend error handling"
```

### Task 19: Write project README and wiki scaffold

**Implementation notes:**
- Update docs to reflect actual implementation choices from this plan, especially `sqlite3` instead of SQLAlchemy if that is what was built.
- Document the v1 text-size cap and atomic style upload behavior.

**Files:**
- Create: `README.md`
- Create: `wiki/README.md`
- Create: `wiki/architecture.md`
- Create: `wiki/setup.md`
- Create: `wiki/coding-standards.md`
- Create: `wiki/api-reference.md`
- Create: `wiki/components.md`
- Create: `wiki/services.md`
- Create: `wiki/troubleshooting.md`
- Create: `wiki/changelog.md`

**Step 1: Write the failing test**

There is no automated test for docs. Instead, write a manual verification checklist in the PR/commit notes:
- README includes backend and frontend startup steps
- wiki files match the architecture in `docs/plans/2026-06-30-style-matching-generator-design.md`
- env vars are documented

**Step 2: Run verification to confirm docs are missing/incomplete**

Run: inspect the repo for missing docs files
Expected: one or more docs files missing

**Step 3: Write minimal implementation**

README must include:
- project overview
- repo layout
- backend startup commands
- frontend startup commands
- required env vars
- supported file types

Wiki files must reflect the current scaffold, not future ideas that were skipped.

**Step 4: Run verification to confirm docs exist**

Run:
- verify `README.md` exists
- verify all `wiki/*.md` files exist
- manually read each file for consistency with implemented code
Expected: all present and internally consistent

**Step 5: Commit**

```bash
git add README.md wiki/README.md wiki/architecture.md wiki/setup.md wiki/coding-standards.md wiki/api-reference.md wiki/components.md wiki/services.md wiki/troubleshooting.md wiki/changelog.md
git commit -m "docs: add project readme and wiki scaffold"
```

### Task 20: Final verification before handoff

### Task 20a: Test provider fallback behavior explicitly

**Files:**
- Create: `backend/tests/test_generate_fallback.py`
- Modify: `backend/services/generate.py`

**Step 1: Write the failing test**

```python
import pytest

from services.generate import generate_text


class UnavailableProvider:
    name = "ollama"

    async def is_available(self):
        return False


class WorkingProvider:
    name = "anthropic"

    async def is_available(self):
        return True

    async def generate(self, messages):
        return "fallback output"


@pytest.mark.asyncio
async def test_generate_uses_fallback_provider_when_first_is_unavailable(monkeypatch, tmp_path):
    monkeypatch.setenv("STORAGE_BASE_DIR", str(tmp_path / "storage"))
    monkeypatch.setattr("services.generate.get_provider_chain", lambda: [UnavailableProvider(), WorkingProvider()])
    # test setup should create style row and extracted/{style_id}.combined.txt before call
    result = await generate_text("style-1", "Write an update")

    assert result["provider_used"] == "anthropic"
    assert result["text"] == "fallback output"
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_generate_fallback.py -v`
Expected: FAIL until the test fixture/setup and fallback behavior are implemented correctly

**Step 3: Write minimal implementation**

- Make the test self-contained by inserting the required `styles` row and saving `extracted/style-1.combined.txt` before calling `generate_text()`.
- Ensure `generate_text()` skips unavailable providers, continues after provider exceptions, and returns the successful fallback response.
- Add a second test where the first provider raises during `generate()` and the second succeeds.
- Add a third test that asserts a `RuntimeError` is raised when all providers are unavailable or fail.

**Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_generate_fallback.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/tests/test_generate_fallback.py backend/services/generate.py
git commit -m "test: cover provider fallback behavior"
```

### Task 21: Final verification before handoff

**Files:**
- Modify: `wiki/changelog.md`
- Modify: `README.md` if verification reveals drift

**Step 1: Write the verification checklist**

Checklist:
- backend unit tests pass
- backend integration tests pass
- frontend tests pass
- backend starts with `uvicorn main:app --reload --port 8000`
- frontend starts with `npm run dev`
- create style flow works with `.txt`
- generate page renders and handles empty states
- export endpoint returns file response for PDF and DOCX

**Step 2: Run verification**

Run:
- `cd backend && pytest -v`
- `cd frontend && npm test -- --runInBand`
- `cd backend && uvicorn main:app --reload --port 8000`
- `cd frontend && npm run dev`

Expected:
- tests PASS
- servers start without import/config errors

**Step 3: Fix only verified failures**

If any command fails, fix the specific failure and re-run only the affected command before changing anything else.

**Step 4: Re-run full verification**

Run the same command set again until all pass.
Expected: all checks pass

**Step 5: Commit**

```bash
git add README.md wiki/changelog.md backend frontend
git commit -m "chore: verify scaffold and update docs"
```

## Notes for the implementing engineer

- Health response should eventually include provider availability details if that is implemented; if not, document the simpler `{ "status": "ok" }` contract in README/wiki so docs match code.

- Keep routers thin; business logic belongs in `backend/services/`.
- Do not add auth, blob storage, streaming, or model fine-tuning in this phase.
- Use the exact storage layout from the design doc:
  - `storage/documents/{doc_id}.{ext}`
  - `storage/extracted/{doc_id}.txt`
  - `storage/extracted/{style_id}.combined.txt`
- Prefer `.txt` coverage first; PDF/DOCX parsing depth can stay minimal as long as the interfaces and tests exist.
- Keep frontend styling minimal until the flows work.
- Update wiki docs only to match implemented behavior.
