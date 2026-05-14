from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def codec_for(path: Path) -> str:
    result = subprocess.run(
        [
            "ffprobe",
            "-v", "error",
            "-select_streams", "a:0",
            "-show_entries", "stream=codec_name",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        return f"ERROR: {result.stderr.strip() or 'ffprobe failed'}"
    return (result.stdout or "").strip().splitlines()[0].strip().lower() if result.stdout else "unknown"


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify that .ogg files are Vorbis encoded.")
    parser.add_argument("path", nargs="?", default=r"C:\Pressor\output", help="Folder or .ogg file to inspect.")
    args = parser.parse_args()

    root = Path(args.path)
    files = [root] if root.is_file() else sorted(root.rglob("*.ogg"))
    if not files:
        print(f"No .ogg files found under {root}")
        return 1

    failed = False
    for file in files:
        codec = codec_for(file)
        status = "OK" if codec == "vorbis" else "FAIL"
        print(f"{status}: {file} -> {codec}")
        if codec != "vorbis":
            failed = True

    return 2 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
