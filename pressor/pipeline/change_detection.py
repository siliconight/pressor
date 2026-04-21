
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DEFAULT_STATE_FILENAME = "pressor_state_manifest.json"


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"entries": {}}
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        return {"entries": {}}
    payload.setdefault("entries", {})
    return payload


def save_state(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    return path


def _fingerprint_for_item(item: dict[str, Any], mode: str) -> dict[str, Any]:
    return {
        "input_sha256": item.get("input_sha256", ""),
        "profile": item.get("profile", ""),
        "mode": mode,
    }


def filter_changed_manifest(payload: dict[str, Any], state_payload: dict[str, Any], mode: str) -> tuple[dict[str, Any], int, int]:
    raw_items = payload.get("items", [])
    entries = state_payload.setdefault("entries", {})
    changed_items: list[dict[str, Any]] = []
    unchanged_count = 0

    for item in raw_items:
        source = str(item.get("source", ""))
        current = _fingerprint_for_item(item, mode)
        previous = entries.get(source)
        if previous == current:
            unchanged_count += 1
            continue
        changed_items.append(item)

    filtered = dict(payload)
    filtered["items"] = changed_items
    filtered["changed_only"] = True
    filtered["changed_item_count"] = len(changed_items)
    filtered["unchanged_item_count"] = unchanged_count
    return filtered, len(changed_items), unchanged_count


def update_state_from_manifest_results(
    state_payload: dict[str, Any],
    manifest_payload: dict[str, Any],
    successful_sources: set[str],
    mode: str,
) -> dict[str, Any]:
    entries = state_payload.setdefault("entries", {})
    for item in manifest_payload.get("items", []):
        source = str(item.get("source", ""))
        if source in successful_sources:
            entries[source] = _fingerprint_for_item(item, mode)
    return state_payload
