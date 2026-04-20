import unittest
from pathlib import Path

from pressor.core.audio_probe import AudioInfo, assess_input_lossiness
from pressor.core.paths import is_within, normalize_path


class SecurityTests(unittest.TestCase):
    def test_normalize_path_resolves(self):
        path = normalize_path('.')
        self.assertTrue(path.is_absolute())

    def test_is_within_true_for_nested_child(self):
        parent = Path('/tmp/pressor_parent').resolve()
        child = parent / 'child'
        self.assertTrue(is_within(parent, child))

    def test_is_within_false_for_sibling(self):
        parent = Path('/tmp/pressor_parent').resolve()
        child = Path('/tmp/pressor_other').resolve()
        self.assertFalse(is_within(parent, child))

    def test_lossy_detection_uses_codec_as_truth_when_present(self):
        info = AudioInfo(path=Path('voice.ogg'), channels=2, sample_rate=48000, duration=1.0, bit_rate=128000, codec_name='flac', format_name='ogg')
        is_lossy, reason = assess_input_lossiness(Path('voice.ogg'), info)
        self.assertFalse(is_lossy)
        self.assertIn('codec flac', reason)
