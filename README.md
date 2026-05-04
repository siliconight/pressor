# Pressor

Make audio smaller without changing what players hear.

Pressor is a perceptual audio optimization tool for game teams, pipelines, and batch processing workflows.

Version: v3.13.3  
License: MIT

---

## First-Time Users

### Windows

Start here:

```text
START_HERE_WINDOWS.bat
```

After setup completes:

1. Put audio files in `C:\Pressor\input`
2. Run `run_windows.bat`

Use `run_windows_structured.bat` when you want pipeline-friendly `encoded/`, `skipped/`, and `failed/` folders.

Use `run_windows_opus.bat` when you want Pressor-optimized `.opus` outputs.

Use `run_windows_ogg.bat` when you want Pressor-optimized `.ogg` outputs.

Use `run_windows_sfx_ogg.bat` when you want to run the current SFX tuning path into `.ogg` outputs from `C:\Pressor\input\sfx`.

Use `format_convert_to_opus.bat` or `format_convert_to_ogg.bat` when you only want to convert formats without applying Pressor's optimization pipeline.

### Linux

Start here:

```bash
./setup_linux.sh
```

Then put audio files in `~/Pressor/input` and run:

```bash
./run_linux.sh
```

---

## What Pressor Is For

Pressor reduces shipped audio size while preserving perceived quality.

It is built for teams that want to:

- shrink install and patch sizes
- reduce download and CDN costs
- batch-process large audio sets safely
- prepare cleaner upstream inputs for Wwise workflows

The goal is not to improve audio.
The goal is to remove data that is unlikely to matter perceptually, while keeping the player experience intact.

---

## 2-Minute Success Path

If you want the fastest path to a first successful run, do this.

### Windows

1. Download the release zip and extract it.
2. Double-click `START_HERE_WINDOWS.bat`.
3. Put source-quality audio files into:

```text
C:\Pressor\input
```

4. Double-click `run_windows.bat`.
5. Open:

```text
C:\Pressor\output
```

If you want skipped and failed source files copied into the run folder too, use:

```text
run_windows_structured.bat
```

### Linux

1. Extract or clone Pressor.
2. Run:

```bash
./setup_linux.sh
```

3. Put source-quality audio files into:

```text
~/Pressor/input
```

4. Run:

```bash
./run_linux.sh
```

5. Open:

```text
~/Pressor/output
```

---

## Windows Runner Shortcuts

Use these from the extracted Pressor folder:

- `run_windows.bat` uses profile-defined output behavior
- `run_windows_structured.bat` uses profile-defined output behavior with `encoded/`, `skipped/`, and `failed/` folders
- `run_windows_opus.bat` forces optimized `.opus` output
- `run_windows_ogg.bat` forces optimized `.ogg` output
- `run_windows_sfx_ogg.bat` runs SFX-only optimized `.ogg` output from `C:\Pressor\input\sfx` to the normal `C:\Pressor\output` run root
- `format_convert_to_opus.bat` converts supported inputs to `.opus` without the optimization pipeline
- `format_convert_to_ogg.bat` converts supported inputs to `.ogg` without the optimization pipeline

---



## SFX OGG Runner

Use `run_windows_sfx_ogg.bat` when you want to process only SFX assets through the current Pressor tuning path and force `.ogg` output.

Expected folder layout:

```text
C:\Pressor\input\sfx
```

Output folder:

```text
C:\Pressor\output
```

This is useful when you want to isolate SFX processing while dialogue uses its own more conservative tuning floor.

---


## Dialogue-Safe Tuning Floor

Dialogue is protected more conservatively than SFX.

Pressor no longer allows the dialogue profile to drop into very low speech-style settings such as 24 kHz sample rate or sub-160k bitrate. This prevents the audible high-end cutoff and over-compressed voice quality that can appear when game dialogue is treated like low-bandwidth voice chat.

Dialogue profile floor:

- sample rate: 48 kHz minimum
- bitrate: 160k minimum
- normal dialogue target: 192k
- conservative high-risk target: 224k
- channels: preserve up to stereo

SFX tuning remains unchanged and continues to use the existing SFX profile behavior.

Folder routing includes common content folders such as `dialogue/`, `vo/`, `voice/`, `sfx/`, and `music/`.

---

## Format Conversion Mode

