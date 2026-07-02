# Troubleshooting

## Backend import errors
- Verify requirements are installed.
- Run commands from `backend/`.

## Frontend test failures
- Run `npm install` first.
- Confirm Vitest and Testing Library packages are installed.

## Provider unavailable
- Check `OLLAMA_API_KEY` and `ANTHROPIC_API_KEY`.
- Confirm network access to provider APIs.

## CORS issues
- Frontend dev server should use `http://localhost:5173`.
- Backend CORS config should allow that origin.
