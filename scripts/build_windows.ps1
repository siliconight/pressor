param(
    [switch]$Windowed
)

$ErrorActionPreference = 'Stop'

function Require-Command([string]$Name) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command not found on PATH: $Name"
    }
}

Require-Command py

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

$VenvPath = Join-Path $ProjectRoot '.venv-build'
if (-not (Test-Path $VenvPath)) {
    py -m venv $VenvPath
}

$PythonExe = Join-Path $VenvPath 'Scripts\python.exe'
if (-not (Test-Path $PythonExe)) {
    throw "Virtual environment python not found: $PythonExe"
}

& $PythonExe -m pip install --upgrade pip
& $PythonExe -m pip install pyinstaller
if (Test-Path requirements.txt) {
    & $PythonExe -m pip install -r requirements.txt
}

$Args = @(
    '-m', 'PyInstaller',
    '--noconfirm',
    '--clean',
    '--onefile',
    '--name', 'pressor',
    '--add-data', 'pressor.profiles.json;.',
    '--add-data', 'pressor.routing.json;.',
    '--add-data', 'pressor.wwise.json;.',
    '--add-data', 'assets;assets',
    '--icon', 'assets/pressor.ico'
)

if ($Windowed) {
    $Args += '--windowed'
}

$Args += 'pressor.py'

& $PythonExe @Args

Write-Host ''
Write-Host 'Build complete.' -ForegroundColor Green
Write-Host "Binary: $ProjectRoot\dist\pressor.exe"
Write-Host 'Reminder: FFmpeg and FFprobe must still be installed and available on PATH.'
