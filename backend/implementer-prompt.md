# Implementer Subagent Prompt

You are implementing Task 1 from the style-matching generator plan:

## Task: Scaffold backend application shell

**Files to create:**
- `backend/main.py`
- `backend/requirements.txt`
- `backend/.env.example`
- `backend/routers/__init__.py`
- `backend/routers/styles.py`
- `backend/routers/generate.py`
- `backend/routers/export.py`
- `backend/tests/test_health.py`

## Implementation Steps

### Step 1: Write the failing test
Create `backend/tests/test_health.py` with this test:

```python
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health_returns_ok_payload():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

### Step 2: Run test to verify it fails
Run: `cd backend && pytest tests/test_health.py -v`
Expected: FAIL with `ModuleNotFoundError` or missing `app`

### Step 3: Write minimal implementation

**backend/main.py:**
```python
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

**backend/routers/styles.py:**
```python
from fastapi import APIRouter

router = APIRouter(prefix="/styles", tags=["styles"])
```

**backend/routers/generate.py:**
```python
from fastapi import APIRouter

router = APIRouter(tags=["generate"])
```

**backend/routers/export.py:**
```python
from fastapi import APIRouter

router = APIRouter(tags=["export"])
```

**backend/requirements.txt:**
```
fastapi
uvicorn[standard]
pytest
httpx
python-multipart
```

**backend/.env.example:**
```
OLLAMA_API_KEY=
ANTHROPIC_API_KEY=
OLLAMA_MODEL=llama3.1
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
STORAGE_TYPE=local
STORAGE_BASE_DIR=./storage
DATABASE_URL=sqlite:///./storage/gpt-writer.db
```

### Step 4: Run test to verify it passes
Run: `cd backend && pytest tests/test_health.py -v`
Expected: PASS

### Step 5: Commit
```bash
git add backend/main.py backend/requirements.txt backend/.env.example backend/routers/__init__.py backend/routers/styles.py backend/routers/generate.py backend/routers/export.py backend/tests/test_health.py
git commit -m "chore: scaffold backend app structure"
```

## Context

- This is Task 1 in a 20-task implementation plan
- The project is `D:/gpt-writer` - a style-matching writing generator
- Use TDD: write tests first, then implement
- Keep the implementation minimal and passing
- Commit after each task
