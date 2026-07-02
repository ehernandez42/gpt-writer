# Setup

## Backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

## Frontend

```powershell
cd frontend
npm install
npm run dev
```

## Test commands

Backend:
```powershell
cd backend
python -m pytest -v
```

Frontend:
```powershell
cd frontend
npm test -- --runInBand
```

## Environment

Backend vars:
- `OLLAMA_API_KEY`
- `ANTHROPIC_API_KEY`
- `OLLAMA_MODEL`
- `ANTHROPIC_MODEL`
- `STORAGE_TYPE`
- `STORAGE_BASE_DIR`
- `DATABASE_URL`
