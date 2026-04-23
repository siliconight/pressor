# Pressor

Make audio smaller without changing what players hear.

Pressor is a perceptual audio optimization tool designed for game developers, pipelines, and batch processing workflows.

Version: v3.8.0  
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

## Structured Output (New in v3.6.2)

Pressor can optionally organize all inputs into a clearer, pipeline-friendly structure:

```
python pressor.py --structured-output
```

This creates:

```
OutputRoot/
└── pressor_runs/<timestamp>/
    ├── encoded/   # successfully processed files
    ├── skipped/   # inputs intentionally not processed
    ├── failed/    # files that encountered errors
    ├── reports/
    │   └── pressor_run.jsonl
```

Key behavior:

- disabled by default so existing behavior does not break  
- preserves original folder structure  
- skipped and failed files are copied, not moved  
- does not affect hashing or change detection  

Recommended for pipelines:

```
python pressor.py --wwise-mode --structured-output
```

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

Use `--wwise-mode` to run with a Wwise-oriented preset. This enables Wwise-safe handling, import artifact generation, and CI-friendly summaries while keeping Wwise as the source of truth for playback. Changed-only processing is optional and should be requested explicitly with `--changed-only`.

Generated Wwise event and object names are derived from the asset's relative path so that same-stem files in different folders do not collide during automated import.

Typical Wwise-oriented command:

```
python pressor.py --input ./AudioRaw --output ./AudioOut --auto-profile --wwise-mode --wwise-prep
```

Typical incremental Wwise-oriented command:

```
python pressor.py --input ./AudioRaw --output ./AudioOut --auto-profile --wwise-mode --wwise-prep --changed-only
```

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

Pressor detects lossy inputs and handles them conservatively by default. In standard runner scripts, lossy files are skipped so the rest of the batch can continue.

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

Default runner scripts process the full batch and skip lossy inputs. Incremental behavior is only enabled when you explicitly pass `--changed-only`.

Skip lossy inputs while continuing the rest of the batch:

```
python pressor.py --skip-lossy-inputs
```

Run with changed-only processing and benchmark output:

```
python pressor.py --changed-only --benchmark
```

Run in Wwise-oriented mode:

```
python pressor.py --wwise-mode
```

Run in Wwise-oriented prep mode:

```
python pressor.py --wwise-mode --wwise-prep
```

Run in Wwise-oriented incremental mode:

```
python pressor.py --wwise-mode --changed-only
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

Changed-only and Wwise-mode runs may also produce:

- pressor_manifest_full.json  
- pressor_manifest_changed.json  
- pressor_state_manifest.json  
- wwise_import.json  
- wwise_import.tsv  

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


### Handling Skipped Files

By default, Pressor does not copy skipped files into the output directory.

To include skipped inputs, such as MP3 files when using `--skip-lossy-inputs`, enable structured output:

```
python pressor.py --input INPUT --output OUTPUT --auto-profile --skip-lossy-inputs --structured-output
```

Important:

- skipped files are copied, not moved  
- original filenames and folder structure are preserved  
- this behavior is opt-in so existing workflows do not change  



## Input Hardening (New in v3.8.0)

Pressor now treats the input folder as an explicit trust boundary. It will never execute files from the input folder, and it will reject clearly unsafe or unsupported files before they reach ffmpeg.

What changed:
- blocked executable and script-like inputs such as `.exe`, `.bat`, `.cmd`, `.ps1`, `.sh`, and `.js` are rejected
- common audio formats are accepted by extension
- unknown extensions are probed with `ffprobe` by default and accepted only when an audio stream is confirmed
- rejected inputs are written to `reports/pressor_rejected_inputs.json`
- when `--structured-output` is enabled, rejected source files are copied into `rejected/`

Example pipeline-friendly usage:

```bash
python pressor.py --input INPUT --output OUTPUT --auto-profile --skip-lossy-inputs --structured-output
```

If you need the older strict extension-only behavior, you can disable probing for unknown extensions:

```bash
python pressor.py --input INPUT --output OUTPUT --no-input-sniffing
```


## Cleanup and Retention

If you run Pressor frequently in CI or batch pipelines, old timestamped run folders can add up over time. Pressor 3.8.0 adds a safe cleanup command that only manages folders inside `pressor_runs/`.

Examples:

```bash
python pressor.py cleanup --output OUTPUT --keep-last 50
python pressor.py cleanup --output OUTPUT --older-than-days 3
python pressor.py cleanup --output OUTPUT --keep-last 50 --older-than-days 3 --dry-run
```

What it does:
- `--keep-last N` keeps the newest N run folders
- `--older-than-days D` removes runs older than D days
- `--dry-run` shows what would be deleted without deleting anything
- `--verbose` prints each deleted run folder

Cleanup only touches `OUTPUT/pressor_runs/` and leaves other output content alone.

