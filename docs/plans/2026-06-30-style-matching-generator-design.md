# Style-Matching Writing Generator — Design

**Date:** 2026-06-30
**Status:** Validated
**Purpose:** Scaffold a Vite/React frontend + FastAPI backend + LLM wiki knowledge base for a style-matching writing generator.

---

## Overview

An app that helps users create generated writing samples in the style of documents they upload.

**Core workflow:**
1. User uploads sample documents (style references).
2. App parses docs and saves a reusable "style profile."
3. User selects a style + writes a prompt.
4. LLM generates writing that emulates the uploaded style.
5. User edits the generated text in a word-processor-like editor, then exports to PDF or DOCX.

**LLM provider strategy:** Ollama Cloud (API key) as default, Anthropic API as fallback. The active provider is surfaced in the UI.

**MVP constraints:**
- Style creation is atomic: if any uploaded file fails validation or parsing, the whole request fails and nothing is persisted.
- Combined extracted style text is bounded before generation time. For v1, cap the combined style reference at a fixed limit such as 20,000 characters and truncate deterministically.
- Local filesystem storage is the only supported runtime for parsing in v1. Blob storage remains a later migration.

**Three components in one repo:**
1. **Frontend** — Vite + React + TypeScript (the app UI)
2. **Backend** — FastAPI + Python (the app API)
3. **Wiki** — Markdown knowledge base (documents the codebase for LLM coding agents)

The frontend/backend are the app itself. The wiki is a context layer for coding agents working on the FE/BE. It is maintained by asking the model to update it when things change.

**Non-goals for this scaffold:**
- No authentication (single-user, localhost demo).
- No blob storage yet (local files now, Azure Blob later via abstraction).
- No streaming generation (optional future enhancement).

---

## Architecture & Repo Layout

```
gpt-writer/
├── frontend/          # Vite + React + TypeScript
├── backend/           # FastAPI (Python)
├── wiki/              # LLM knowledge base (markdown)
├── docs/
│   └── plans/
├── README.md
└── docker-compose.yml # optional, for local dev
```

**Frontend** (`frontend/`): Vite + React + TypeScript. Two main areas:
- **Style Studio** — upload docs, create/manage named style profiles, preview extracted text
- **Generator** — pick a style, write a prompt, get generated text in an editable preview, export to PDF/DOCX

Server state via TanStack Query; light UI state via Zustand. A thin API client module wraps all backend calls so endpoints live in one place.

**Backend** (`backend/`): FastAPI with a clean layered structure:
- `routers/` — HTTP endpoints (thin)
- `services/` — business logic (style extraction, generation, export)
- `providers/` — LLM provider interface + Ollama/Anthropic impls with fallback
- `storage/` — storage backend interface (Local now, Blob later)
- `parsers/` — text extraction from .txt/.md/.docx/.pdf

**Wiki** (`wiki/`): plain markdown, organized by topic, updated by the user asking the model. Always reflects the current state of FE/BE. Agents read it directly as context.

**Cross-cutting:** A `README.md` ties it together with setup steps. No auth. Everything runs locally for the demo.

---

## Backend API

### Endpoints

```
# Style management
POST   /styles                # create style from uploaded docs
GET    /styles                # list all styles
GET    /styles/{id}           # get style details + extracted text preview
DELETE /styles/{id}           # delete a style

# Generation
POST   /generate              # generate text: { style_id, prompt }
GET    /generations/{id}      # get saved generation

# Export (stateless — accepts edited text from UI)
POST   /export                # { text, format: "pdf"|"docx" } -> file download

# Health
GET    /health                # backend health; provider detail optional in v1
```

### Style profile structure (on disk)

```
storage/
├── documents/
│   └── {doc_id}.{ext}              # original uploaded files
├── extracted/
│   ├── {doc_id}.txt                # per-document extracted text
│   └── {style_id}.combined.txt     # concatenated text for LLM context
└── gpt-writer.db                   # SQLite database
```

`meta.json` is not needed; metadata lives in SQLite. The combined text file is what the LLM reads at generation time. Parsing happens once at upload time, not per generation.

### Request/Response shapes

**POST /styles** (multipart form with files + name field):
```
Response: { style_id, name, docs_count }
```

Validation rules for v1:
- Accept only `.txt`, `.md`, `.pdf`, `.docx`
- Reject empty file uploads
- Reject files over a configured size limit
- Fail the entire request if any file is invalid or cannot be parsed

