# Coding Standards

## Backend

- Keep routers thin.
- Put business logic in `services/`.
- Use direct `sqlite3` access for this scaffold.
- Prefer small, test-driven changes.

## Frontend

- Use TypeScript.
- Keep API calls in `src/lib/api.ts`.
- Keep route components small and compose from `components/`.
- Use TanStack Query for server-state helpers where practical.

## General

- Match docs to implemented behavior.
- Prefer minimal passing implementations first.
