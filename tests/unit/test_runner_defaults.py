import unittest
from pathlib import Path


class RunnerDefaultsTests(unittest.TestCase):
    def test_windows_runner_skips_lossy_inputs(self):
        content = Path("run_windows.bat").read_text(encoding="utf-8")
        self.assertIn("--skip-lossy-inputs", content)
        self.assertNotIn("powershell -ExecutionPolicy Bypass", content)

    def test_linux_runner_skips_lossy_inputs(self):
        content = Path("scripts/run_linux.sh").read_text(encoding="utf-8")
        self.assertIn("--skip-lossy-inputs", content)
        self.assertNotIn("--fail-on-lossy-inputs", content)


if __name__ == "__main__":
    unittest.main()
