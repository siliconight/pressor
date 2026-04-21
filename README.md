# Pressor

Make audio smaller without changing what players hear.

Pressor is a perceptual audio optimization tool designed for game developers, pipelines, and batch processing workflows.

Version: v3.4.1  
License: MIT

---

## Why Pressor

Audio often contains more data than players can actually perceive.

Pressor reduces that footprint so teams can:

- shrink install sizes  
- reduce patch sizes  
- lower bandwidth and CDN costs  
- speed up downloads and updates  

The goal is not to change how audio sounds.

The goal is to remove data that is unlikely to matter perceptually, while preserving the player experience.

---

## What Pressor Demonstrates

Pressor is designed to prove three things in real pipelines:

- measurable reduction in packaged build size  
- deterministic behavior suitable for CI systems  
- seamless integration into Wwise without runtime impact  

The goal is not just compression, but safe, repeatable optimization in production environments.

---

## Quick Start

### Windows

1. Download or clone this repository  
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

```
./setup_linux.sh
```

3. Place audio files into:

```
~/Pressor/input
```

4. Run:

```
./run_linux.sh
```

5. Results are written to:

```
~/Pressor/output
```

---

## Run Experience

Pressor provides clear feedback during execution.

Each run shows:

- total files detected  
- per-file processing status  
- whether files were encoded, skipped, or failed  
- a final summary with output and report locations  
- an optional benchmark summary for measured size reduction  

Outputs are organized into timestamped run folders for easy tracking and comparison.

---

## How It Works

Pressor applies perceptual audio optimization in a batch-friendly workflow.

At a high level it:

1. scans input audio  
2. determines how each file should be treated  
3. applies a controlled encoding strategy  
4. validates the result  
5. writes outputs, reports, and review artifacts  

### Perceptual encoding

Pressor does not try to improve your audio.

It reduces file size by removing data that is less likely to be heard by the player.

This works because human hearing does not perceive every part of a waveform equally.

In many cases:

- quieter sounds are masked by louder sounds  
- some frequency detail is less noticeable in context  
- dense material can tolerate reduction without changing perceived quality  

Pressor is built around that principle.

### What Pressor preserves

Pressor is not meant to remove meaningful audible content.

It is designed to reduce data where the listener is unlikely to notice a difference.

The target is not the smallest file possible.

The target is smaller files without perceptible loss in normal listening and gameplay conditions.

---

## Wwise Pipeline Usage

Pressor is designed to sit upstream of Wwise and integrate cleanly into existing audio pipelines.

Typical flow:

```
Raw Audio → Pressor → Wwise Import → SoundBank Build
```

Pressor does not alter mix, gain structure, authoring intent, or runtime audio behavior.

Use `--wwise-mode` to run with Wwise-oriented validation and messaging. This enables Wwise-safe handling while keeping Wwise as the source of truth for playback.

Generated Wwise event and object names are derived from the asset's relative path so that same-stem files in different folders do not collide during automated import.

---

## Determinism and Changed-Only Processing

Pressor supports deterministic, changed-only processing so CI systems and Perforce workflows stay stable.

When `--changed-only` is enabled:

- only assets whose source hash or selected profile changed are processed  
- unchanged assets are skipped before encoding begins  
- a persistent state manifest is stored in the output root  
- repeated runs avoid unnecessary churn  

This is intended to reduce rebuild noise and keep version control diffs clean.

---

## Benchmarking

Use `--benchmark` to print a measured size comparison after a run.

Example:

```
python pressor.py --input ./AudioRaw --output ./AudioOut --auto-profile --changed-only --benchmark
```

This prints:

- input size  
- output size  
- measured reduction percentage  

Use this to demonstrate measurable packaged build-size reduction on real datasets.

---

## Lossy Input Handling

Pressor is intended for source-quality audio such as WAV, FLAC, or other lossless formats.

If already compressed audio such as MP3, AAC, OGG, or Opus is provided, Pressor must decode and re-encode that content. This can introduce additional quality loss.

In general:

- lossless to lossy is expected and controlled  
- lossy to lossy is cumulative degradation  

Pressor detects lossy inputs and handles them conservatively by default.

It is strongly recommended to use Pressor on original, uncompressed audio whenever possible.

---

## Default Workspace

Pressor creates a workspace automatically.

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

Each run creates a timestamped output folder:

```
output/
  2026-04-18_214233/
    encoded/
    review/
    reports/
```

Changed-only state is tracked separately in the output root:

```
pressor_state_manifest.json
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

Run with changed-only processing and benchmark output:

```
python pressor.py --changed-only --benchmark
```

Run in Wwise-oriented mode:

```
python pressor.py --wwise-mode
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

Each run generates structured outputs:

- pressor_report.csv  
- pressor_failures.json  
- pressor_run.jsonl  

Changed-only runs may also produce:

- pressor_manifest_full.json  
- pressor_manifest_changed.json  
- pressor_state_manifest.json  

These artifacts make pipeline decisions visible and traceable.

---

## Security

Pressor runs locally and does not transmit data externally.

It processes files within the configured workspace and relies on FFmpeg and FFprobe for media inspection and encoding.

Manifest-driven runs validate that destinations remain within the configured output root and will fail if a manifest attempts to write outside it.

For best safety:

- use trusted, source-quality audio files  
- avoid processing untrusted media from unknown sources  
- review setup scripts before execution  
- prefer the default strict handling for lossy inputs  

Pressor does not require elevated privileges and runs within normal user permissions.

---

## Documentation

- docs/WINDOWS_SETUP.md  
- docs/LINUX_SETUP.md  
- docs/CI_BUILD_PIPELINE_SETUP.md  
- docs/TEAMCITY_SETUP.md  

---

## Dependencies

Pressor requires:

- Python 3.x  
- FFmpeg and FFprobe  

Setup scripts attempt automatic installation where possible.

---

## Testing

Run all tests:

```
python -m unittest discover -s tests/unit -v
```

---

## Maintainer

Brannen Graves
