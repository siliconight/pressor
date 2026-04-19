Write-Host ""
Write-Host "=== Pressor Windows Setup ==="
Write-Host ""

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptRoot
Set-Location $RepoRoot

function Get-PythonCommand {
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCmd) { return "python" }
    $pyCmd = Get-Command py -ErrorAction SilentlyContinue
    if ($pyCmd) { return "py" }
    return $null
}

function Test-CommandAvailable {
    param([string]$Name)
    return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

function Confirm-YesNo {
    param([string]$Prompt, [bool]$DefaultYes = $true)
    $suffix = if ($DefaultYes) { " [Y/n]" } else { " [y/N]" }
    $reply = Read-Host "$Prompt$suffix"
    if ([string]::IsNullOrWhiteSpace($reply)) { return $DefaultYes }
    switch ($reply.Trim().ToLowerInvariant()) {
        "y" { return $true }
        "yes" { return $true }
        "n" { return $false }
        "no" { return $false }
        default { return $DefaultYes }
    }
}

function Refresh-PathFromSystem {
    $machine = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $user = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($machine -and $user) { $env:Path = "$machine;$user" }
    elseif ($machine) { $env:Path = $machine }
    elseif ($user) { $env:Path = $user }
}

function Test-FFmpegReady {
    if (-not (Test-CommandAvailable "ffmpeg")) { return $false }
    if (-not (Test-CommandAvailable "ffprobe")) { return $false }
    & ffmpeg -version *> $null
    if ($LASTEXITCODE -ne 0) { return $false }
    & ffprobe -version *> $null
    return $LASTEXITCODE -eq 0
}

function Install-FFmpegWithWinget {
    Write-Host ""
    Write-Host "Attempting FFmpeg install with winget..."
    winget install -e --id Gyan.FFmpeg --accept-package-agreements --accept-source-agreements
    return $LASTEXITCODE -eq 0
}

function Install-FFmpegWithChoco {
    Write-Host ""
    Write-Host "Attempting FFmpeg install with Chocolatey..."
    choco install ffmpeg -y
    return $LASTEXITCODE -eq 0
}

function Show-ManualFFmpegInstructions {
    Write-Host ""
    Write-Host "FFmpeg is still not available."
    Write-Host "Manual install:"
    Write-Host "1. Open: https://ffmpeg.org/download.html"
    Write-Host "2. Under Windows, choose one of the linked builds"
    Write-Host "3. Extract to: C:\ffmpeg"
    Write-Host "4. Add to PATH: C:\ffmpeg\bin"
    Write-Host "5. Open a new terminal and re-run setup"
    Write-Host ""
}

$PYTHON = Get-PythonCommand
if (-not $PYTHON) {
    Write-Host "ERROR: Python not found."
    Write-Host "Install Python from https://www.python.org/downloads/"
    Write-Host "Make sure to check 'Add Python to PATH'"
    exit 1
}

Write-Host "Python found: $PYTHON"
& $PYTHON --version
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Python is installed but could not be executed."
    exit 1
}

$requirementsPath = Join-Path $RepoRoot "requirements.txt"
if (-not (Test-Path $requirementsPath)) {
    Write-Host "ERROR: requirements.txt not found in: $RepoRoot"
    exit 1
}

Write-Host ""
Write-Host "Upgrading pip, setuptools, and wheel..."
& $PYTHON -m pip install --upgrade pip setuptools wheel
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to prepare Python packaging tools."
    exit 1
}

Write-Host ""
Write-Host "Installing Pressor Python dependencies..."
& $PYTHON -m pip install -r $requirementsPath
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install Python dependencies."
    exit 1
}

Write-Host ""
Write-Host "Installing optional GUI drag-and-drop support..."
& $PYTHON -m pip install tkinterdnd2
if ($LASTEXITCODE -ne 0) {
    Write-Host "WARNING: Could not install tkinterdnd2."
    Write-Host "The GUI will still work, but in-window drag and drop may not."
}

Write-Host ""
Write-Host "Checking FFmpeg..."
if (-not (Test-FFmpegReady)) {
    Write-Host "FFmpeg and/or FFprobe not found."
    if (Test-CommandAvailable "winget") {
        if (Confirm-YesNo "Install FFmpeg automatically using winget?") {
            $ok = Install-FFmpegWithWinget
            if (-not $ok) { Write-Host "WARNING: winget install did not complete successfully." }
            Refresh-PathFromSystem
        }
    } elseif (Test-CommandAvailable "choco") {
        if (Confirm-YesNo "Install FFmpeg automatically using Chocolatey?") {
            $ok = Install-FFmpegWithChoco
            if (-not $ok) { Write-Host "WARNING: Chocolatey install did not complete successfully." }
            Refresh-PathFromSystem
        }
    } else {
        Write-Host "Neither winget nor Chocolatey was found."
    }
    if (-not (Test-FFmpegReady)) {
        Write-Host ""
        Write-Host "Pressor still cannot find FFmpeg in the current terminal."
        Write-Host "If you just installed it, close this terminal and open a new one, then run setup again."
        Show-ManualFFmpegInstructions
        exit 1
    }
}

Write-Host ""
Write-Host "FFmpeg detected:"
& ffmpeg -version | Select-Object -First 1
Write-Host "FFprobe detected:"
& ffprobe -version | Select-Object -First 1

$defaultWorkspace = "C:\Pressor"
Write-Host ""
Write-Host "Initializing Pressor workspace at: $defaultWorkspace"
& $PYTHON pressor.py --init --workspace-root $defaultWorkspace
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Workspace initialization failed."
    exit 1
}

Write-Host ""
Write-Host "Running Pressor doctor check..."
& $PYTHON pressor.py --doctor
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "WARNING: Pressor doctor reported a problem."
    Write-Host "Fix the reported issue before continuing."
    exit 1
}

$inputFolder = Join-Path $defaultWorkspace "input"
$outputFolder = Join-Path $defaultWorkspace "output"

Write-Host ""
Write-Host "=== Setup Complete ==="
Write-Host ""
Write-Host "Pressor workspace: $defaultWorkspace"
Write-Host "Input folder      : $inputFolder"
Write-Host "Output root       : $outputFolder"
Write-Host ""
Write-Host "The input folder will open now. Put source-quality audio there, then run run_windows.bat."
Start-Process explorer.exe $inputFolder
