
from pathlib import Path

from pressor.tools.benchmark import build_benchmark_summary


def test_build_benchmark_summary_reports_reduction(tmp_path: Path):
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    output_dir.mkdir()

    (input_dir / "a.bin").write_bytes(b"x" * 100)
    (output_dir / "a.bin").write_bytes(b"x" * 25)

    summary = build_benchmark_summary(input_dir, output_dir)

    assert summary["input_bytes"] == 100
    assert summary["output_bytes"] == 25
    assert round(summary["reduction_pct"], 2) == 75.0
