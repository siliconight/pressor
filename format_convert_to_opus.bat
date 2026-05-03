@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo.
echo ==========================================
echo Pressor Format Conversion: Opus
echo ==========================================
echo.

set "PYTHON="
where py >nul 2>nul
if %errorlevel%==0 (
    py -3 --version >nul 2>nul
    if %errorlevel%==0 (
        set "PYTHON=py -3"
    )
)

if not defined PYTHON (
    where python >nul 2>nul
    if %errorlevel%==0 (
        set "PYTHON=python"
    )
)

if not defined PYTHON (
    echo ERROR: Python was not found on PATH.
    echo Run setup.bat first, or install Python and try again.
    echo.
    pause
    exit /b 1
)

set "INPUTDIR=C:\Pressor\input"
set "OUTPUTDIR=C:\Pressor\output"

if not exist "%INPUTDIR%" mkdir "%INPUTDIR%"
if not exist "%OUTPUTDIR%" mkdir "%OUTPUTDIR%"

echo Input : %INPUTDIR%
echo Output: %OUTPUTDIR%
echo Mode  : Format Conversion
echo Target: opus
echo.

echo Running environment check...
%PYTHON% pressor.py --doctor
if %ERRORLEVEL% neq 0 (
    echo.
    echo Pressor is not ready to run yet.
    echo Run setup.bat again, then retry.
    echo.
    pause
    exit /b 1
)

echo.
echo Checking for supported audio files...
%PYTHON% -c "from pathlib import Path; from encoder import ALLOWED_INPUT_EXTENSIONS; import sys; root=Path(r'%INPUTDIR%'); files=[p for p in root.rglob('*') if p.is_file() and p.suffix.lower() in ALLOWED_INPUT_EXTENSIONS]; print(f'Found {len(files)} supported audio file(s).'); sys.exit(0 if files else 3)"
if %ERRORLEVEL% neq 0 (
    echo.
    echo No supported audio files were found in:
    echo %INPUTDIR%
    echo.
    echo Add audio files, then run this again.
    start "" "%INPUTDIR%"
    pause
    exit /b 0
)

echo.
echo Starting Pressor Format Conversion Mode to Opus...
echo.
%PYTHON% pressor.py --input "%INPUTDIR%" --output "%OUTPUTDIR%" --format-conversion --target-format opus --structured-output --benchmark
set "EXITCODE=%ERRORLEVEL%"

echo.
if %EXITCODE% neq 0 (
    echo Pressor format conversion did not complete successfully.
    echo Check the terminal output and reports in the latest run folder.
    echo.
    pause
    exit /b %EXITCODE%
)

echo Pressor format conversion completed successfully.
echo Check C:\Pressor\output for the latest timestamped run folder.
echo.
pause
exit /b 0
