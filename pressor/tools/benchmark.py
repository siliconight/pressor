
from __future__ import annotations

import os
from pathlib import Path


def folder_size(path: Path) -> int:
    total = 0
    for dirpath, _, filenames in os.walk(path):
        for filename in filenames:
            fp = Path(dirpath) / filename
            if fp.exists() and fp.is_file():
                total += fp.stat().st_size
    return total


def format_bytes(size: int) -> str:
    value = float(size)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if value < 1024 or unit == "TB":
            return f"{value:.2f} {unit}"
        value /= 1024
    return f"{value:.2f} TB"


def build_benchmark_summary(input_root: Path, output_root: Path) -> dict[str, object]:
    input_bytes = folder_size(input_root)
    output_bytes = folder_size(output_root)
    reduction_pct = 0.0
    if input_bytes > 0:
        reduction_pct = (1.0 - (output_bytes / input_bytes)) * 100.0
    return {
        "input_bytes": input_bytes,
        "output_bytes": output_bytes,
        "reduction_pct": reduction_pct,
        "input_human": format_bytes(input_bytes),
        "output_human": format_bytes(output_bytes),
    }


def print_benchmark_summary(input_root: Path, output_root: Path) -> None:
    summary = build_benchmark_summary(input_root, output_root)
    print("Benchmark summary.")
    print("")
    print(f"Input Size : {summary['input_human']}")
    print(f"Output Size: {summary['output_human']}")
    print(f"Reduction  : {summary['reduction_pct']:.2f}%")
    print("")
