import unittest

from pressor.core.profiles import get_profile, resolve_profile_settings, validate_profile_name


class ProfilesTests(unittest.TestCase):
    def setUp(self):
        self.profiles = {
            'dialogue': {
                'codec': 'libopus',
                'container': '.opus',
                'bitrate_mono': '24k',
                'bitrate_stereo': '48k',
                'max_channels': 2,
            }
        }

    def test_get_profile_returns_requested_profile(self):
        self.assertEqual(get_profile(self.profiles, 'dialogue')['codec'], 'libopus')

    def test_validate_profile_name_rejects_unknown(self):
        with self.assertRaises(ValueError):
            validate_profile_name('music', self.profiles)

    def test_resolve_profile_settings_validates_definition(self):
        resolved = resolve_profile_settings(
            self.profiles,
            'dialogue',
            allowed_codecs={'libopus', 'aac'},
            allowed_containers={'.opus', '.m4a', '.wav'},
        )
        self.assertEqual(resolved['container'], '.opus')


if __name__ == '__main__':
    unittest.main()
