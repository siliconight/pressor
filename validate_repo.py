#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent

REQUIRED_FILES = [
    "setup.bat",
    "run_windows.bat",
    "run_windows_structured.bat",
    "setup_linux.sh",
    "run_linux.sh",
    "pressor.py",
    "build_release.py",
    "README.md",
    "VERSION.txt",
    "requirements.txt",
    "pytest.ini",
    "scripts/build_linux.sh",
    "scripts/build_windows.ps1",
    "docs/REPO_STRUCTURE.md",
]

ROOT_BUILD_HELPERS_THAT_SHOULD_NOT_EXIST = [
    "build_linux.sh",
    "build_windows.ps1",
]

README_EXPECTED_TERMS = [
    "setup.bat",
    "run_windows.bat",
    "run_windows_structured.bat",
    "setup_linux.sh",
    "run_linux.sh",
    "python pressor.py --doctor",
    "python pressor.py --selftest",
]

WINDOWS_RUNNERS = [
    "run_windows.bat",
    "run_windows_structured.bat",
]

CACHE_DIRS = {
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}


def read_text(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8", errors="replace")


def main() -> int:
    issues: list[str] = []

    for rel_path in REQUIRED_FILES:
        if not (ROOT / rel_path).exists():
            issues.append(f"Missing required file: {rel_path}")

    for rel_path in ROOT_BUILD_HELPERS_THAT_SHOULD_NOT_EXIST:
        if (ROOT / rel_path).exists():
            issues.append(f"Build helper should live under scripts/, not root: {rel_path}")

    if (ROOT / "README.md").exists():
        readme = read_text("README.md")
        for term in README_EXPECTED_TERMS:
            if term not in readme:
                issues.append(f"README.md does not mention expected command or script: {term}")

    for rel_path in WINDOWS_RUNNERS:
        if not (ROOT / rel_path).exists():
            continue
        content = read_text(rel_path)
        if "pressor.py" not in content:
            issues.append(f"{rel_path} does not reference pressor.py")
        if "--doctor" not in content:
            issues.append(f"{rel_path} does not run --doctor before execution")

    for path in ROOT.rglob("*"):
        rel_parts = path.relative_to(ROOT).parts
        if any(part in CACHE_DIRS for part in rel_parts):
            issues.append(f"Generated cache/noise should not be committed: {path.relative_to(ROOT)}")

    if issues:
        print("Repository validation failed:\n")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("Repository validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
