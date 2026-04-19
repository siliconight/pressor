# Windows Setup

## Quick Setup

1. Run `setup.bat`
2. Wait for setup to complete
3. Add audio files to:

```
C:\Pressor\input
```

4. Run:

```
run_windows.bat
```

---

## What Setup Does

- installs Python dependencies
- installs optional GUI support
- installs FFmpeg (via Winget or Chocolatey when available)
- initializes workspace
- verifies environment
- opens input folder

---

## Troubleshooting

### Python not found
Install from:
https://www.python.org/downloads/

Make sure:
```
Add Python to PATH
```

---

### FFmpeg not found

Setup will try to install automatically.

If not:

1. Download from:
   https://ffmpeg.org/download.html
2. Add to PATH:
```
C:\ffmpeg\bin
```
3. Run setup again
