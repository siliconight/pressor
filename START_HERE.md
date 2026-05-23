# Start Here

For the normal Windows OGG workflow:

1. Double-click `setup.bat` once.
2. Put source-quality audio in `C:\Pressor\input`.
3. Double-click `run_windows_ogg.bat`.
4. Get results from `C:\Pressor\output`.

Advanced launchers live in `launchers/`. Internal support files live in `support/`, `tools/`, and `docs/`.

---

# Start Here

This file is for first-time users.

## Windows

1. Double-click `START_HERE_WINDOWS.bat`.
2. Follow the setup prompts.
3. Put audio files in `C:\Pressor\input`.
4. Double-click `run_windows.bat`.

For pipeline-style output, use `launchers/run_windows_structured.bat`.

## What Each File Is For

- `START_HERE_WINDOWS.bat` starts first-time setup.
- `setup.bat` installs/checks dependencies and creates the workspace.
- `run_windows.bat` runs the normal Pressor batch process.
- `launchers/run_windows_structured.bat` runs Pressor with encoded/skipped/failed folders.
- `README.md` contains full usage details.

## Linux

1. Run `./setup_linux.sh`.
2. Put files in `~/Pressor/input`.
3. Run `./run_linux.sh`.


## Dialogue-safe tuning

Dialogue now preserves a 48 kHz sample rate and a minimum 160k bitrate floor. SFX tuning remains unchanged.
