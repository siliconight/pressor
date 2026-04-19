import unittest

from pressor.core.audio_probe import AudioPreview
from pressor.core.classifier import classify_audio_preview


class ClassifierTests(unittest.TestCase):
    def test_classifies_dialogue_like_preview(self):
        preview = AudioPreview(1, 48000, 3.0, 0.30, 0.1, 0.10, 0.07, 0.12, 1.8)
        decision = classify_audio_preview(preview)
        self.assertEqual(decision.profile, 'dialogue')
        self.assertEqual(decision.source, 'auto-preview')
        self.assertTrue(35 <= decision.confidence <= 98)

    def test_classifies_music_like_preview(self):
        preview = AudioPreview(2, 48000, 75.0, 0.01, 0.1, 0.04, 0.06, 0.09, 1.7)
        decision = classify_audio_preview(preview)
        self.assertEqual(decision.profile, 'music')


if __name__ == '__main__':
    unittest.main()
