# Pressor

Make audio smaller without changing what players hear.

Pressor is a perceptual audio optimization tool designed for game development pipelines, CI systems, and large-scale asset processing.

Version: v3.12.1  
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

```text
C:\Pressor\input
```

4. Run:

```text
run_windows.bat
```

5. Results are written to:

```text
C:\Pressor\output
```

---

### Linux

1. Clone the repository  
2. Run:

```bash
./setup_linux.sh
```

3. Place audio files into:

```text
~/Pressor/input
```

4. Run:

```bash
./run_linux.sh
```

5. Results are written to:

```text
~/Pressor/output
```

---

## Windows Runner Shortcuts

Use these from the extracted Pressor folder:

- `run_windows.bat` → default behavior (profile-driven)
- `run_windows_structured.bat` → structured output (`encoded/`, `skipped/`, `failed/`)
- `run_windows_opus.bat` → forces `.opus` output
- `run_windows_ogg.bat` → forces `.ogg` output

---

## Commands

### Standard Run

```bash
python pressor.py --input INPUT --output OUTPUT --auto-profile --skip-lossy-inputs
```

### Structured Output

```bash
python pressor.py --input INPUT --output OUTPUT --auto-profile --skip-lossy-inputs --structured-output
```

### Force Opus Output

```bash
python pressor.py --input INPUT --output OUTPUT --auto-profile --skip-lossy-inputs --output-format opus
```

### Force OGG Output

```bash
python pressor.py --input INPUT --output OUTPUT --auto-profile --skip-lossy-inputs --output-format ogg
```

### Lossy to OGG Conversion

```bash
python pressor.py --input INPUT --output OUTPUT --convert-lossy-to-ogg
```

### Validation

```bash
python pressor.py --doctor
python pressor.py --selftest
```

---

## Output Format Overrides

By default, Pressor uses profiles to determine output format.

Use `--output-format` when you want explicit control.

- `--output-format opus` → writes `.opus` using `libopus`  
- `--output-format ogg` → writes `.ogg` using `libopus`  

Behavior:

- output format overrides force both codec and container  
- auto-profile still controls tuning and classification  
- default profile behavior remains unchanged  

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

Examples:

- masked frequencies  
- low-impact detail in dense material  
- non-critical audio information  

The goal is reduced size without perceptible loss in gameplay.

---

## Wwise Pipeline Usage

Typical flow:

```text
Raw Audio -> Pressor -> Wwise Import -> SoundBank Build
```

Pressor:

- does not modify mix or gain structure  
- does not alter runtime playback  
- keeps Wwise as the source of truth  

---

## Structured Output

```bash
python pressor.py --structured-output
```

Creates:

```text
pressor_runs/<timestamp>/
  encoded/
  skipped/
  failed/
  reports/
```

Behavior:

- preserves folder structure  
- skipped and failed files are copied  
- designed for pipeline handoff  

---

## Lossy Input Handling

Pressor is intended for source-quality audio (WAV, FLAC).

Lossy inputs:

- are detected automatically  
- are skipped by default  
- can be processed intentionally  

### Normalize Lossy Inputs

```bash
python pressor.py --convert-lossy-to-ogg
```

Behavior:

- converts lossy formats (MP3, AAC, etc.) to `.ogg`  
- skips lossless inputs  
- preserves folder structure  

---

## Output Artifacts

Each run produces:

- `pressor_report.csv`  
- `pressor_failures.json`  
- `pressor_run.jsonl`  

Optional outputs include manifests and Wwise import data.

---

## Dependencies

Pressor installs required dependencies during setup.

- Python  
- FFmpeg  

If setup completes successfully, no additional steps are required.

Manual installation is supported for advanced environments.

---

## Security

Pressor runs locally and does not transmit data externally.

- uses FFmpeg for encoding  
- operates within configured input/output directories  
- does not modify source files  

Dependencies are installed using trusted package sources (WinGet) or user-provided binaries.

Best practices:

- use trusted source audio  
- review setup scripts before execution  

---

## Testing

```bash
pytest
```

---

Pressor is designed to be simple to run, predictable in behavior, and safe to integrate into production pipelines.
