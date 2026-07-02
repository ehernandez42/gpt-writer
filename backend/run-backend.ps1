$ErrorActionPreference = 'Stop'

Set-Location $PSScriptRoot

if (-not (Test-Path .\.venv\Scripts\python.exe)) {
  Write-Error 'Virtual environment not found. Run .\setup-uv.ps1 first.'
}

.\.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
