@echo off
setlocal
cd /d "%~dp0"
echo.
echo === Pressor Windows Setup ===
echo This will install dependencies, initialize C:\Pressor, and open the input folder.
echo.
if not exist "scripts\install_windows.ps1" (
    echo ERROR: scripts\install_windows.ps1 was not found.
    exit /b 1
)
powershell -ExecutionPolicy Bypass -File "%~dp0scripts\install_windows.ps1"
exit /b %ERRORLEVEL%
