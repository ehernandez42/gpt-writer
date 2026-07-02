# Architecture

## Backend

FastAPI app with thin routers and service-layer modules.

Key folders:
- `routers/` HTTP endpoints
- `services/` business logic
- `providers/` Ollama and Anthropic provider implementations
- `parsers/` txt/md/pdf/docx parsing
- `storage/` local storage abstraction
- `database/` sqlite schema and connection helpers

## Frontend

Vite + React + TypeScript with React Router.

Key folders:
- `src/routes/` page-level UI
- `src/components/` reusable UI pieces
- `src/lib/` API client and query client
- `src/queries/hooks/` query helpers

## Storage layout

- `storage/documents/{doc_id}.{ext}`
- `storage/extracted/{doc_id}.txt`
- `storage/extracted/{style_id}.combined.txt`
- `storage/gpt-writer.db`

## Provider strategy

Preferred order:
1. Ollama
2. Anthropic fallback

## Implementation notes

Design docs call for atomic style upload and a bounded combined-text cap. The code scaffold should be checked against those requirements during verification.
