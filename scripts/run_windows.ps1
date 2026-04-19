Write-Host ""
Write-Host "=== Pressor Run ==="
Write-Host ""
Write-Host "Running Pressor using the saved workspace defaults."
Write-Host ""

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptRoot
Set-Location $RepoRoot

$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
$pyCmd = Get-Command py -ErrorAction SilentlyContinue

if ($pythonCmd) {
    $PYTHON="python"
} elseif ($pyCmd) {
    $PYTHON="py"
} else {
    Write-Host "ERROR: Python not found."
    exit 1
}

& $PYTHON pressor.py --auto-profile --fail-on-lossy-inputs
exit $LASTEXITCODE
