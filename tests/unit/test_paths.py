import tempfile
import unittest
from pathlib import Path

from pressor.core.paths import create_run_workspace, find_supported_audio_files, validate_path_relationships
from encoder import EncoderError


class PathsTests(unittest.TestCase):
    def test_find_supported_audio_files_filters_extensions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'a.wav').write_bytes(b'1')
            (root / 'b.txt').write_text('x', encoding='utf-8')
            (root / 'sub').mkdir()
            (root / 'sub' / 'c.ogg').write_bytes(b'2')
            files = find_supported_audio_files(root)
            self.assertEqual([p.name for p in files], ['a.wav', 'c.ogg'])


    def test_create_run_workspace_creates_timestamped_layout(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'out'
            workspace = create_run_workspace(root, run_label='music pass')
            self.assertTrue(workspace.run_root.exists())
            self.assertTrue(workspace.encoded_root.exists())
            self.assertTrue(workspace.reports_root.exists())
            self.assertIn('music-pass', workspace.run_root.name)
            self.assertEqual(workspace.review_root.parent, workspace.run_root)

    def test_create_run_workspace_creates_structured_folders_when_enabled(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'out'
            workspace = create_run_workspace(root, structured_output=True)
            self.assertTrue(workspace.encoded_root.exists())
            self.assertTrue(workspace.skipped_root.exists())
            self.assertTrue(workspace.failed_root.exists())

    def test_validate_path_relationships_rejects_nested_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_root = root / 'input'
            input_root.mkdir()
            nested_output = input_root / 'out'
            with self.assertRaises(EncoderError):
                validate_path_relationships(input_root, nested_output, None)


if __name__ == '__main__':
    unittest.main()
