from __future__ import annotations

import json
from pathlib import Path

from encoder import AudioBatchEncoder, ProfileStore, RuleStore


class DummyLocator:
    ffmpeg = "ffmpeg"
    ffprobe = "ffprobe"


def _write_configs(root: Path) -> tuple[Path, Path]:
    profiles = root / "profiles.json"
    routes = root / "routes.json"
    profiles.write_text(json.dumps({
        "dialogue": {
            "codec": "aac",
            "container": ".m4a",
            "bitrate_mono": "64k",
            "bitrate_stereo": "96k",
            "max_channels": 2
        }
    }), encoding="utf-8")
    routes.write_text("[]", encoding="utf-8")
    return profiles, routes


def test_batch_encode_forced_container_opus_changes_destination_suffix(tmp_path: Path) -> None:
    input_root = tmp_path / "input"
    output_root = tmp_path / "output"
    input_root.mkdir()
    source = input_root / "voice.wav"
    source.write_bytes(b"fake wav bytes")

    profiles, routes = _write_configs(tmp_path)
    encoder = AudioBatchEncoder(DummyLocator(), ProfileStore(profiles), RuleStore(routes))

    plan = encoder.build_plan(
        input_root,
        output_root,
        "dialogue",
        forced_container=".opus",
    )

    assert len(plan) == 1
    assert Path(plan[0].destination).suffix == ".opus"


def test_batch_encode_forced_container_ogg_changes_destination_suffix(tmp_path: Path) -> None:
    input_root = tmp_path / "input"
    output_root = tmp_path / "output"
    input_root.mkdir()
    source = input_root / "voice.wav"
    source.write_bytes(b"fake wav bytes")

    profiles, routes = _write_configs(tmp_path)
    encoder = AudioBatchEncoder(DummyLocator(), ProfileStore(profiles), RuleStore(routes))

    plan = encoder.build_plan(
        input_root,
        output_root,
        "dialogue",
        forced_container=".ogg",
    )

    assert len(plan) == 1
    assert Path(plan[0].destination).suffix == ".ogg"
