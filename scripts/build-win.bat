@echo off
echo ========================================================
echo Building NEXUS AI Windows Production Package...
echo ========================================================
cd /d "%~dp0\.."
call npm.cmd run build
echo.
echo Packaging complete! Check release/ directory for installer.
pause
