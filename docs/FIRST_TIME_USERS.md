# First-Time User Guide

This guide explains which file to run first.

## Windows

Use this order:

1. `START_HERE_WINDOWS.bat`
2. `run_windows.bat`

`START_HERE_WINDOWS.bat` delegates to `setup.bat` and explains what setup will do before it runs.

After setup, Pressor uses this workspace:

```text
C:\Pressor\
  input\
  output\
```

Put source audio files into `C:\Pressor\input`.

Then run:

```text
run_windows.bat
```

For pipeline-friendly output folders, run:

```text
run_windows_structured.bat
```

## Linux

Use this order:

```bash
./setup_linux.sh
./run_linux.sh
```

The Linux workspace is:

```text
~/Pressor/
  input/
  output/
```

## Do Not Start With These

Most first-time users should not start with:

- `pressor.py`
- `build_release.py`
- files in `scripts/`
- files in `teamcity/`

Those are for CLI usage, release packaging, maintainers, or CI.
