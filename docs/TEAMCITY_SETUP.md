# Pressor – TeamCity Setup Guide

This guide explains how to run Pressor in TeamCity as part of a build or asset-processing pipeline.

Pressor is well suited for TeamCity because it is:
- headless
- scriptable
- deterministic
- batch-oriented
- able to produce machine-readable logs and reports

## What TeamCity should use Pressor for

Use Pressor in TeamCity when you want to:
- reduce the size of source-quality audio assets
- enforce consistent audio processing rules across teams
- prepare audio for downstream systems such as Wwise
- block lossy re-processing in production workflows
- produce reports for debugging and audit

## Recommended pipeline shape

A typical TeamCity flow looks like this:

```text
Source Sync
→ Pressor Doctor Check
→ Pressor Audio Processing
→ Optional Wwise Prep
→ Package / Build / Publish
```

## Prerequisites on the TeamCity agent

Each TeamCity build agent that runs Pressor should have:

- Python 3 installed
- FFmpeg installed and on PATH
- FFprobe installed and on PATH
- Pressor checked out or copied onto disk

Verify manually on the agent first:

```bash
python3 pressor.py --doctor
```

On Windows agents:

```bat
python pressor.py --doctor
```

## Recommended routing model

Use folder-based routing as the primary signal.

Example mappings:

```text
VO/** -> dialogue
Ambient/** -> ambient
Music/** -> music
SFX/** -> sfx
Foley/** -> sfx
```

For production TeamCity jobs, `--strict-routing` is strongly recommended.

## Recommended Pressor command for TeamCity

For standard production processing:

### Linux agent
```bash
python3 pressor.py --input ./AudioRaw --output ./AudioOut --auto-profile --strict-routing --fail-on-lossy-inputs
```

### Windows agent
```bat
python pressor.py --input .\AudioRaw --output .\AudioOut --auto-profile --strict-routing --fail-on-lossy-inputs
```

## Recommended command for Wwise-safe prep

If your project uses Wwise and wants prepared WAV outputs:

### Linux agent
```bash
python3 pressor.py --input ./AudioRaw --output ./AudioPrepared --auto-profile --strict-routing --fail-on-lossy-inputs --wwise-prep --wwise-safe
```

### Windows agent
```bat
python pressor.py --input .\AudioRaw --output .\AudioPrepared --auto-profile --strict-routing --fail-on-lossy-inputs --wwise-prep --wwise-safe
```

## TeamCity step structure

A good TeamCity build configuration can use three command-line steps.

### Step 1: Environment validation

#### Linux
```bash
python3 pressor.py --doctor
```

#### Windows
```bat
python pressor.py --doctor
```

### Step 2: Audio processing

#### Linux
```bash
python3 pressor.py --input ./AudioRaw --output ./AudioOut --auto-profile --strict-routing --fail-on-lossy-inputs
```

#### Windows
```bat
python pressor.py --input .\AudioRaw --output .\AudioOut --auto-profile --strict-routing --fail-on-lossy-inputs
```

### Step 3: Publish artifacts

Publish:
- processed audio output
- `pressor_report.csv`
- `pressor_failures.json`
- `pressor_run.jsonl`

## TeamCity artifact paths

Recommended artifact publication rules:

```text
AudioOut => AudioOut
pressor_report.csv => Reports
pressor_failures.json => Reports
pressor_run.jsonl => Reports
```

## Using review packs in TeamCity

Review packs are usually best for:
- validation runs
- profile tuning runs
- QA review runs

They are usually not needed on every production build.

## Recommended TeamCity build parameters

You may want to expose these as TeamCity parameters:

- input root
- output root
- review pack enabled
- Wwise prep enabled
- strict routing enabled

Example parameterized command:

```bash
python3 pressor.py --input %env.AUDIO_INPUT% --output %env.AUDIO_OUTPUT% --auto-profile --strict-routing --fail-on-lossy-inputs
```

## Error handling and diagnostics

Pressor writes structured diagnostics that are helpful in TeamCity.

Files to archive:
- `pressor_report.csv`
- `pressor_failures.json`
- `pressor_run.jsonl`

Important error codes include:
- `P1001` input path or source file missing
- `P1002` output nested inside input
- `P1101` FFmpeg or FFprobe missing
- `P1102` permission problem
- `P1301` encode or prep failed
- `P1302` output verification failed
- `P1303` FFmpeg timed out
- `P1401` manifest invalid
- `P1501` lossy input blocked
- `P9001` unexpected internal error

If a TeamCity build fails, check:
1. console output
2. `pressor_failures.json`
3. `pressor_run.jsonl`

## Best practices for TeamCity use

- Use source-quality audio
- Fail on lossy input
- Prefer strict routing
- Archive reports
- Validate on real content before full rollout


Note: Pressor creates a new timestamped run folder inside the selected output root by default. Use `--flat-output` only if you intentionally want to write directly into the selected output folder.
