#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import shutil
import zipfile

ROOT = Path(__file__).resolve().parent
VERSION_FILE = ROOT / "VERSION.txt"
DIST_DIR = ROOT / "dist"
STAGING_DIR = DIST_DIR / "_staging"

EXCLUDE_DIR_NAMES = {
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    ".git", ".idea", ".vscode", "logs", "output", "reports",
    "dist", "build", ".venv", "venv", "env", ".venv-build", "tmp", "scratch", "debug"
}
EXCLUDE_SUFFIXES = {".pyc", ".pyo", ".pyd", ".log", ".jsonl", ".tsv", ".csv", ".tmp", ".spec"}
EXCLUDE_FILES = {".DS_Store", "Thumbs.db"}


def read_version() -> str:
    raw = VERSION_FILE.read_text(encoding="utf-8").strip()
    return raw.replace("Pressor ", "", 1).strip()


def should_include(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    parts = set(rel.parts)
    if parts & EXCLUDE_DIR_NAMES:
        return False
    if path.name in EXCLUDE_FILES:
        return False
    if path.suffix.lower() in EXCLUDE_SUFFIXES:
        return False
    return True


def iter_release_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if should_include(path):
            files.append(path)
    return sorted(files, key=lambda p: p.relative_to(ROOT).as_posix())


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    version = read_version()
    release_root_name = f"pressor-{version}"
    zip_name = f"pressor-{version}-release.zip"

    if STAGING_DIR.exists():
        shutil.rmtree(STAGING_DIR)
    STAGING_DIR.mkdir(parents=True, exist_ok=True)

    release_root = STAGING_DIR / release_root_name
    release_root.mkdir(parents=True, exist_ok=True)

    files = iter_release_files()
    manifest_lines = []
    for src in files:
        rel = src.relative_to(ROOT)
        dest = release_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        manifest_lines.append(f"{sha256_file(src)}  {rel.as_posix()}")

    (release_root / "RELEASE_MANIFEST_SHA256.txt").write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")

    DIST_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = DIST_DIR / zip_name
    if zip_path.exists():
        zip_path.unlink()

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(release_root.rglob("*"), key=lambda p: p.relative_to(STAGING_DIR).as_posix()):
            if path.is_file():
                zf.write(path, arcname=path.relative_to(STAGING_DIR).as_posix())

    print(f"Built {zip_path}")
    print(f"Release root: {release_root_name}")
    print(f"Files packaged: {len(files)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
