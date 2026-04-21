
from pathlib import Path

from pressor.pipeline.change_detection import filter_changed_manifest, update_state_from_manifest_results


def test_filter_changed_manifest_skips_unchanged_entries():
    payload = {
        "items": [
            {"source": "/tmp/a.wav", "input_sha256": "111", "profile": "dialogue"},
            {"source": "/tmp/b.wav", "input_sha256": "222", "profile": "music"},
        ]
    }
    state = {
        "entries": {
            "/tmp/a.wav": {"input_sha256": "111", "profile": "dialogue", "mode": "encode"}
        }
    }

    changed_payload, changed_count, unchanged_count = filter_changed_manifest(payload, state, "encode")

    assert changed_count == 1
    assert unchanged_count == 1
    assert changed_payload["items"][0]["source"] == "/tmp/b.wav"


def test_update_state_from_manifest_results_only_updates_successful_sources():
    state = {"entries": {}}
    manifest_payload = {
        "items": [
            {"source": "/tmp/a.wav", "input_sha256": "111", "profile": "dialogue"},
            {"source": "/tmp/b.wav", "input_sha256": "222", "profile": "music"},
        ]
    }

    updated = update_state_from_manifest_results(state, manifest_payload, {"/tmp/b.wav"}, "encode")

    assert "/tmp/a.wav" not in updated["entries"]
    assert updated["entries"]["/tmp/b.wav"]["input_sha256"] == "222"
    assert updated["entries"]["/tmp/b.wav"]["profile"] == "music"
