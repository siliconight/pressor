# Pressor v3.14.1

## Changes

- Reduced the repo root to the essential user-facing items.
- Kept `run_windows_ogg.bat` at the root as the primary double-click workflow.
- Moved advanced Windows launchers into `launchers/`.
- Moved support files such as requirements, version metadata, pytest config, and release manifests into `support/` and `docs/releases/`.
- Preserved the existing Python entry point with `python pressor.py`.
- Preserved the Godot-compatible Ogg Vorbis behavior from v3.13.6 and v3.14.0.

## Primary user path

1. Run `setup.bat` once.
2. Add source audio files to `C:\Pressor\input`.
3. Double-click `run_windows_ogg.bat`.
4. Retrieve output from `C:\Pressor\output`.
