from pathlib import Path
import unittest

from pressor.core.audio_probe import AudioInfo, assess_input_lossiness


class TestAudioProbeLossiness(unittest.TestCase):
    def test_lossless_codec_not_flagged(self) -> None:
        info = AudioInfo(path=Path("voice.m4a"), channels=2, sample_rate=48000, duration=1.0, bit_rate=128000, codec_name="alac", format_name="mov,mp4,m4a,3gp,3g2,mj2")
        is_lossy, reason = assess_input_lossiness(Path("voice.m4a"), info)
        self.assertFalse(is_lossy)
        self.assertIn("lossless", reason)

    def test_lossy_codec_flagged(self) -> None:
        info = AudioInfo(path=Path("voice.wav"), channels=1, sample_rate=48000, duration=1.0, bit_rate=128000, codec_name="opus", format_name="ogg")
        is_lossy, reason = assess_input_lossiness(Path("voice.wav"), info)
        self.assertTrue(is_lossy)
        self.assertIn("lossy", reason)

    def test_lossy_extension_flagged_when_codec_unknown(self) -> None:
        is_lossy, reason = assess_input_lossiness(Path("voice.opus"), None)
        self.assertTrue(is_lossy)
        self.assertIn("extension", reason)
