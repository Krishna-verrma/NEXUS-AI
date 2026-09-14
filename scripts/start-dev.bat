@echo off
echo ========================================================
echo Launching NEXUS AI Desktop Development Environment...
echo ========================================================
cd /d "%~dp0\.."
call npm.cmd run dev
pause