Format Conversion Mode is for standardizing audio formats without applying Pressor's optimization pipeline.

Use it when you want to convert files such as MP3, WAV, FLAC, M4A, or OGG into a consistent `.ogg` or `.opus` output for a downstream tool or pipeline.

This still uses FFmpeg to encode into the target codec. It does not run Pressor's perceptual optimization, auto-profile tuning, or size-reduction decision path.

Convert to OGG:

```bash
python pressor.py --input INPUT --output OUTPUT --format-conversion --target-format ogg
```

Convert to Opus:

```bash
python pressor.py --input INPUT --output OUTPUT --format-conversion --target-format opus
```

Optional bitrate override:

```bash
python pressor.py --input INPUT --output OUTPUT --format-conversion --target-format opus --conversion-bitrate 128k
```

Windows shortcuts:

- `format_convert_to_ogg.bat`
- `format_convert_to_opus.bat`

Behavior:

- converts supported audio inputs to the requested target format
- skips files that are already in the requested target format
- preserves relative folder structure
- supports `--structured-output`
- does not combine with Wwise mode, manifests, changed-only, or `--output-format`

Legacy compatibility:

- `--convert-lossy-to-ogg` still works as an alias for `--format-conversion --target-format ogg`

## Output Format Overrides

By default, Pressor uses the selected profile to decide the output container.

Use `--output-format` when you want a specific output type without editing profile JSON.

Force Opus output:

```bash
python pressor.py --input INPUT --output OUTPUT --auto-profile --skip-lossy-inputs --output-format opus
```

Force OGG output:

```bash
python pressor.py --input INPUT --output OUTPUT --auto-profile --skip-lossy-inputs --output-format ogg
```

Behavior:

- `--output-format opus` writes `.opus` outputs
- `--output-format ogg` writes `.ogg` outputs
- auto-profile still controls tuning and classification
- the override only applies to normal encoding runs
- output format overrides force both codec and container together

Windows shortcuts:

- `run_windows_opus.bat`
- `run_windows_ogg.bat`
- `run_windows_sfx_ogg.bat`

---

## Before Your First Real Run

Run this once to confirm the machine is ready:

```bash
python pressor.py --doctor
```

You should see:

- Python detected
- FFmpeg detected
- FFprobe detected
- Pressor config files loaded
- zero failures

If FFmpeg is missing, Pressor will now tell you what to do next instead of failing vaguely.

---

## The 4 Commands That Matter Most

These are the commands that should be treated as the stable, everyday Pressor surface area.

### 1. Environment check

```bash
python pressor.py --doctor
```

### 2. Safe first run

```bash
python pressor.py --auto-profile --skip-lossy-inputs --benchmark
```

### 3. Structured pipeline run

```bash
python pressor.py --auto-profile --skip-lossy-inputs --structured-output --benchmark
```

### Force Opus Output

```bash
python pressor.py --auto-profile --skip-lossy-inputs --output-format opus --benchmark
```

### Force OGG Output

```bash
python pressor.py --auto-profile --skip-lossy-inputs --output-format ogg --benchmark
```

### 4. Wwise-oriented run

```bash
python pressor.py --input ./AudioRaw --output ./AudioOut --auto-profile --wwise-mode --wwise-prep
```

---

## What the Main Flags Mean

These flags are the intended public contract going into 1.0 positioning.

- `--doctor` checks the environment before a real run
- `--selftest` validates Pressor on generated sample inputs
- `--auto-profile` classifies files when no routing rule matches
- `--skip-lossy-inputs` protects already-lossy sources from being processed again
- `--structured-output` creates `encoded/`, `skipped/`, `failed/`, and `reports/` inside the run folder
- `--wwise-mode` enables Wwise-oriented behavior and reporting
- `--wwise-prep` writes import-oriented Wwise artifacts
- `--changed-only` processes only files whose source hash or chosen profile changed
- `--benchmark` prints measured size reduction after the run
- `--output-format opus|ogg` forces normal encoding runs to produce `.opus` or `.ogg` outputs
- `--format-conversion --target-format ogg|opus` converts formats without applying Pressor's optimization pipeline

Default behavior remains backward-compatible when `--structured-output` is not used.

---

## What a Normal Run Looks Like

Each run shows:

- total files detected
- per-file processing status
- whether files were encoded, skipped, or failed
- a final summary with output and report locations
- an optional benchmark summary for measured size reduction

