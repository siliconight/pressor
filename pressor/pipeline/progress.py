from __future__ import annotations

from pathlib import Path


def print_progress_header(total_files: int) -> None:
    print(f"Found {total_files} supported audio files.")
    print("")


def print_progress_result(index: int, total: int, source_name: str, profile: str | None, status: str, reason: str | None = None) -> None:
    print(f"[{index}/{total}] {source_name}")
    if profile:
        print(f"       Profile: {profile}")
    print(f"       Status : {status}")
    if reason:
        print(f"       Reason : {reason}")
    print("")


def print_run_summary(succeeded: int, skipped: int, failed: int, output_root: str, reports_root: str) -> None:
    print("Run complete.")
    print("")
    print(f"Succeeded: {succeeded}")
    print(f"Skipped  : {skipped}")
    print(f"Failed   : {failed}")
    print(f"Output   : {output_root}")
    print(f"Reports  : {reports_root}")
    print("")
