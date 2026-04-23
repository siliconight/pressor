import unittest
from pathlib import Path


class RunnerIncrementalDefaultsTests(unittest.TestCase):
    def test_windows_runner_does_not_force_changed_only(self):
        content = Path("run_windows.bat").read_text(encoding="utf-8")
        self.assertNotIn("--changed-only", content)
        self.assertIn("--skip-lossy-inputs", content)

    def test_linux_runner_does_not_force_changed_only(self):
        content = Path("scripts/run_linux.sh").read_text(encoding="utf-8")
        self.assertNotIn("--changed-only", content)
        self.assertIn("--skip-lossy-inputs", content)
