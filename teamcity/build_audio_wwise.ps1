param(
    [string]$Python = "py",
    [string]$InputRoot = ".\AudioRaw",
    [string]$PreparedRoot = ".\AudioPrepared",
    [string]$ArtifactsRoot = ".\artifacts",
    [string]$DefaultProfile = "dialogue"
)

$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force -Path $PreparedRoot | Out-Null
New-Item -ItemType Directory -Force -Path $ArtifactsRoot | Out-Null

& $Python .\pressor.py --input $InputRoot --output $PreparedRoot --profile $DefaultProfile --wwise-prep --review-pack "$ArtifactsRoot\review_pack" --wwise-import-json-out "$ArtifactsRoot\wwise_import_starter.json" --wwise-import-tsv-out "$ArtifactsRoot\wwise_import_starter.tsv"
if ($LASTEXITCODE -ne 0) { throw "Pressor Wwise prep failed." }

Write-Host "Prepared audio in $PreparedRoot"
Write-Host "Starter Wwise mappings written to $ArtifactsRoot"
Write-Host "Next step: import the prepared WAV files into Wwise and generate SoundBanks."
