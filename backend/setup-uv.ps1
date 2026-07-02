$ErrorActionPreference = 'Stop'

Set-Location $PSScriptRoot

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
  Write-Error 'uv is not installed or not on PATH.'
}

uv venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
uv pip install --python .\.venv\Scripts\python.exe -r requirements.txt

Write-Host 'Backend venv is ready at backend\.venv' -ForegroundColor Green