**POST /generate**:
```json
// Request
{ "style_id": "uuid", "prompt": "Write a 500-word executive summary about X" }

// Response
{ "generation_id": "uuid", "text": "...", "provider_used": "ollama" | "anthropic", "created_at": "..." }
```

**POST /export** (stateless):
```json
// Request
{ "text": "...", "format": "pdf" | "docx" }

// Response: file download (StreamingResponse with proper Content-Type)
```

### Provider fallback logic

In `services/generate.py`:
1. Try Ollama → on success, return with `provider_used: "ollama"`
2. If Ollama is unavailable, skip it and try Anthropic
3. If Ollama is available but generation fails (timeout, unreachable, provider error), log and retry with Anthropic → return with `provider_used: "anthropic"`
4. If both fail, return 503 with error details

`is_available()` is checked *before* each attempt, so if Ollama is down we skip straight to Anthropic without waiting on a timeout.

---

## Database & Storage Layer

### SQLite schema (`backend/database/init.sql`)

```sql
CREATE TABLE styles (
    id TEXT PRIMARY KEY,          -- UUID
    name TEXT NOT NULL,
    created_at TEXT NOT NULL,     -- ISO timestamp
    updated_at TEXT NOT NULL
);

CREATE TABLE documents (
    id TEXT PRIMARY KEY,          -- UUID
    style_id TEXT NOT NULL,
    filename TEXT NOT NULL,
    original_path TEXT NOT NULL,  -- where file is stored
    extracted_path TEXT NOT NULL, -- path to extracted .txt
    content_type TEXT,            -- e.g., "application/pdf"
    file_size INTEGER,
    created_at TEXT NOT NULL,
    FOREIGN KEY (style_id) REFERENCES styles(id) ON DELETE CASCADE
);

CREATE TABLE generations (
    id TEXT PRIMARY KEY,          -- UUID
    style_id TEXT NOT NULL,
    prompt TEXT NOT NULL,
    generated_text TEXT NOT NULL,
    provider_used TEXT NOT NULL,  -- "ollama" | "anthropic"
    created_at TEXT NOT NULL,
    FOREIGN KEY (style_id) REFERENCES styles(id) ON DELETE CASCADE
);

CREATE INDEX idx_styles_updated ON styles(updated_at DESC);
CREATE INDEX idx_generations_style ON generations(style_id, created_at DESC);
```

### Storage abstraction

```python
# backend/storage/base.py
class StorageBackend(ABC):
    @abstractmethod
    def save_file(self, path: str, content: bytes) -> str: ...
    @abstractmethod
    def get_file(self, path: str) -> bytes: ...
    @abstractmethod
    def delete_file(self, path: str) -> None: ...
    @abstractmethod
    def list_files(self, prefix: str) -> List[str]: ...

# backend/storage/local.py
class LocalStorage(StorageBackend):
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)

# backend/storage/blob.py (placeholder for later)
class BlobStorage(StorageBackend):
    def __init__(self, connection_string: str, container: str): ...
```

When switching to blob storage later, the database paths become blob keys, and we swap the `StorageBackend` implementation. The rest of the code doesn't care.

---

## LLM Provider Layer & Style Learning

### Provider interface (`backend/providers/base.py`)

```python
class LLMProvider(ABC):
    name: str  # "ollama" | "anthropic"

    @abstractmethod
    async def generate(self, messages: List[dict], **kwargs) -> str:
        """Return generated text."""
        ...

    @abstractmethod
    async def is_available(self) -> bool:
        """Quick health check - is this provider reachable/configured?"""
        ...
```

### Implementations

- `backend/providers/ollama.py` — calls Ollama Cloud API (`OLLAMA_API_KEY`, OpenAI-compatible chat completion format)
- `backend/providers/anthropic.py` — calls Anthropic Messages API via `anthropic` SDK
- `backend/providers/registry.py` — builds the chain `[OllamaProvider, AnthropicProvider]`, tries each in order

```python
# backend/providers/ollama.py
class OllamaProvider(LLMProvider):
    name = "ollama"
    base_url = "https://api.ollama.com/v1"
    model = os.getenv("OLLAMA_MODEL", "llama3.1")
    api_key = os.getenv("OLLAMA_API_KEY")

    async def generate(self, messages: List[dict], **kwargs) -> str:
        response = await httpx.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"model": self.model, "messages": messages, **kwargs},
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    async def is_available(self) -> bool:
        if not self.api_key:
            return False
        try:
            await httpx.get(f"{self.base_url}/models", timeout=5.0)
            return True
        except Exception:
            return False
```

