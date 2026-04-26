from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from encoder import AudioBatchEncoder, JobPlanItem


class DummyEncoder(AudioBatchEncoder):
    def __init__(self) -> None:
        pass


def test_lossy_to_ogg_skips_non_lossy_input(tmp_path: Path) -> None:
    source = tmp_path / "input" / "voice.wav"
    output = tmp_path / "output"
    source.parent.mkdir()
    source.write_bytes(b"fake wav bytes")

    item = JobPlanItem(
        source=str(source),
        relative_path="voice.wav",
        profile="lossy-to-ogg",
        destination=str(output / "voice.ogg"),
        input_sha256=AudioBatchEncoder.sha256(source),
        source_size=source.stat().st_size,
    )

    encoder = DummyEncoder()
    encoder.ffmpeg = SimpleNamespace(ffmpeg="ffmpeg", ffprobe="ffprobe")
    encoder.probe = lambda path: SimpleNamespace(codec_name="pcm_s16le", format_name="wav", channels=1, sample_rate=48000, duration=1.0, bit_rate=None)
    encoder.inspect_input_lossiness = lambda path, info=None: (False, "codec pcm_s16le is lossless")

    result = encoder._convert_lossy_to_ogg_item(item, overwrite=False, dry_run=True, bitrate="96k")

    assert result.success is True
    assert result.changed is False
    assert "Skipped non-lossy input" in result.message


def test_lossy_to_ogg_dry_run_builds_ogg_command_for_lossy_input(tmp_path: Path) -> None:
    source = tmp_path / "input" / "voice.mp3"
    output = tmp_path / "output"
    source.parent.mkdir()
    source.write_bytes(b"fake mp3 bytes")

    item = JobPlanItem(
        source=str(source),
        relative_path="voice.mp3",
        profile="lossy-to-ogg",
        destination=str(output / "voice.ogg"),
        input_sha256=AudioBatchEncoder.sha256(source),
        source_size=source.stat().st_size,
    )

    encoder = DummyEncoder()
    encoder.ffmpeg = SimpleNamespace(ffmpeg="ffmpeg", ffprobe="ffprobe")
    encoder.probe = lambda path: SimpleNamespace(codec_name="mp3", format_name="mp3", channels=2, sample_rate=44100, duration=1.0, bit_rate=128000)
    encoder.inspect_input_lossiness = lambda path, info=None: (True, "codec mp3 is lossy")

    result = encoder._convert_lossy_to_ogg_item(item, overwrite=True, dry_run=True, bitrate="96k")

    assert result.success is True
    assert result.changed is False
    assert result.destination == output / "voice.ogg"
    assert "-c:a libopus" in result.message
    assert "-b:a 96k" in result.message
    assert "-f ogg" in result.message
