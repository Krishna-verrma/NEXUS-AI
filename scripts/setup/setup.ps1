# Nexus AI - Environment Initialization
Write-Host "Installing all dependencies across Frontend, Backend, and Desktop..." -ForegroundColor Cyan

$Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

Write-Host "`n[1/3] Backend Python dependencies..." -ForegroundColor Yellow
Set-Location (Join-Path $Root "backend")
python -m pip install -r requirements.txt

Write-Host "`n[2/3] Frontend npm packages..." -ForegroundColor Yellow
Set-Location (Join-Path $Root "frontend")
npm.cmd install

Write-Host "`n[3/3] Desktop Electron packages..." -ForegroundColor Yellow
Set-Location (Join-Path $Root "desktop")
npm.cmd install

Write-Host "`nNexus AI setup complete!" -ForegroundColor Green
