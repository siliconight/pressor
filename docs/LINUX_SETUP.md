# Linux Setup

## Quick Setup

1. Run:
```
./setup_linux.sh
```

2. Add audio files to:
```
~/Pressor/input
```

3. Run:
```
./run_linux.sh
```

---

## What Setup Does

- installs Python dependencies
- installs optional GUI support
- installs FFmpeg using system package manager
- initializes workspace
- verifies environment

---

## Supported Package Managers

- apt
- dnf
- pacman
- zypper

---

## Troubleshooting

### Python not found
Install Python 3 using your distro package manager

---

### FFmpeg not found

Install manually:

```
sudo apt install ffmpeg
```

(or equivalent for your distro)


## Security Note

Use trusted, source-quality audio files when possible. Avoid processing untrusted media from unknown sources.
