# Windows Setup

## Fastest Path

1. Double-click `setup.bat`
2. Put source-quality audio into:

```text
C:\Pressor\input
```

3. Double-click `run_windows.bat`
4. Open:

```text
C:\Pressor\output
```

If you want skipped and failed source files copied into the run folder too, use `run_windows_structured.bat`.

---

## What Setup Does

- verifies Python
- installs Python dependencies
- installs optional GUI support
- checks for FFmpeg and FFprobe
- tries to install FFmpeg with Winget or Chocolatey when available
- initializes the default workspace at `C:\Pressor`
- runs `python pressor.py --doctor`
- opens the input folder when setup completes

---

## Confirm the Machine Is Ready

Run:

```bash
python pressor.py --doctor
```

You want zero failures before a real run.

---

## Troubleshooting

### Python not found

Install Python from:
https://www.python.org/downloads/

During install, enable:

```text
Add Python to PATH
```

### FFmpeg not found

Setup will try to install it automatically.

If that still does not work:

1. Install FFmpeg
2. Make sure both `ffmpeg` and `ffprobe` are on `PATH`
3. Open a new terminal
4. Run:

```bash
python pressor.py --doctor
```

---

## Security Note

Use trusted, source-quality audio files when possible. Avoid processing untrusted media from unknown sources.
