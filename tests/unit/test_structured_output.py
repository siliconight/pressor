import tempfile
import unittest
from pathlib import Path

from pressor.core.paths import create_run_workspace


class StructuredOutputTests(unittest.TestCase):
    def test_create_run_workspace_creates_structured_folders_when_enabled(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = create_run_workspace(Path(tmp) / "out", structured_output=True)
            self.assertTrue(workspace.encoded_root.exists())
            self.assertTrue(workspace.skipped_root.exists())
            self.assertTrue(workspace.failed_root.exists())
            self.assertTrue(workspace.reports_root.exists())

    def test_create_run_workspace_keeps_legacy_layout_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = create_run_workspace(Path(tmp) / "out")
            self.assertTrue(workspace.encoded_root.exists())
            self.assertIsNone(workspace.skipped_root)
            self.assertIsNone(workspace.failed_root)


if __name__ == "__main__":
    unittest.main()
