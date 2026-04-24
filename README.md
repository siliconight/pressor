# Pressor

Make audio smaller without changing what players hear.

Pressor is a perceptual audio optimization tool designed for game development pipelines, CI systems, and large-scale asset processing.

Version: v3.10.6  
License: MIT

---

## Why Pressor

Game audio often contains more data than players can perceive.

Pressor reduces that footprint to:

- shrink install sizes  
- reduce patch sizes  
- lower bandwidth and CDN costs  
- speed up downloads and updates  

This is not about changing audio.

It is about removing data that does not materially impact the player experience.

---

## What Pressor Demonstrates

Pressor is built to prove three things in real production pipelines:

- measurable reduction in packaged build size  
- deterministic behavior suitable for CI and Perforce workflows  
- clean integration into Wwise with no runtime impact  

The goal is not compression alone.

The goal is safe, repeatable optimization at scale.

---

## Quick Start

### Windows

1. Download the latest release  
2. Run `setup.bat`  
3. Place audio files into:

C:\Pressor\input

4. Run:

run_windows.bat

5. Results are written to:

C:\Pressor\output

---

### Linux

1. Clone the repository  
2. Run:

./setup_linux.sh

3. Place audio files into:

~/Pressor/input

4. Run:

./run_linux.sh

5. Results are written to:

~/Pressor/output

---

## Commands

Run using workspace defaults:

python pressor.py

Explicit run:

python pressor.py --input INPUT --output OUTPUT --auto-profile --skip-lossy-inputs

Structured output:

python pressor.py --input INPUT --output OUTPUT --auto-profile --skip-lossy-inputs --structured-output

Wwise-oriented run:

python pressor.py --input INPUT --output OUTPUT --auto-profile --wwise-mode --wwise-prep

Changed-only incremental run:

python pressor.py --changed-only --benchmark

Environment check:

python pressor.py --doctor

Self-test:

python pressor.py --selftest

---

## Run Behavior

Each run provides:

- total files detected  
- per-file processing status  
- encoded, skipped, and failed classification  
- output location  
- optional benchmark summary  

Outputs are written to timestamped folders for traceability.

---

## Structured Output

Optional pipeline-friendly structure:

python pressor.py --structured-output

Creates:

pressor_runs/<timestamp>/
  encoded/
  skipped/
  failed/
  reports/

- disabled by default  
- preserves source folder structure  
- skipped and failed files are copied, not moved  
- does not affect hashing or change detection  

---

## How It Works

Pressor applies perceptual encoding in a controlled batch workflow:

1. scan input audio  
2. classify content  
3. apply encoding strategy  
4. validate output  
5. write results and reports  

### Perceptual Encoding

Pressor reduces size by removing data that is unlikely to be perceived.

- masked frequencies  
- low-impact detail in dense material  
- non-critical audio information  

The target is not minimum size.

The target is reduced size without perceptible loss in gameplay.

---

## Wwise Pipeline Usage

Typical flow:

Raw Audio -> Pressor -> Wwise Import -> SoundBank Build

Pressor:

- does not modify mix or gain structure  
- does not alter runtime playback  
- keeps Wwise as the source of truth  

Recommended usage:

python pressor.py --wwise-mode --structured-output

---

## Determinism and Incremental Processing

With `--changed-only`:

- only modified assets are processed  
- unchanged assets are skipped  
- a persistent state manifest is used  
- repeated runs avoid unnecessary work  

This keeps builds stable and reduces churn.

---

## Benchmarking

python pressor.py --benchmark

Outputs:

- input size  
- output size  
- reduction percentage  

---

## Workspace

### Windows

C:\Pressor\
  input\
  output\

### Linux

~/Pressor/
  input/
  output/

Each run produces a timestamped output folder.

---

## Dependency Installation and Security

Pressor installs dependencies using WinGet when approved during setup.

- Python -> Python.Python.3.12  
- FFmpeg -> Gyan.FFmpeg  

This approach:

- uses Microsoft’s package manager  
- installs from known package IDs  
- avoids bundling third-party binaries  
- keeps installation explicit and user-approved  

Manual setup is supported if required.

---

## Lossy Input Handling

Pressor is intended for source-quality audio (WAV, FLAC).

Lossy inputs:

- are detected automatically  
- are skipped by default  
- can be processed intentionally when required  

---

## Output Artifacts

Each run produces:

- pressor_report.csv  
- pressor_failures.json  
- pressor_run.jsonl  

Optional outputs include manifests and Wwise import data.

---

## Security

Pressor runs locally and does not transmit data externally.

- operates within the configured workspace  
- relies on FFmpeg for encoding and inspection  
- validates output paths against the workspace root  

Best practices:

- use trusted source audio  
- avoid untrusted media inputs  
- review setup scripts before execution  

---

## Testing

pytest

---

## Maintainer

Brannen Graves
