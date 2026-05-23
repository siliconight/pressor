# Pressor Repository Structure

Pressor keeps the root directory focused on the files most users need.

## User-facing root files

- `START_HERE_WINDOWS.bat` starts first-time Windows setup.
- `setup.bat` prepares the Windows machine.
- `run_windows_ogg.bat` runs the common Godot-friendly Ogg Vorbis workflow.
- `run_windows.bat`, `launchers/run_windows_opus.bat`, `launchers/run_windows_structured.bat`, and `launchers/run_windows_sfx_ogg.bat` remain available for alternate workflows.
- `pressor.py` is the stable CLI entry point.
- `README.md`, `START_HERE.md`, `VERSION.txt`, and `LICENSE` describe the project and release.

## Main folders

- `assets/` contains Pressor branding and icon assets.
- `config/` contains Pressor profile, routing, and Wwise JSON configuration.
- `docs/` contains deeper setup and pipeline documentation.
- `pressor/` contains the application code.
- `scripts/` contains platform build and install helpers.
- `teamcity/` contains CI examples.
- `tests/` contains regression and smoke tests.
- `tools/` contains repo validation, release packaging, and developer utilities.

## Compatibility

The root still includes wrapper files for important commands so existing habits and automation do not have to change immediately.
