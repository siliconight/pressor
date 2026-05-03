# Pressor

Make audio smaller without changing what players hear.

Pressor is a perceptual audio optimization tool designed for game development pipelines, CI systems, and large-scale asset processing.

Version: v3.13.0  
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

## Quick Start

### Windows

1. Download the latest release  
2. Run `setup.bat`  
3. Place audio files into:

```
C:\Pressor\input
```

4. Run:

```
run_windows.bat
```

5. Results are written to:

```
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

```
~/Pressor/input
```

4. Run:

```bash
./run_linux.sh
```

5. Results are written to:

```
~/Pressor/output
```

---

## Windows Runner Shortcuts

- `run_windows.bat` → default behavior (profile-driven)
- `run_windows_structured.bat` → structured output (`encoded/`, `skipped/`, `failed/`)
- `run_windows_opus.bat` → forces `.opus` output
- `run_windows_ogg.bat` → forces `.ogg` output
- `format_convert_to_opus.bat` → format conversion only (no optimization)
- `format_convert_to_ogg.bat` → format conversion only (no optimization)

---

## Format Conversion Mode

Format Conversion Mode standardizes audio formats without applying Pressor's optimization pipeline.

Use it to convert inputs like MP3, WAV, FLAC, M4A, or OGG into `.ogg` or `.opus`.

This still performs encoding via FFmpeg, but skips:

- perceptual optimization  
- auto-profiling  
- size reduction logic  

### Convert to OGG

```bash
python pressor.py --input INPUT --output OUTPUT --format-conversion --target-format ogg
```

### Convert to Opus

```bash
python pressor.py --input INPUT --output OUTPUT --format-conversion --target-format opus
```

### Optional bitrate

```bash
python pressor.py --input INPUT --output OUTPUT --format-conversion --target-format opus --conversion-bitrate 128k
```

### Behavior

- converts supported audio inputs to target format  
- skips files already in that format  
- preserves folder structure  
- supports `--structured-output`  
- does NOT combine with Wwise mode or optimization flags  

### Legacy Compatibility

- `--convert-lossy-to-ogg` still works

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

---

## What the Main Flags Mean

- `--doctor` checks the environment  
- `--selftest` validates functionality  
- `--auto-profile` classifies files  
- `--skip-lossy-inputs` avoids reprocessing lossy audio  
- `--structured-output` creates `encoded/`, `skipped/`, `failed/`, `reports/`  
- `--wwise-mode` enables Wwise pipeline behavior  
- `--changed-only` processes only changed files  
- `--benchmark` reports size reduction  
- `--output-format` forces codec output  
- `--format-conversion` converts formats without optimization  

---

## FFmpeg Requirements

Pressor requires:

- `ffmpeg`  
- `ffprobe`

### Windows

Run:

```bash
python pressor.py --doctor
python pressor.py --selftest
```

---

## How It Works

1. scan input audio  
2. classify content  
3. apply encoding strategy  
4. validate output  
5. write results  

---

## Structured Output

```
encoded/
skipped/
failed/
reports/
```

---

## Lossy Input Handling

Lossy inputs are skipped by default.

To normalize them:

```bash
python pressor.py --convert-lossy-to-ogg
```

---

## Dependencies

- Python  
- FFmpeg  

---

## Testing

```bash
pytest
```

---

Pressor is designed to be predictable, scalable, and safe for production pipelines.