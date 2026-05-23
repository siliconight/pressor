# Pressor v3.14.1

## Changes

- Fixed `.ogg` output to use true Ogg Vorbis via `libvorbis`.
- Preserved `.opus` output using `libopus`.
- Improved compatibility with Godot and other tools that expect `.ogg` files to contain Vorbis streams.
- Added official Pressor branding assets:
  - `assets/pressor_logo.png`
  - `assets/pressor_icon.ico`
- Updated README branding so the logo renders on GitHub.

## Why this matters

Previously, `.ogg` output could contain an Opus stream inside an Ogg container. Some engines, including Godot, expect `.ogg` imports to be Ogg Vorbis and will reject Ogg Opus streams.
