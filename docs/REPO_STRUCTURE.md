# Pressor Repository Structure

This document describes the current repository layout and identifies stable entrypoints that should not be moved or renamed casually.

The goal is to prevent accidental breakage during future refactors, cleanup passes, or release packaging changes.

---

## Root Directory

User-facing entrypoints. Do not move or rename these without updating README commands, setup flows, release packaging, and validation checks in the same change.

- `setup.bat`
- `run_windows.bat`
- `run_windows_structured.bat`
- `setup_linux.sh`
- `run_linux.sh`

Core execution:

- `pressor.py` is the primary CLI entrypoint.

Release and packaging:

- `build_release.py` builds the release package.

Project metadata:

- `README.md`
- `VERSION.txt`
- `requirements.txt`
- `pytest.ini`
- `LICENSE`

---

## `pressor/`

Primary application package.

This is where package-level modules, version metadata, CLI helpers, pipeline logic, workspace support, and reporting code should continue to consolidate over time.

---

## `scripts/`

Helper scripts that are not the primary user-facing entrypoints.

This is the preferred home for build helpers, installer helpers, and platform-specific utilities that are useful for maintainers but are not the first thing users should run.

Current examples:

- `scripts/build_linux.sh`
- `scripts/build_windows.ps1`
- `scripts/install_linux.sh`
- `scripts/install_windows.ps1`
- `scripts/run_linux.sh`

---

## `docs/`

Supporting documentation beyond the main README.

Use this folder for setup details, CI notes, TeamCity guidance, repo structure notes, and future operational documentation.

---

## `tests/`

Automated tests for CLI behavior, pipeline behavior, structured output, manifests, security checks, routing, profiles, and other core behaviors.

Tests should protect user-facing behavior before cleanup or refactor work happens.

---

## `teamcity/`

TeamCity-oriented CI helper scripts.

These should remain separate from user-facing local setup and run scripts.

---

## Stability Rules

Before moving or renaming any file, check whether it is referenced by:

- `setup.bat`
- `run_windows.bat`
- `run_windows_structured.bat`
- `setup_linux.sh`
- `run_linux.sh`
- `build_release.py`
- `README.md`
- `docs/`
- `teamcity/`
- tests

If a file is referenced, update all references in the same change and run validation before packaging.

---

## Hygiene Rules

Safe cleanup should be incremental.

Prefer:

- documenting structure before moving files
- moving only non-user-facing helper files first
- validating setup and run scripts after changes
- keeping release packages deterministic

Avoid:

- moving root entrypoints without a compatibility plan
- changing setup behavior during repo cleanup
- changing run behavior during repo cleanup
- mixing refactors with dependency bootstrap changes

---

## Future Direction

Potential future cleanup, after validation coverage is in place:

- gradually move implementation-only modules from the root into `pressor/`
- keep root user entrypoints stable
- keep build-only scripts under `scripts/`
- expand validation around release package contents
