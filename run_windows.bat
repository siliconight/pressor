@echo off
setlocal
cd /d "%~dp0"

echo.
echo ==========================================
echo Pressor Run
echo ==========================================
echo Using saved workspace defaults.
echo Input:  C:\Pressor\input
echo Output: C:\Pressor\output
echo.
echo Progress will be shown below.
echo.

if not exist "scripts\run_windows.ps1" (
    echo ERROR: scripts\run_windows.ps1 was not found.
    echo.
    pause
    exit /b 1
)

powershell -ExecutionPolicy Bypass -File "%~dp0scripts\run_windows.ps1"
set EXITCODE=%ERRORLEVEL%

echo.
if %EXITCODE% neq 0 (
    echo Pressor run did not complete successfully.
    echo Check the terminal output and reports in the latest run folder. Lossy files may now be skipped while the rest continue.
    echo.
    pause
    exit /b %EXITCODE%
)

echo Pressor run completed successfully.
echo Check C:\Pressor\output for the latest timestamped run folder.
echo.
pause
exit /b 0
