import unittest
from pathlib import Path

from pressor.core.audio_probe import AudioInfo, AudioPreview
from pressor.core.perceptual import compute_perceptual_risk, recommend_bitrate, recommend_encode_plan


class PerceptualTests(unittest.TestCase):
    def setUp(self):
        self.profile = {
            'bitrate_mono': '24k',
            'bitrate_stereo': '48k',
            'adaptive_bitrate_mono_min': '16k',
            'adaptive_bitrate_mono_max': '32k',
            'adaptive_bitrate_stereo_min': '32k',
            'adaptive_bitrate_stereo_max': '64k',
            'sample_rate': 48000,
            'max_channels': 2,
        }

    def test_compute_perceptual_risk_returns_expected_shapes(self):
        info = AudioInfo(Path('line.wav'), 1, 48000, 2.0, None)
        preview = AudioPreview(1, 48000, 2.0, 0.25, 0.1, 0.06, 0.08, 0.20, 2.7)
        score, risk, recommendation, reasons = compute_perceptual_risk('dialogue', info, preview)
        self.assertTrue(0 <= score <= 100)
        self.assertIn(risk, {'low', 'medium', 'high'})
        self.assertIn(recommendation, {'aggressive', 'balanced', 'safe'})
        self.assertIsInstance(reasons, list)
        self.assertGreater(len(reasons), 0)

    def test_recommend_bitrate_stays_within_profile_bounds(self):
        info = AudioInfo(Path('line.wav'), 1, 48000, 2.0, None)
        preview = AudioPreview(1, 48000, 2.0, 0.25, 0.1, 0.06, 0.08, 0.20, 2.7)
        bitrate, sample_rate, channels = recommend_bitrate('sfx', self.profile, info, preview)
        self.assertRegex(bitrate, r'^\d+k$')
        value = int(bitrate[:-1])
        self.assertGreaterEqual(value, 16)
        self.assertLessEqual(value, 32)
        self.assertEqual(sample_rate, 48000)
        self.assertEqual(channels, 1)


    def test_dialogue_profile_enforces_quality_floor(self):
        profile = {
            'bitrate_mono': '28k',
            'bitrate_stereo': '40k',
            'adaptive_bitrate_mono_min': '24k',
            'adaptive_bitrate_mono_max': '36k',
            'adaptive_bitrate_stereo_min': '32k',
            'adaptive_bitrate_stereo_max': '48k',
            'sample_rate': 24000,
            'max_channels': 1,
        }
        info = AudioInfo(Path('dialogue.wav'), 1, 48000, 1.5, None)
        preview = AudioPreview(1, 48000, 1.5, 0.66, 0.03, 0.02, 0.11, 0.19, 1.1)

        bitrate, sample_rate, channels = recommend_bitrate('dialogue', profile, info, preview)

        self.assertGreaterEqual(int(bitrate[:-1]), 160)
        self.assertGreaterEqual(sample_rate, 48000)
        self.assertEqual(channels, 1)

    def test_recommend_encode_plan_returns_stable_contract(self):
        info = AudioInfo(Path('sword.wav'), 2, 48000, 1.5, None)
        preview = AudioPreview(2, 48000, 1.5, 0.10, 0.1, 0.11, 0.16, 0.24, 2.9)
        decision = recommend_encode_plan(Path('sword.wav'), 'sfx', self.profile, info, preview)
        self.assertRegex(decision.bitrate, r'^\d+k$')
        self.assertIn(decision.risk, {'low', 'medium', 'high'})
        self.assertIn(decision.recommendation, {'aggressive', 'balanced', 'safe'})
        self.assertGreater(len(decision.reasons), 0)


if __name__ == '__main__':
    unittest.main()
