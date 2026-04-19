import tempfile
import unittest
from pathlib import Path

from pressor.core.routing import RouteRule, matches_route_rule, resolve_profile_from_route, validate_strict_routing


class RoutingTests(unittest.TestCase):
    def test_matches_route_rule_for_top_level_and_recursive(self):
        rule = RouteRule(pattern='VO/**', profile='dialogue')
        self.assertTrue(matches_route_rule('VO/line.wav', rule))
        self.assertTrue(matches_route_rule('Some/VO/line.wav', rule))
        self.assertFalse(matches_route_rule('Music/theme.wav', rule))

    def test_resolve_profile_from_route_skips_unknown_profiles(self):
        rules = [
            RouteRule(pattern='VO/**', profile='unknown'),
            RouteRule(pattern='VO/**', profile='dialogue'),
        ]
        matched = resolve_profile_from_route('VO/line.wav', rules, {'dialogue'})
        self.assertIsNotNone(matched)
        self.assertEqual(matched.profile, 'dialogue')

    def test_validate_strict_routing_reports_non_rule_matches(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src = root / 'Misc' / 'line.wav'
            src.parent.mkdir(parents=True)
            src.write_bytes(b'1')

            def iter_audio_files(input_root, recursive):
                return [src]

            def sanitize_relative_path(value):
                return Path(value)

            class Decision:
                profile = 'dialogue'
                source = 'auto-preview'
                confidence = 88
                reasons = ['fallback']

            def choose_profile(rel_path, default_profile, source_path=None, auto_profile=False):
                return Decision()

            issues = validate_strict_routing(root, iter_audio_files, sanitize_relative_path, choose_profile, 'dialogue')
            self.assertEqual(len(issues), 1)
            self.assertEqual(issues[0]['profile_source'], 'auto-preview')


if __name__ == '__main__':
    unittest.main()