### Fallback flow

```python
# services/generate.py
async def generate(style_id, prompt):
    style = db.get_style(style_id)
    style_text = storage.read(style.extracted_path)  # combined docs

    messages = build_messages(style_text, prompt)

    for provider in registry.chain:  # [ollama, anthropic]
        if await provider.is_available():
            try:
                text = await provider.generate(messages)
                return Generation(provider_used=provider.name, ...)
            except Exception as e:
                log.warning(f"{provider.name} failed: {e}")
                continue  # try next

    raise HTTPException(503, "All providers unavailable")
```

### Style learning approach

Prompt-based, not fine-tuning. Style is passed as context each generation — no separate training step.

Because uploaded style material may be large, the combined reference passed into the prompt must be bounded. For v1, truncate deterministically at a fixed cap such as 20,000 characters and document the cap in README/wiki.

```python
def build_messages(style_text: str, prompt: str) -> List[dict]:
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
```

### Model selection (env vars)

```bash
OLLAMA_MODEL=llama3.1
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
```

---

## Document Parsing & Generation/Export

### Document parsers (`backend/parsers/`)

```python
# backend/parsers/base.py
class Parser(ABC):
    @abstractmethod
    def parse(self, file_path: Path) -> str:
        """Extract plain text from a document file."""
        ...

# backend/parsers/factory.py
def get_parser(content_type: str) -> Parser:
    if content_type in ("text/plain", "text/markdown"):
        return TextParser()
    elif content_type == "application/pdf":
        return PDFParser()       # pypdf or pdfplumber
    elif content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return DocxParser()      # python-docx
    else:
        raise ValueError(f"Unsupported content type: {content_type}")
```

Supported upload types: `.txt`, `.md`, `.pdf`, `.docx`.

Parsing is local-filesystem-based in v1. The parser interface currently works with file paths on disk; when blob storage is introduced later, parsing should be refactored to support streamed bytes or temporary local materialization.

### Upload flow (POST /styles)

1. Receive documents (multipart form).
2. Validate all files up front when possible (type, size, non-empty input).
3. For each document:
   a. Save original to `storage/documents/{doc_id}.{ext}` via `StorageBackend`.
   b. Parse to plain text → save to `storage/extracted/{doc_id}.txt`.
   c. Insert row in `documents` table.
4. Concatenate all extracted texts into `storage/extracted/{style_id}.combined.txt`.
5. Insert style row, return `style_id`.
6. If any step fails for any file, rollback database writes and delete files created during the request.

### Generation flow (POST /generate)

1. Load combined style text from storage.
2. Build messages via `build_messages()`.
3. Run provider chain (Ollama → Anthropic fallback).
4. Save generation row in SQLite with `provider_used`.
5. Return `{ generation_id, text, provider_used }`.

### Export flow (POST /export, stateless)

1. Receive `{ text, format }` from UI (the edited text from the Tiptap editor).
2. Generate PDF or DOCX on the fly:
   - **PDF**: `reportlab` (or `weasyprint` for HTML → PDF)
   - **DOCX**: `python-docx`
3. Return as file download (`StreamingResponse` with proper Content-Type).

Export is decoupled from generation — no database lookup. The frontend sends the current edited text directly.

---

## Frontend Architecture & State

### Tech stack

- Vite + React 18 + TypeScript
- Tailwind CSS (via `@vitejs/plugin-react-swc`)
- TanStack Query — server state
- Zustand — light UI state (optional; React Context also acceptable)
- Tiptap (`@tiptap/react` + `@tiptap/starter-kit`) — word-processor-style editable preview
- React Router DOM — routing
- `sonner` — toast notifications

### Pages

```
/                          # Redirect to /styles
/styles                    # Style Studio
/styles/new                # Create new style (upload docs)
/generate                  # Generator workspace
```

### TanStack Query hooks (`frontend/src/queries/`)

```typescript
// hooks/useStyles.ts
export function useStyles() {
  return useQuery({ queryKey: ['styles'], queryFn: () => api.get('/styles') })
}

export function useStyle(id: string) {
  return useQuery({ queryKey: ['styles', id], queryFn: () => api.get(`/styles/${id}`) })
}

export function useCreateStyle() {
  return useMutation({ mutationFn: (data) => api.post('/styles', data) })
}

// hooks/useGeneration.ts
export function useGenerate() {
  return useMutation({
    mutationFn: ({ styleId, prompt }) => api.post('/generate', { style_id: styleId, prompt })
  })
}
```

