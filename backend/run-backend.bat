@echo off
cd /d %~dp0
if not exist .\.venv\Scripts\python.exe (
  echo Virtual environment not found. Run setup-uv.bat first.
  exit /b 1
)
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
