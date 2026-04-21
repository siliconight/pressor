from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict

from encoder import AudioBatchEncoder, EncoderError
from pressor.core.config import load_wwise_config
from pressor.core.paths import default_output_root_for_manifest_build


def load_manifest_context(manifest_path: Path) -> Dict[str, object]:
    try:
        with manifest_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except FileNotFoundError as exc:
        raise EncoderError(f"Manifest not found: {manifest_path}") from exc
    except json.JSONDecodeError as exc:
        raise EncoderError(f"Manifest is not valid JSON: {manifest_path}") from exc
    if not isinstance(payload, dict):
        raise EncoderError(f"Manifest must contain a JSON object: {manifest_path}")
    return payload




def sanitize_wwise_name(relative_path: Path) -> str:
    parts = list(relative_path.with_suffix("").parts)
    joined = "_".join(parts)
    cleaned = re.sub(r"[^A-Za-z0-9_]+", "_", joined)
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    return cleaned or "Unnamed"


def _raise_on_wwise_name_collisions(items: list[Dict[str, object]]) -> None:
    event_sources: dict[str, list[str]] = {}
    object_sources: dict[str, list[str]] = {}

    for item in items:
        source = str(item.get("source", ""))
        event_name = str(item.get("wwise_event", ""))
        object_name = str(item.get("wwise_object_path", ""))
        event_sources.setdefault(event_name, []).append(source)
        object_sources.setdefault(object_name, []).append(source)

    duplicate_events = {name: sources for name, sources in event_sources.items() if len(sources) > 1}
    duplicate_objects = {name: sources for name, sources in object_sources.items() if len(sources) > 1}

    if duplicate_events:
        name, sources = next(iter(duplicate_events.items()))
        raise EncoderError(
            "Wwise manifest generation found duplicate event names: "
            f"{name} | Sources: {', '.join(sources)}"
        )

    if duplicate_objects:
        name, sources = next(iter(duplicate_objects.items()))
        raise EncoderError(
            "Wwise manifest generation found duplicate object paths: "
            f"{name} | Sources: {', '.join(sources)}"
        )

def build_manifest(
    encoder: AudioBatchEncoder,
    manifest_path: Path,
    input_root: Path,
    output_root: Path | None,
    default_profile: str,
    recursive: bool,
    auto_profile: bool,
    strict_routing: bool,
    wwise_prep: bool,
) -> Path:
    if output_root is None:
        output_root = default_output_root_for_manifest_build(input_root)
    extra = {"mode": "wwise-prep"} if wwise_prep else None
    forced_container = ".wav" if wwise_prep else None
    encoder.save_manifest(
        manifest_path,
        input_root,
        output_root,
        default_profile,
        recursive=recursive,
        forced_container=forced_container,
        extra=extra,
        auto_profile=auto_profile,
        strict_routing=strict_routing,
    )
    return manifest_path


def build_wwise_manifest(
    encoder: AudioBatchEncoder,
    input_root: Path,
    output_root: Path,
    default_profile: str,
    recursive: bool,
    auto_profile: bool,
    wwise_file: Path,
) -> Dict[str, object]:
    settings = load_wwise_config(wwise_file)
    plan = encoder.build_plan(
        input_root,
        output_root,
        default_profile,
        recursive=recursive,
        forced_container=".wav",
        auto_profile=auto_profile,
        strict_routing=False,
    )
    items: list[Dict[str, object]] = []
    for item in plan:
        relative = Path(item.relative_path)
        object_group = settings.get(item.profile, {}).get(
            "wwise_object_path", f"\\Actor-Mixer Hierarchy\\Default Work Unit\\{item.profile.title()}"
        )
        share_set = settings.get(item.profile, {}).get("wwise_share_set", "")
        items.append(
            {
                "source": item.source,
                "prepared_path": item.destination,
                "relative_path": item.relative_path,
                "profile": item.profile,
                "profile_source": item.profile_source,
                "profile_confidence": item.profile_confidence,
                "profile_reasons": item.profile_reasons,
                "wwise_object_path": f"{object_group}\\{sanitize_wwise_name(relative)}",
                "wwise_event": f"Play_{sanitize_wwise_name(relative)}",
                "wwise_share_set": share_set,
            }
        )
    _raise_on_wwise_name_collisions(items)
    return {
        "input_root": str(input_root.resolve()),
        "output_root": str(output_root.resolve()),
        "default_profile": default_profile,
        "recursive": recursive,
        "auto_profile": auto_profile,
        "items": items,
    }


def write_wwise_import_json(import_payload: Dict[str, object], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(import_payload, handle, indent=2)
    return output_path


def write_wwise_import_tsv(import_payload: Dict[str, object], output_path: Path) -> Path:
    import csv

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(["AudioFile", "ObjectPath", "Event", "Conversion", "Profile", "ProfileSource", "Confidence", "Notes"])
        for item in import_payload["items"]:
            writer.writerow(
                [
                    item["prepared_path"],
                    item["wwise_object_path"],
                    item["wwise_event"],
                    item["wwise_share_set"],
                    item["profile"],
                    item.get("profile_source", ""),
                    item.get("profile_confidence", ""),
                    "Starter mapping generated by Pressor. Review before import. " + " | ".join(item.get("profile_reasons", [])),
                ]
            )
    return output_path
