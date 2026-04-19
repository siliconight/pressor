from __future__ import annotations

import math
import random
import struct
import tempfile
import wave
from pathlib import Path
from typing import List

from encoder import AudioBatchEncoder


def _write_wav(path: Path, samples: List[float] | List[tuple[float, float]], sample_rate: int = 24000, channels: int = 1) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(channels)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        frames = bytearray()
        if channels == 1:
            for sample in samples:
                clamped = max(-1.0, min(1.0, float(sample)))
                frames.extend(struct.pack("<h", int(clamped * 32767)))
        else:
            for left, right in samples:
                l = max(-1.0, min(1.0, float(left)))
                r = max(-1.0, min(1.0, float(right)))
                frames.extend(struct.pack("<hh", int(l * 32767), int(r * 32767)))
        handle.writeframes(bytes(frames))


def _make_music_like(path: Path, duration_sec: float, sample_rate: int = 48000) -> None:
    total = int(duration_sec * sample_rate)
    samples: List[tuple[float, float]] = []
    for i in range(total):
        t = i / sample_rate
        left = 0.28 * math.sin(2 * math.pi * 220 * t) + 0.18 * math.sin(2 * math.pi * 660 * t) + 0.08 * math.sin(2 * math.pi * 5900 * t)
        right = 0.26 * math.sin(2 * math.pi * 247 * t) + 0.16 * math.sin(2 * math.pi * 740 * t) + 0.07 * math.sin(2 * math.pi * 6400 * t)
        shimmer = 0.04 * math.sin(2 * math.pi * 8300 * t)
        samples.append((left + shimmer, right + shimmer))
    _write_wav(path, samples, sample_rate, channels=2)


def _make_noise(path: Path, duration_sec: float, sample_rate: int = 24000, amplitude: float = 0.18) -> None:
    total = int(duration_sec * sample_rate)
    rng = random.Random(42)
    samples = [amplitude * (rng.uniform(-1.0, 1.0)) for _ in range(total)]
    _write_wav(path, samples, sample_rate)


def _make_speech_like(path: Path, duration_sec: float, sample_rate: int = 24000) -> None:
    total = int(duration_sec * sample_rate)
    samples: List[float] = []
    for i in range(total):
        t = i / sample_rate
        envelope = 0.45 + 0.35 * math.sin(2 * math.pi * 2.2 * t)
        carrier = 0.55 * math.sin(2 * math.pi * 170 * t) + 0.25 * math.sin(2 * math.pi * 510 * t) + 0.12 * math.sin(2 * math.pi * 940 * t)
        breath = 0.03 * math.sin(2 * math.pi * 27 * t)
        samples.append(envelope * carrier + breath)
    _write_wav(path, samples, sample_rate)


def _make_sfx_like(path: Path, duration_sec: float = 1.1, sample_rate: int = 48000) -> None:
    total = int(duration_sec * sample_rate)
    rng = random.Random(7)
    samples: List[tuple[float, float]] = []
    for i in range(total):
        t = i / sample_rate
        env = math.exp(-5.5 * t)
        burst = (0.55 * math.sin(2 * math.pi * 420 * t) + 0.28 * math.sin(2 * math.pi * 1260 * t)) * env
        noise = 0.16 * rng.uniform(-1.0, 1.0) * math.exp(-9.0 * t)
        click = 0.0
        if i < int(sample_rate * 0.015):
            click = 0.55 * math.sin(2 * math.pi * 2800 * t) * math.exp(-45.0 * t)
        left = burst + noise + click
        right = 0.95 * burst + 0.9 * noise + 0.85 * click
        samples.append((left, right))
    _write_wav(path, samples, sample_rate, channels=2)


def create_selftest_inputs(root: Path) -> Path:
    input_root = root / "input"
    _make_speech_like(input_root / "Misc" / "line_001.wav", 2.3)
    _make_speech_like(input_root / "Misc" / "line_002.wav", 1.7)
    _make_noise(input_root / "Misc" / "wind_loop.wav", 24.0)
    _make_music_like(input_root / "Misc" / "motif.wav", 26.0)
    _make_sfx_like(input_root / "Misc" / "sword_swing.wav", 1.0)
    return input_root


def run_selftest(args, make_encoder, save_report, save_scan_report, log_file) -> int:
    encoder = make_encoder(args.ffmpeg, args.ffprobe)
    with tempfile.TemporaryDirectory(prefix="pressor_selftest_") as temp_dir:
        root = Path(temp_dir)
        input_root = create_selftest_inputs(root)
        output_root = root / "encoded"
        review_root = root / "review_pack"
        scan_results = encoder.scan(input_root, args.profile, recursive=True, auto_profile=True)
        results = encoder.batch_encode(
            input_root=input_root,
            output_root=output_root,
            default_profile=args.profile,
            recursive=True,
            overwrite=True,
            dry_run=False,
            max_workers=2,
            skip_if_larger=True,
            compare_output_root=review_root,
            auto_profile=True,
        )
        report_path = save_report(results, output_root)
        scan_report_path = save_scan_report(scan_results, output_root / "pressor_scan_report.csv")
        summary = AudioBatchEncoder.summarize(results)
        print("Pressor self-test complete")
        print(summary)
        print(f"CSV report: {report_path}")
        print(f"Scan report: {scan_report_path}")
        print(f"Review pack: {review_root}")
        print(f"Log file: {log_file}")
        failures = [item for item in results if not item.success]
        if failures:
            for item in failures:
                print(f"FAILED: {item.source} -> {item.message}")
            return 2
        if args.keep_selftest_output:
            dest_root = Path(args.keep_selftest_output).resolve()
            if dest_root.exists():
                raise SystemExit(f"Self-test output directory already exists: {dest_root}")
            import shutil
            dest_root.mkdir(parents=True, exist_ok=False)
            shutil.copytree(input_root, dest_root / "input")
            shutil.copytree(output_root, dest_root / "encoded")
            shutil.copytree(review_root, dest_root / "review_pack")
            shutil.copy2(report_path, dest_root / "pressor_report.csv")
            shutil.copy2(scan_report_path, dest_root / "pressor_scan_report.csv")
            print(f"Saved self-test artifacts to: {dest_root}")
        return 0
