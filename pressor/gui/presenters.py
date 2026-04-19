from __future__ import annotations

from pathlib import Path
from typing import Any

TABLE_COLUMNS = (
    "relative_path",
    "detected_profile",
    "encode_plan",
    "bitrate",
    "source",
    "confidence",
    "channels",
    "duration",
    "sample_rate",
    "notes",
)

FOLDER_CONVENTIONS_TEXT = """Recommended folder structure

AudioRaw/
  VO/
  Ambient/
  Music/
  SFX/
  Foley/

Recommended mappings

VO/** -> dialogue
Ambient/** -> ambient
Music/** -> music
SFX/** -> sfx
Foley/** -> sfx

Guidance

- Folder routing should be the primary source of truth.
- Auto Profile is a safety net when intent is unclear.
- Manual overrides are useful for edge cases and review.
- Strict Routing is recommended for production runs.
"""


def split_drop_data(root: Any, data: str) -> list[Path]:
    parts = root.tk.splitlist(data)
    cleaned: list[Path] = []
    for part in parts:
        raw = str(part).strip()
        if raw.startswith("{") and raw.endswith("}"):
            raw = raw[1:-1]
        if raw:
            path = Path(raw).expanduser()
            if path.exists():
                cleaned.append(path)
    return cleaned


def describe_drop_selection(paths: list[Path]) -> str:
    if not paths:
        return ""
    file_count = sum(1 for path in paths if path.is_file())
    folder_count = sum(1 for path in paths if path.is_dir())
    parts: list[str] = []
    if file_count:
        parts.append(f"{file_count} file(s)")
    if folder_count:
        parts.append(f"{folder_count} folder(s)")
    return ", ".join(parts) or f"{len(paths)} item(s)"


def dedupe_destination(dest: Path) -> Path:
    if not dest.exists():
        return dest
    index = 2
    while True:
        candidate = dest.with_name(f"{dest.stem}_{index}{dest.suffix}")
        if not candidate.exists():
            return candidate
        index += 1


def build_table_values(item: dict[str, Any]) -> tuple[Any, ...]:
    reasons = item.get("profile_reasons", []) or []
    note = reasons[0] if reasons else ""
    return (
        item.get("relative_path", ""),
        item.get("chosen_profile", ""),
        item.get("perceptual_recommendation", ""),
        item.get("perceptual_bitrate", ""),
        item.get("profile_source", ""),
        item.get("profile_confidence", ""),
        item.get("channels", ""),
        item.get("duration", ""),
        item.get("sample_rate", ""),
        note,
    )


def apply_overrides(items: list[dict[str, Any]], override_map: dict[str, str]) -> list[dict[str, Any]]:
    updated: list[dict[str, Any]] = []
    for item in items:
        copy = dict(item)
        rel = str(copy.get("relative_path", ""))
        if rel in override_map:
            copy["chosen_profile"] = override_map[rel]
            copy["profile_source"] = "manual-override"
            copy["profile_confidence"] = 100
            copy["profile_reasons"] = ["manual override in GUI"]
        updated.append(copy)
    return updated