### UI components (rough breakdown)

- `Layout` — sidebar nav + content area
- `StyleList` — grid/list of styles with delete button
- `StyleForm` — upload docs (drag-drop or file picker), name input
- `StyleCard` — preview style info, view extracted text
- `GeneratorForm` — select style dropdown, prompt textarea, generate button
- `GenerationEditor` — Tiptap editable preview + export buttons (PDF/DOCX)
- `ProviderBadge` — shows "Ollama" or "Anthropic" with color coding
- `FileUploader` — reusable drag-drop component

### GenerationEditor (Tiptap)

```typescript
import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'

const editor = useEditor({
  extensions: [StarterKit],
  content: generatedText,
  editable: true,
})

// Export plain text for backend:
const plainText = editor?.getText() || ''
```

Tiptap with `StarterKit` provides: headings, bold/italic, lists, blockquotes, code blocks. Plain text (`getText()`) is sent to the export endpoint.

---

## Frontend API Client & Error Handling

### API client (`frontend/src/lib/api.ts`)

```typescript
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = {
  async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${API_BASE}${endpoint}`
    const response = await fetch(url, {
      headers: { 'Content-Type': 'application/json', ...options?.headers },
      ...options,
    })

    if (!response.ok) {
      const error = await response.text()
      throw new APIError(response.status, error)
    }

    return response.json()
  },

  get: <T>(endpoint: string) => api.request<T>(endpoint),
  post: <T>(endpoint: string, body: unknown) =>
    api.request<T>(endpoint, { method: 'POST', body: JSON.stringify(body) }),
  delete: <T>(endpoint: string) =>
    api.request<T>(endpoint, { method: 'DELETE' }),

  // Export returns a blob
  async export(text: string, format: 'pdf' | 'docx'): Promise<Blob> {
    const url = `${API_BASE}/export?format=${format}`
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    })

    if (!response.ok) throw new APIError(response.status, await response.text())
    return response.blob()
  },
}

