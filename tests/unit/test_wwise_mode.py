
import unittest

from pressor.cli.args import parse_args


class WwiseModeArgsTests(unittest.TestCase):
    def test_wwise_mode_flag_parses(self):
        args = parse_args(["--wwise-mode"])
        self.assertTrue(args.wwise_mode)

    def test_changed_only_can_still_be_explicit(self):
        args = parse_args(["--wwise-mode", "--changed-only"])
        self.assertTrue(args.wwise_mode)
        self.assertTrue(args.changed_only)
