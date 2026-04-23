@echo off
setlocal EnableExtensions

echo.
echo ==========================================
echo Pressor Windows Setup
echo ==========================================
echo.

set "PYTHON="

call :FindPython
if defined PYTHON goto :PythonReady

echo Python was not found.
echo.
echo Pressor needs Python 3.10 or newer.
echo Setup can try to install Python 3.12 using WinGet.
echo.

choice /C YN /M "Install Python 3.12 now with WinGet"
if errorlevel 2 goto :ManualPython

call :RequireWinget
if errorlevel 1 goto :ManualPython

echo.
echo Installing Python 3.12 with WinGet...
echo This may open an installer or prompt for permission.
echo.
winget install --id Python.Python.3.12 --exact --source winget --accept-package-agreements --accept-source-agreements

if errorlevel 1 (
    echo.
    echo Python installation through WinGet did not complete successfully.
    goto :ManualPython
)

echo.
echo Python install command completed.
echo.
echo Windows may need a new terminal session before Python is visible.
echo Close this window, open a new Command Prompt, and run setup.bat again.
echo.
pause
exit /b 0

:PythonReady
echo Python found:
%PYTHON% --version
echo.

echo Checking pip...
%PYTHON% -m pip --version >nul 2>nul
if errorlevel 1 (
    echo.
    echo pip was not found. Trying to enable pip with ensurepip...
    %PYTHON% -m ensurepip --upgrade
    if errorlevel 1 (
        echo.
        echo ERROR: pip could not be enabled.
        goto :ManualPython
    )
)

echo pip is available.
echo.

echo Installing Pressor Python dependencies...
echo This can take a minute on first run.
echo.
%PYTHON% -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo ERROR: Failed to install Pressor Python dependencies.
    echo Check your internet connection, proxy, firewall, or Python install.
    pause
    exit /b 1
)

echo.
echo Checking FFmpeg and FFprobe...
call :FindFfmpeg
if not errorlevel 1 goto :FfmpegReady

echo.
echo FFmpeg and/or FFprobe were not found.
echo.
echo Pressor needs FFmpeg and FFprobe for audio inspection and encoding.
echo Setup can try to install FFmpeg through WinGet using the Gyan.FFmpeg package.
echo.

choice /C YN /M "Install FFmpeg now with WinGet"
if errorlevel 2 goto :ManualFfmpeg

call :RequireWinget
if errorlevel 1 goto :ManualFfmpeg

echo.
echo Installing FFmpeg with WinGet...
echo.
winget install --id Gyan.FFmpeg --exact --source winget --accept-package-agreements --accept-source-agreements

if errorlevel 1 (
    echo.
    echo FFmpeg installation through WinGet did not complete successfully.
    goto :ManualFfmpeg
)

echo.
echo FFmpeg install command completed.
echo Refreshing this command window PATH...
call :RefreshPath

call :FindFfmpeg
if not errorlevel 1 goto :FfmpegReady

echo.
echo FFmpeg may have installed, but this command window cannot see it yet.
echo Close this window, open a new Command Prompt, and run setup.bat again.
echo.
pause
exit /b 0

:FfmpegReady
echo FFmpeg found:
ffmpeg -version | findstr /B /C:"ffmpeg version"
echo FFprobe found:
ffprobe -version | findstr /B /C:"ffprobe version"
echo.

echo Running Pressor doctor...
echo.
%PYTHON% pressor.py --doctor
if errorlevel 1 (
    echo.
    echo Doctor found issues. Review the messages above.
    echo Setup will still create the workspace.
    echo.
)

set "WORKDIR=C:\Pressor"
set "INPUTDIR=%WORKDIR%\input"
set "OUTPUTDIR=%WORKDIR%\output"

if not exist "%INPUTDIR%" mkdir "%INPUTDIR%"
if not exist "%OUTPUTDIR%" mkdir "%OUTPUTDIR%"

echo.
echo Workspace ready:
echo Input : %INPUTDIR%
echo Output: %OUTPUTDIR%
echo.

echo Opening input folder...
start "" "%INPUTDIR%"

echo.
echo ==========================================
echo Setup complete
echo ==========================================
echo.
echo Next:
echo 1. Drop audio files into C:\Pressor\input
echo 2. Run run_windows.bat
echo.
pause
exit /b 0

:FindPython
where py >nul 2>nul
if not errorlevel 1 (
    py -3.12 --version >nul 2>nul
    if not errorlevel 1 (
        set "PYTHON=py -3.12"
        exit /b 0
    )
    py -3 --version >nul 2>nul
    if not errorlevel 1 (
        set "PYTHON=py -3"
        exit /b 0
    )
)

where python >nul 2>nul
if not errorlevel 1 (
    python --version >nul 2>nul
    if not errorlevel 1 (
        set "PYTHON=python"
        exit /b 0
    )
)

where python3 >nul 2>nul
if not errorlevel 1 (
    python3 --version >nul 2>nul
    if not errorlevel 1 (
        set "PYTHON=python3"
        exit /b 0
    )
)

exit /b 0

:FindFfmpeg
where ffmpeg >nul 2>nul
if errorlevel 1 exit /b 1
where ffprobe >nul 2>nul
if errorlevel 1 exit /b 1
exit /b 0

:RequireWinget
where winget >nul 2>nul
if errorlevel 1 (
    echo.
    echo WinGet is not available on this machine.
    exit /b 1
)
exit /b 0

:RefreshPath
for /f "tokens=2,*" %%A in ('reg query "HKCU\Environment" /v Path 2^>nul') do set "USERPATH=%%B"
for /f "tokens=2,*" %%A in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v Path 2^>nul') do set "SYSTEMPATH=%%B"
if defined SYSTEMPATH set "PATH=%SYSTEMPATH%;%PATH%"
if defined USERPATH set "PATH=%PATH%;%USERPATH%"
exit /b 0

:ManualPython
echo.
echo Manual Python install required.
echo.
echo 1. Open:
echo    https://www.python.org/downloads/windows/
echo.
echo 2. Download Python 3.12 or newer.
echo.
echo 3. During install, check:
echo    Add python.exe to PATH
echo.
echo 4. Close this window, open a new Command Prompt, and run setup.bat again.
echo.
pause
exit /b 1

:ManualFfmpeg
echo.
echo Manual FFmpeg install required.
echo.
echo Recommended Windows path:
echo 1. Open a new Command Prompt.
echo 2. Run:
echo    winget install --id Gyan.FFmpeg --exact --source winget
echo.
echo If WinGet is blocked or unavailable, ask your IT/admin team to install FFmpeg and FFprobe
echo and make sure both commands are available on PATH:
echo    ffmpeg
echo    ffprobe
echo.
pause
exit /b 1
