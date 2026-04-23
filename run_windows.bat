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

where python >nul 2>nul
if %errorlevel%==0 (
    set "PYTHON=python"
) else (
    where py >nul 2>nul
    if %errorlevel%==0 (
        set "PYTHON=py"
    ) else (
        echo ERROR: Python was not found on PATH.
        echo Run setup.bat first, or install Python and try again.
        echo.
        pause
        exit /b 1
    )
)

%PYTHON% pressor.py --auto-profile --skip-lossy-inputs --benchmark
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
