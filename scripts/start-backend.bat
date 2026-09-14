@echo off
echo ========================================================
echo Starting NEXUS AI Backend (FastAPI + SQLite)...
echo ========================================================
cd /d "%~dp0\.."
call .\backend\venv\Scripts\activate
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
pause
