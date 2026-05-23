# Pressor v3.14.1

## Changes

- Reorganized the root directory so user-facing launchers are easier to find.
- Moved Pressor JSON configuration files into `config/`.
- Moved developer and release utilities into `tools/`.
- Moved the legacy encoder implementation into the `pressor/` package.
- Kept root-level compatibility wrappers for existing commands such as `python pressor.py`, `python tools/build_release.py`, and `python tools/validate_repo.py`.
- Preserved the Windows double-click flow, including `run_windows_ogg.bat`.
- Preserved the Godot-compatible Ogg Vorbis behavior from v3.13.6.

## Why this matters

The repo root is now closer to a product download surface instead of a development scratchpad. Most users can focus on setup and runner files, while configuration, tools, tests, and implementation details live in dedicated folders.
