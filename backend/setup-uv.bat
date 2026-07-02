@echo off
cd /d %~dp0
uv venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
uv pip install --python .\.venv\Scripts\python.exe -r requirements.txt
echo Backend venv is ready at backend\.venv
