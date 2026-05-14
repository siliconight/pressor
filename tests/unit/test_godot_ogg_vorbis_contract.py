from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from pressor.core.encoder import build_ffmpeg_command


def test_output_format_ogg_builds_vorbis_ogg_command() -> None:
    tuning = SimpleNamespace(channels=2, bitrate="128k", sample_rate=48000)
    cmd, temp_output = build_ffmpeg_command(
        "ffmpeg",
        Path("input.wav"),
        Path("output.ogg"),
        {"codec": "libvorbis", "container": ".ogg", "quality": 5},
        tuning,
        True,
    )

    assert temp_output.name == "output.part.ogg"
    assert "libvorbis" in cmd
    assert "libopus" not in cmd
    assert "-q:a" in cmd
    assert "-f" in cmd
    assert cmd[cmd.index("-f") + 1] == "ogg"


def test_output_format_opus_builds_opus_command() -> None:
    tuning = SimpleNamespace(channels=2, bitrate="128k", sample_rate=48000)
    cmd, temp_output = build_ffmpeg_command(
        "ffmpeg",
        Path("input.wav"),
        Path("output.opus"),
        {"codec": "libopus", "container": ".opus"},
        tuning,
        True,
    )

    assert temp_output.name == "output.part.opus"
    assert "libopus" in cmd
    assert "libvorbis" not in cmd
    assert "-b:a" in cmd
    assert "-f" in cmd
    assert cmd[cmd.index("-f") + 1] == "opus"
