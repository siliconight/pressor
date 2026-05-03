from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from encoder import AudioBatchEncoder, JobPlanItem


class DummyEncoder(AudioBatchEncoder):
    def __init__(self) -> None:
        pass


def _item(source: Path, destination: Path, profile: str = "format-conversion-ogg") -> JobPlanItem:
    return JobPlanItem(
        source=str(source),
        relative_path=source.name,
        profile=profile,
        destination=str(destination),
        input_sha256=AudioBatchEncoder.sha256(source),
        source_size=source.stat().st_size,
    )


def _encoder(codec_name: str, format_name: str, lossy: bool, reason: str) -> DummyEncoder:
    encoder = DummyEncoder()
    encoder.ffmpeg = SimpleNamespace(ffmpeg="ffmpeg", ffprobe="ffprobe")
    encoder.probe = lambda path: SimpleNamespace(codec_name=codec_name, format_name=format_name, channels=2, sample_rate=44100, duration=1.0, bit_rate=128000)
    encoder.inspect_input_lossiness = lambda path, info=None: (lossy, reason)
    return encoder


def test_format_conversion_dry_run_builds_ogg_command_for_mp3_input(tmp_path: Path) -> None:
    source = tmp_path / "input" / "voice.mp3"
    output = tmp_path / "output"
    source.parent.mkdir()
    source.write_bytes(b"fake mp3 bytes")

    item = _item(source, output / "voice.ogg")
    encoder = _encoder("mp3", "mp3", True, "codec mp3 is lossy")

    result = encoder._format_conversion_item(item, overwrite=True, dry_run=True, bitrate="96k", target_format="ogg")

    assert result.success is True
    assert result.changed is False
    assert result.destination == output / "voice.ogg"
    assert "-c:a libopus" in result.message
    assert "-b:a 96k" in result.message
    assert "-f ogg" in result.message


def test_format_conversion_dry_run_builds_opus_command_for_wav_input(tmp_path: Path) -> None:
    source = tmp_path / "input" / "voice.wav"
    output = tmp_path / "output"
    source.parent.mkdir()
    source.write_bytes(b"fake wav bytes")

    item = _item(source, output / "voice.opus", "format-conversion-opus")
    encoder = _encoder("pcm_s16le", "wav", False, "codec pcm_s16le is lossless")

    result = encoder._format_conversion_item(item, overwrite=True, dry_run=True, bitrate="128k", target_format="opus")

    assert result.success is True
    assert result.changed is False
    assert result.destination == output / "voice.opus"
    assert "-c:a libopus" in result.message
    assert "-b:a 128k" in result.message
    assert "-f opus" in result.message


def test_format_conversion_skips_existing_target_format_input(tmp_path: Path) -> None:
    source = tmp_path / "input" / "voice.ogg"
    output = tmp_path / "output"
    source.parent.mkdir()
    source.write_bytes(b"fake ogg bytes")

    item = _item(source, output / "voice.ogg")
    encoder = _encoder("opus", "ogg", True, "codec opus is lossy")

    result = encoder._format_conversion_item(item, overwrite=True, dry_run=True, bitrate="96k", target_format="ogg")

    assert result.success is True
    assert result.changed is False
    assert "Skipped existing .ogg input" in result.message
