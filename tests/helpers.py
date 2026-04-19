from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
PRESSOR = ROOT / 'pressor.py'
TMP = ROOT / 'tests' / '_tmp'


def reset_tmp() -> None:
    if TMP.exists():
        shutil.rmtree(TMP)
    TMP.mkdir(parents=True, exist_ok=True)


def run_cmd(args: list[str], expect_success: bool = True, cwd: Path | None = None, timeout: int = 300) -> subprocess.CompletedProcess:
    proc = subprocess.run(
        args,
        cwd=str(cwd or ROOT),
        text=True,
        capture_output=True,
        timeout=timeout,
    )
    if expect_success and proc.returncode != 0:
        raise AssertionError(
            f"Command failed: {' '.join(args)}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
        )
    if not expect_success and proc.returncode == 0:
        raise AssertionError(
            f"Command unexpectedly succeeded: {' '.join(args)}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
        )
    return proc


def pressor_args(*extra: str) -> list[str]:
    return [PYTHON, str(PRESSOR), *extra]


def assert_exists(path: os.PathLike[str] | str) -> None:
    p = Path(path)
    if not p.exists():
        raise AssertionError(f"Expected path to exist: {p}")


def assert_contains(text: str, needle: str) -> None:
    if needle not in text:
        raise AssertionError(f"Expected to find {needle!r} in output:\n{text}")
