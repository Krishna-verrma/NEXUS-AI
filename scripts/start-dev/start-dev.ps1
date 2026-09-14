# Nexus AI - Windows PowerShell Development Launcher
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "   NEXUS AI - Launching Development Hive  " -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

$Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$BackendDir = Join-Path $Root "backend"
$FrontendDir = Join-Path $Root "frontend"

Write-Host "`n[1/2] Launching FastAPI Backend on http://localhost:8000..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$BackendDir'; python -m uvicorn app.main:app --reload --port 8000"

Write-Host "`n[2/2] Launching Vite Frontend on http://localhost:5173..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$FrontendDir'; npm.cmd run dev"

Write-Host "`nNexus AI Development servers are initializing in dedicated windows." -ForegroundColor Green
Write-Host "Frontend: http://localhost:5173" -ForegroundColor Green
Write-Host "Backend API: http://localhost:8000/docs" -ForegroundColor Green
