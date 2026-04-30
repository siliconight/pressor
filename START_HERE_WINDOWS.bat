\
@echo off
setlocal
cd /d "%~dp0"

echo.
echo ==========================================
echo Pressor First-Time Setup
echo ==========================================
echo.
echo This will run setup.bat.
echo.
echo Setup will:
echo - check for Python
echo - check for FFmpeg / FFprobe
echo - install dependencies through WinGet only if you approve
echo - create C:\Pressor\input and C:\Pressor\output
echo.
echo After setup finishes:
echo 1. Put audio files in C:\Pressor\input
echo 2. Run run_windows.bat
echo.
pause

call "%~dp0setup.bat"
exit /b %ERRORLEVEL%
