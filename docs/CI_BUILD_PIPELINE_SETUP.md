# Pressor – CI / Build Pipeline Integration Guide

This guide explains how to run Pressor in a build or CI pipeline so audio assets can be processed in a repeatable, headless workflow.

Pressor is designed to work well in automated environments:
- no GUI required
- deterministic batch processing
- machine-readable reports
- explicit error codes
- safe guardrails for production use

## What Pressor is good at in CI

Pressor can be used in build automation to:

- reduce the size of source-quality audio assets
- enforce consistent profile-based encoding
- fail fast on already-lossy inputs
- generate reports for audit and troubleshooting
- prepare audio for downstream workflows such as Wwise-safe prep

## Recommended production principles

For CI and build systems, use Pressor with these assumptions:

- input audio should be source-quality
- output should always go to a separate folder
- lossy re-processing should be blocked
- routing rules should be treated as the source of truth
- review packs are optional and usually best for sampling or validation jobs, not every build

## Typical pipeline shape

A common flow looks like this:

```text
Source Sync
→ Pressor Doctor Check
→ Pressor Batch Process
→ Optional Wwise Prep
→ Build / Package / Publish
```

## Prerequisites

Your build machine should have:

- Python 3 installed
- FFmpeg installed and available on PATH
- FFprobe installed and available on PATH
- Pressor checked out or extracted on disk

Verify with:

```bash
python pressor.py --doctor
```

## Minimal CI command

Use this as the standard batch command:

```bash
python pressor.py --input ./AudioRaw --output ./AudioOut --auto-profile --fail-on-lossy-inputs
```

## Recommended CI command

For a safer production run:

```bash
python pressor.py --input ./AudioRaw --output ./AudioOut --auto-profile --strict-routing --fail-on-lossy-inputs
```

## Recommended Wwise-safe command

If the project uses Wwise and wants WAV outputs for later import:

```bash
python pressor.py --input ./AudioRaw --output ./AudioPrepared --auto-profile --strict-routing --fail-on-lossy-inputs --wwise-prep --wwise-safe
```

## Suggested folder layout for CI

```text
repo/
  AudioRaw/
    VO/
    Ambient/
    Music/
    SFX/
    Foley/

  BuildArtifacts/
    AudioOut/
    Reports/
```

## Reports and logs

Pressor writes machine- and human-readable outputs that are useful in CI.

Typical outputs:

- `pressor_report.csv`
- `pressor_failures.json`
- `pressor_run.jsonl`

These can be archived as build artifacts.

## Error handling in CI

Pressor uses stable error codes.

Examples:
- `P1001` input path or source file missing
- `P1002` output nested inside input
- `P1101` FFmpeg or FFprobe missing
- `P1301` encode or prep failed
- `P1302` output verification failed
- `P1303` FFmpeg timed out
- `P1401` manifest invalid
- `P1501` lossy input blocked
- `P9001` unexpected internal error

If the build fails, check:
- terminal output
- `pressor_failures.json`
- `pressor_run.jsonl`

## Example: simple Windows build step

```bat
python pressor.py --doctor
python pressor.py --input C:\Build\AudioRaw --output C:\Build\AudioOut --auto-profile --strict-routing --fail-on-lossy-inputs
```

## Example: simple Linux build step

```bash
python3 pressor.py --doctor
python3 pressor.py --input /build/AudioRaw --output /build/AudioOut --auto-profile --strict-routing --fail-on-lossy-inputs
```

## Example: GitHub Actions job

```yaml
name: Pressor Audio Check

on:
  workflow_dispatch:
  pull_request:

jobs:
  pressor:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install FFmpeg
        run: sudo apt-get update && sudo apt-get install -y ffmpeg

      - name: Verify environment
        run: python3 pressor.py --doctor

      - name: Process audio
        run: |
          python3 pressor.py \
            --input ./AudioRaw \
            --output ./AudioOut \
            --auto-profile \
            --strict-routing \
            --fail-on-lossy-inputs
```

## Best practices

- Use source-quality input
- Keep source and output separate
- Block lossy re-processing
- Prefer routing over guessing
- Archive reports
- Validate on real content before broad rollout


Note: Pressor creates a new timestamped run folder inside the selected output root by default. Use `--flat-output` only if you intentionally want to write directly into the selected output folder.