class APIError extends Error {
  constructor(public status: number, message: string) {
    super(message)
  }
}
```

### Error handling UI

- Global error boundary (`frontend/src/components/ErrorBoundary.tsx`)
- Query errors render inline in components (e.g., "Failed to load styles")
- Mutation errors show toast notifications (`sonner`)
- 503 (all providers unavailable) shows a warning banner suggesting the user check API keys

---

## LLM Wiki Structure

The wiki lives in `wiki/` as markdown. The user asks the model to update it when things change. Agents read it directly as context.

```
wiki/
├── README.md                    # Overview for agents (what is this project?)
├── architecture.md              # FE/BE architecture, layers, decisions
├── setup.md                     # How to run locally (env vars, deps, commands)
├── coding-standards.md          # Naming, patterns, what to do/not do
├── api-reference.md             # Endpoint details
├── components.md                # Key FE components + props/responsibilities
├── services.md                  # Key BE services + functions
├── troubleshooting.md           # Common issues, debug tips
└── changelog.md                 # Major changes, why they were made
```

**Each file's purpose:**

- `README.md` — "This is a style-matching writing generator. Users upload docs → create styles → generate text in that style → export PDF/DOCX. Tech: Vite/React, FastAPI, Ollama Cloud + Anthropic fallback."
- `architecture.md` — Repo layout, API endpoints, provider chain, storage abstraction.
- `setup.md` — install steps, env vars (`OLLAMA_API_KEY`, `ANTHROPIC_API_KEY`), run commands.
- `coding-standards.md` — TypeScript strict mode, PEP 8, service layer over routers, etc.
- `api-reference.md` — Endpoint details (can be auto-generated from FastAPI OpenAPI spec).
- `components.md` — "GenerationEditor uses Tiptap; ProviderBadge shows active model; etc."
- `services.md` — "generate.py handles provider fallback; parsers/ extracts text from docs."
- `troubleshooting.md` — CORS issues, provider unreachable, file too large.
- `changelog.md` — "2026-06-30: Initial scaffold; etc."

When code changes, the user asks the model to update the relevant wiki doc. The model reads the code, updates the doc, the user reviews/commits.

---

## Development Workflow & Tooling

### Local dev (no Docker)

```bash
# Terminal 1 - Backend
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Terminal 2 - Frontend
cd frontend
npm install
npm run dev  # http://localhost:5173
```

### Backend dependencies (`backend/requirements.txt`)

```
fastapi
uvicorn[standard]
httpx
python-dotenv
pypdf                    # PDF parsing
python-docx              # DOCX parsing
anthropic
reportlab                # PDF export
pytest
pytest-asyncio
python-multipart
```

### Frontend dependencies (`frontend/package.json` key deps)

```json
{
  "dependencies": {
    "react": "^18.3",
    "react-dom": "^18.3",
    "react-router-dom": "^6.28",
    "@tanstack/react-query": "^5.62",
    "zustand": "^5.0",
    "@tiptap/react": "^2.10",
    "@tiptap/starter-kit": "^2.10",
    "sonner": "^1.7"
  }
}
```

### Backend structure

```
backend/
├── main.py                 # FastAPI app setup, CORS, include routers
├── database/
│   └── init.sql            # SQLite schema
├── storage/
│   ├── base.py             # StorageBackend interface
│   └── local.py            # LocalStorage impl
├── providers/
│   ├── base.py             # LLMProvider interface
│   ├── ollama.py           # Ollama Cloud
│   ├── anthropic.py        # Anthropic
│   └── registry.py         # Provider chain
├── parsers/
│   ├── base.py
│   ├── pdf.py
│   ├── docx.py
│   └── factory.py
├── services/
│   ├── styles.py           # Create/list/delete styles
│   ├── generate.py         # Generation + provider fallback
│   └── export.py           # PDF/DOCX rendering
├── routers/
│   ├── styles.py
│   ├── generate.py
│   └── export.py
└── .env.example
```

### Frontend structure

```
frontend/
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── lib/
│   │   └── api.ts
│   ├── queries/
│   │   └── hooks/
│   ├── components/
│   │   ├── Layout.tsx
│   │   ├── FileUploader.tsx
│   │   ├── GenerationEditor.tsx
│   │   └── ...
│   └── routes/
│       ├── StylesPage.tsx
│       └── GeneratePage.tsx
├── tailwind.config.js
└── vite.config.ts
```

---

## CORS, Environment & Blob Migration Path

### Health endpoint

Minimum v1 response:

```json
{ "status": "ok" }
```

Optional enhancement:

```json
{
  "status": "ok",
  "providers": {
    "ollama": true,
    "anthropic": false
  }
}
```

If provider details are not implemented, all docs should reflect the simpler response.

### CORS in FastAPI (`backend/main.py`)

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Frontend dev server
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Environment variables

`.env` (backend root, gitignored):
```bash
OLLAMA_API_KEY=...
ANTHROPIC_API_KEY=...
OLLAMA_MODEL=llama3.1
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
STORAGE_TYPE=local
STORAGE_BASE_DIR=./storage
```

`frontend/.env` (Vite):
```bash
VITE_API_URL=http://localhost:8000
```

### Blob migration path (when ready)

1. Implement `BlobStorage` class in `backend/storage/blob.py` using Azure Blob SDK.
2. Add env vars: `STORAGE_TYPE=blob`, `AZURE_CONNECTION_STRING`, `AZURE_CONTAINER`.
3. Update `storage/factory.py`:
   ```python
   def get_storage() -> StorageBackend:
       if os.getenv("STORAGE_TYPE") == "blob":
           return BlobStorage(...)
       return LocalStorage(...)
   ```
4. No code changes needed in services/parsers — they call `storage.save_file()`, `storage.get_file()` via the interface.
5. Migrate existing files: run a one-off script that uploads local `storage/documents/` to blob, updates SQLite `original_path` values.

Blob paths use the same keys (`documents/{doc_id}.{ext}`) — different backend, same layout.

---

## Summary

| Component | Tech | Purpose |
|-----------|------|---------|
| Frontend | Vite + React + Tiptap + TanStack Query | Upload styles, generate text, edit & export |
| Backend | FastAPI + SQLite + Ollama Cloud/Anthropic | Parse docs, manage styles, run LLM generation, render exports |
| Wiki | Markdown | Documents the codebase for LLM coding agents |

**Key flows:**
- **Create style:** Upload docs → parse to text → save to storage + SQLite
- **Generate:** Pick style + prompt → LLM reads style text → returns text (with provider indicator)
- **Export:** Edit in Tiptap → send plain text to `/export` → download PDF/DOCX

**No auth** for demo. **Local file storage** now, **Azure Blob** later (swap via env + interface).

For the MVP scaffold, prefer direct `sqlite3` access over introducing SQLAlchemy unless there is a clear immediate need for ORM behavior.
