
import json
import tempfile
import unittest
from pathlib import Path

from encoder import AudioBatchEncoder, EncoderError, FFmpegLocator, ProfileStore, RuleStore


class ManifestContainmentTests(unittest.TestCase):
    def _write_profiles(self, root: Path) -> tuple[Path, Path, Path]:
        profiles = root / "profiles.json"
        routes = root / "routes.json"
        wwise = root / "wwise.json"
        profiles.write_text(json.dumps({
            "dialogue": {
                "codec": "libopus",
                "container": ".opus",
                "bitrate_mono": "24k",
                "bitrate_stereo": "48k",
                "max_channels": 2
            }
        }), encoding="utf-8")
        routes.write_text("[]", encoding="utf-8")
        wwise.write_text("{}", encoding="utf-8")
        return profiles, routes, wwise

    def test_manifest_destination_inside_output_root_is_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profiles, routes, wwise = self._write_profiles(root)
            encoder = AudioBatchEncoder(FFmpegLocator("ffmpeg", "ffprobe"), ProfileStore(profiles), RuleStore(routes))
            manifest = root / "manifest.json"
            output_root = root / "out"
            payload = {
                "output_root": str(output_root),
                "items": [{
                    "source": str(root / "input.wav"),
                    "relative_path": "input.wav",
                    "profile": "dialogue",
                    "destination": str(output_root / "input.m4a"),
                    "input_sha256": "abc",
                    "source_size": 123
                }]
            }
            manifest.write_text(json.dumps(payload), encoding="utf-8")
            items = encoder._load_manifest(manifest)
            self.assertEqual(len(items), 1)

    def test_manifest_destination_outside_output_root_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profiles, routes, wwise = self._write_profiles(root)
            encoder = AudioBatchEncoder(FFmpegLocator("ffmpeg", "ffprobe"), ProfileStore(profiles), RuleStore(routes))
            manifest = root / "manifest.json"
            output_root = root / "out"
            payload = {
                "output_root": str(output_root),
                "items": [{
                    "source": str(root / "input.wav"),
                    "relative_path": "input.wav",
                    "profile": "dialogue",
                    "destination": str(root / "elsewhere" / "input.m4a"),
                    "input_sha256": "abc",
                    "source_size": 123
                }]
            }
            manifest.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(EncoderError):
                encoder._load_manifest(manifest)
