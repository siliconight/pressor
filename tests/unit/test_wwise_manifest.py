
import json
import tempfile
import unittest
from pathlib import Path

from encoder import AudioBatchEncoder, FFmpegLocator, ProfileStore, RuleStore
from pressor.pipeline.manifest import build_wwise_manifest, sanitize_wwise_name


class WwiseNamingTests(unittest.TestCase):
    def _write_files(self, root: Path) -> tuple[Path, Path, Path]:
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
        routes.write_text(json.dumps([
            {"pattern": "Weapons/**", "profile": "dialogue"}
        ]), encoding="utf-8")
        wwise.write_text(json.dumps({
            "dialogue": {"wwise_object_path": "\\Actor-Mixer Hierarchy\\Default Work Unit\\Dialogue"}
        }), encoding="utf-8")
        return profiles, routes, wwise

    def test_sanitize_wwise_name_uses_relative_path(self):
        value = sanitize_wwise_name(Path("Weapons/Pistol/Fire.wav"))
        self.assertEqual(value, "Weapons_Pistol_Fire")

    def test_build_wwise_manifest_generates_unique_names_for_same_stem(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_root = root / "input"
            output_root = root / "output"
            (input_root / "Weapons" / "Pistol").mkdir(parents=True)
            (input_root / "Weapons" / "Rifle").mkdir(parents=True)
            (input_root / "Weapons" / "Pistol" / "Fire.wav").write_bytes(b"RIFF")
            (input_root / "Weapons" / "Rifle" / "Fire.wav").write_bytes(b"RIFF")
            output_root.mkdir()
            profiles, routes, wwise = self._write_files(root)
            encoder = AudioBatchEncoder(FFmpegLocator("ffmpeg", "ffprobe"), ProfileStore(profiles), RuleStore(routes))
            payload = build_wwise_manifest(encoder, input_root, output_root, "dialogue", True, False, wwise)
            names = [item["wwise_event"] for item in payload["items"]]
            self.assertEqual(len(names), len(set(names)))
            self.assertIn("Play_Weapons_Pistol_Fire", names)
            self.assertIn("Play_Weapons_Rifle_Fire", names)