Outputs are written into timestamped run folders for easy comparison.

With `--structured-output`, a run folder contains:

```text
encoded/
skipped/
failed/
reports/
```

Without that flag, default output behavior remains unchanged.

---

## FFmpeg Requirements

Pressor requires both `ffmpeg` and `ffprobe`.

### Windows

`setup.bat` will try to help install FFmpeg automatically when possible.

If that does not work:

1. Install FFmpeg
2. Make sure both `ffmpeg` and `ffprobe` are on `PATH`
3. Open a new terminal
4. Run:

```bash
python pressor.py --doctor
```

### Linux

Install FFmpeg with your package manager, then run:

```bash
python pressor.py --doctor
```

Example:

```bash
sudo apt install ffmpeg
```

---

## Wwise Pipeline Usage

Pressor is designed to sit upstream of Wwise and integrate cleanly into existing audio pipelines.

Typical flow:

```text
Raw Audio -> Pressor -> Wwise Import -> SoundBank Build
```

Pressor does not alter mix, gain structure, authoring intent, or runtime playback behavior.

Typical Wwise-oriented command:

```bash
python pressor.py --input ./AudioRaw --output ./AudioOut --auto-profile --wwise-mode --wwise-prep
```

Typical incremental Wwise-oriented command:

```bash
python pressor.py --input ./AudioRaw --output ./AudioOut --auto-profile --wwise-mode --wwise-prep --changed-only
```

Generated Wwise event and object names are derived from the asset's relative path so same-stem files in different folders do not collide during automated import.

---

## Determinism and Changed-Only Processing

When `--changed-only` is enabled:

- only assets whose source hash or selected profile changed are processed
- unchanged assets are skipped before encoding begins
- a persistent state manifest is stored in the output root
- repeated runs avoid unnecessary churn

This is intended to reduce rebuild noise and keep version control diffs clean.

---

## Repository Hygiene and Release Packaging

Pressor is intended to ship as a clean release, not a snapshot of a developer workspace.

- generated logs, temp files, reports, caches, and local workspaces are ignored
- the release builder excludes those artifacts while preserving scripts, tests, docs, and pipeline assets
- packaged releases include a `RELEASE_MANIFEST_SHA256.txt` file for traceability

To build a deterministic release zip from the repo root, run:

```bash
python build_release.py
```

---

## Validation Commands

From the release root:

```bash
pytest -q
python pressor.py --doctor
python pressor.py --selftest
```

---

## Security Note

Use trusted, source-quality audio files when possible. Avoid processing untrusted media from unknown sources.


## Windows dependency bootstrap

Run `START_HERE_WINDOWS.bat` first.

On Windows, setup checks for:
- Python 3.10 or newer
- pip
- Pressor Python dependencies
- FFmpeg
- FFprobe

If Python is missing, setup can install Python 3.12 through WinGet.

If FFmpeg or FFprobe are missing, setup can install FFmpeg through WinGet using the `Gyan.FFmpeg` package.

After installing Python or FFmpeg, Windows may not refresh PATH inside the same Command Prompt. If setup tells you to reopen the terminal, close the window, open a new Command Prompt, and run `setup.bat` again.


## Windows launcher behavior

`run_windows.bat` and `run_windows_structured.bat` use the default workspace explicitly:

- Input: `C:\Pressor\input`
- Output: `C:\Pressor\output`

Before running, the launcher checks whether supported audio files are present in the input folder.
If none are found, it opens the input folder and stops with a clear message.


## Dependency Installation & Security

Pressor installs required dependencies using **WinGet (Windows Package Manager)** when you approve it during setup.

This includes:
- Python (Python.Python.3.12)
- FFmpeg (Gyan.FFmpeg)

Why this approach:
- Uses Microsoft's official package manager (WinGet)
- Installs from known package IDs, not arbitrary URLs
- Does not bundle third-party binaries directly in Pressor
- Prompts before installing anything on your system

What this means:
- You are trusting the WinGet package source and maintainers
- This is standard practice for developer tooling on Windows

If you prefer:
- You can decline automatic installation
- Install Python manually from https://www.python.org/
- Install FFmpeg manually and ensure `ffmpeg` and `ffprobe` are on PATH

Pressor will work the same either way.
