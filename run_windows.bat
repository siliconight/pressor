@echo off
setlocal
cd /d "%~dp0"
echo.
echo === Pressor Run ===
echo.
if not exist "scripts\run_windows.ps1" (
    echo ERROR: scripts\run_windows.ps1 was not found.
    exit /b 1
)
powershell -ExecutionPolicy Bypass -File "%~dp0scripts\run_windows.ps1"
exit /b %ERRORLEVEL%
