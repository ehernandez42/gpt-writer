# API Reference

## Health
- `GET /health` -> `{ "status": "ok" }`

## Styles
- `POST /styles`
- `GET /styles`
- `GET /styles/{id}`
- `DELETE /styles/{id}`

## Generation
- `POST /generate`
- `GET /generations/{id}`

## Export
- `POST /export`
  - request body: `{ "text": string, "format": "pdf" | "docx" }`
