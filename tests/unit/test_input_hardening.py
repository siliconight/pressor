from pathlib import Path

import encoder as encoder_module
from encoder import AudioBatchEncoder, FFmpegLocator, ProfileStore, RejectedInputRecord, RuleStore
from pressor.core.audio_probe import AudioInfo
from pressor.core.paths import create_run_workspace


def build_encoder(tmp_path):
    ffmpeg = FFmpegLocator('ffmpeg', 'ffprobe')
    profiles = ProfileStore(Path('pressor.profiles.json'))
    rules = RuleStore(Path('pressor.routing.json'))
    return AudioBatchEncoder(ffmpeg, profiles, rules)


def test_create_run_workspace_creates_rejected_folder_when_structured(tmp_path):
    workspace = create_run_workspace(tmp_path / 'out', structured_output=True)
    assert workspace.rejected_root is not None
    assert workspace.rejected_root.exists()


def test_blocked_extension_is_rejected(tmp_path):
    root = tmp_path / 'input'
    root.mkdir()
    path = root / 'payload.exe'
    path.write_bytes(b'MZ')
    enc = build_encoder(tmp_path)

    accepted, rejected = enc._classify_input_candidate(path, root, sniff_input_audio=True)

    assert not accepted
    assert isinstance(rejected, RejectedInputRecord)
    assert rejected.reason == 'blocked_extension'


def test_unknown_extension_can_be_accepted_when_ffprobe_confirms_audio(tmp_path, monkeypatch):
    root = tmp_path / 'input'
    root.mkdir()
    path = root / 'mystery.asset'
    path.write_bytes(b'not really audio, probe is mocked')
    enc = build_encoder(tmp_path)

    def fake_probe(candidate, ffprobe_bin, validate_input_file=None):
        return AudioInfo(path=candidate, channels=2, sample_rate=48000, duration=1.0, bit_rate=128000, codec_name='flac', format_name='flac')

    monkeypatch.setattr(encoder_module, 'probe_audio_file', fake_probe)

    accepted, rejected = enc._classify_input_candidate(path, root, sniff_input_audio=True)

    assert accepted
    assert rejected is None
