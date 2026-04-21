Write-Host ""
Write-Host "=========================================="
Write-Host "Pressor Run"
Write-Host "=========================================="
Write-Host ""

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptRoot
Set-Location $RepoRoot

$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
$pyCmd = Get-Command py -ErrorAction SilentlyContinue

if ($pythonCmd) {
    $PYTHON = "python"
} elseif ($pyCmd) {
    $PYTHON = "py"
} else {
    Write-Host "ERROR: Python not found."
    exit 1
}

Write-Host "Running Pressor using saved workspace defaults..."
Write-Host "Workspace input:  C:\Pressor\input"
Write-Host "Workspace output: C:\Pressor\output"
Write-Host ""
Write-Host "Starting processing..."
Write-Host ""

& $PYTHON pressor.py --auto-profile --fail-on-lossy-inputs --changed-only --benchmark
$EXITCODE = $LASTEXITCODE

Write-Host ""
if ($EXITCODE -eq 0) {
    Write-Host "Pressor finished successfully."
    Write-Host "Open C:\Pressor\output to find the latest run folder."
} else {
    Write-Host "Pressor finished with errors."
    Write-Host "Check the latest reports in C:\Pressor\output."
}

exit $EXITCODE
