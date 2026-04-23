from pathlib import Path
from types import SimpleNamespace

from pressor.pipeline.run_job import _route_structured_outputs


def test_route_structured_outputs_copies_skipped_and_failed(tmp_path):
    input_root = tmp_path / "input"
    skipped_root = tmp_path / "skipped"
    failed_root = tmp_path / "failed"
    (input_root / "a").mkdir(parents=True)
    (input_root / "b").mkdir(parents=True)
    skipped_src = input_root / "a" / "skip.wav"
    failed_src = input_root / "b" / "fail.wav"
    skipped_src.write_bytes(b"skip")
    failed_src.write_bytes(b"fail")

    results = [
        SimpleNamespace(source=skipped_src, success=True, changed=False, message="Skipped lossy input: already lossy"),
        SimpleNamespace(source=failed_src, success=False, changed=False, message="ffmpeg failed"),
    ]

    skipped_count, failed_count = _route_structured_outputs(results, input_root, skipped_root, failed_root)

    assert skipped_count == 1
    assert failed_count == 1
    assert (skipped_root / "a" / "skip.wav").read_bytes() == b"skip"
    assert (failed_root / "b" / "fail.wav").read_bytes() == b"fail"
