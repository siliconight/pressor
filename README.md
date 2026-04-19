# Pressor

Reduce audio file size without perceptible quality loss.

Pressor is a perceptual audio optimization tool designed for game development pipelines and batch processing workflows.

Version: v3.2.5  
License: MIT

---

## Quick Start

### Windows

1. Download or clone this repository  
2. Run `setup.bat`  
3. Drop source-quality audio into:

```
C:\Pressor\input
```

4. Run:

```
run_windows.bat
```

5. Find results in:

```
C:\Pressor\output
```

---

### Linux

1. Clone the repository  
2. Run:

```
./setup_linux.sh
```

3. Drop source-quality audio into:

```
~/Pressor/input
```

4. Run:

```
./run_linux.sh
```

5. Find results in:

```
~/Pressor/output
```

---

## What Pressor Does

Pressor is built to:

- Reduce audio file size using perceptual encoding  
- Preserve perceived audio quality  
- Prevent accidental lossy reprocessing  
- Operate safely in batch and CI workflows  
- Produce consistent, deterministic outputs  

**Goal:**
> Reduce size without the end user noticing.

---

## How It Works

Pressor:
- analyzes audio characteristics
- selects encoding strategies automatically
- validates outputs
- produces review-ready comparison files

---

## Default Workspace

Pressor automatically creates a workspace:

### Windows
```
C:\Pressor\
  input\
  output\
  pressor.workspace.json
```

### Linux
```
~/Pressor/
  input/
  output/
  pressor.workspace.json
```

Each run creates a timestamped output:

```
output/
  2026-04-18_214233/
    encoded/
    review/
    reports/
```

---

## Common Commands

Check environment:
```
python pressor.py --doctor
```

Run self-test:
```
python pressor.py --selftest
```

Run using workspace defaults:
```
python pressor.py
```

Show workspace:
```
python pressor.py --show-workspace
```

Version:
```
python pressor.py --version
```

---

## Output Artifacts

Each run generates:

- `pressor_report.csv`
- `pressor_failures.json`
- `pressor_run.jsonl`

These include:
- encoding decisions
- errors and classifications
- FFmpeg command details
- diagnostics

---

## Documentation

- `docs/WINDOWS_SETUP.md`
- `docs/LINUX_SETUP.md`
- `docs/CI_BUILD_PIPELINE_SETUP.md`
- `docs/TEAMCITY_SETUP.md`

---

## Project Structure

```
pressor/
  pressor.py
  app.py
  encoder.py
  pressor/
    core/
    pipeline/
    cli/
    gui/
  scripts/
    install_windows.ps1
    run_windows.ps1
    install_linux.sh
    run_linux.sh
  docs/
  tests/
  setup.bat
  run_windows.bat
  setup_linux.sh
  run_linux.sh
  README.md
  LICENSE
  requirements.txt
```

---

## Dependencies

Pressor requires:

- Python 3.x  
- FFmpeg + FFprobe  

Setup scripts will attempt automatic installation where possible.

---

## Testing

Run all tests:

```
python -m unittest discover -s tests/unit -v
```

---

## Maintainer

Brannen Graves
