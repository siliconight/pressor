"""Planning helpers for Pressor batch operations.

Extracted during the refactor so discovery, routing, and destination planning
are easier to understand independently of encode execution.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Iterable, List, Optional


def detect_destination_conflicts(items: List[Any], destination_getter: Callable[[Any], str]) -> None:
    seen_destinations: set[str] = set()
    for item in items:
        destination_key = str(Path(destination_getter(item))).casefold()
        if destination_key in seen_destinations:
            raise ValueError(f"Multiple inputs would write to the same destination: {destination_getter(item)}")
        seen_destinations.add(destination_key)


def validate_plan(items: List[Any], destination_getter: Callable[[Any], str]) -> List[Any]:
    if not items:
        raise ValueError("No supported audio files found.")
    detect_destination_conflicts(items, destination_getter)
    return items


def build_encode_plan(
    *,
    input_root: Path,
    output_root: Path,
    default_profile: str,
    recursive: bool,
    forced_container: Optional[str],
    auto_profile: bool,
    strict_routing: bool,
    iter_audio_files: Callable[[Path, bool], Iterable[Path]],
    sanitize_relative_path: Callable[[str], Path],
    choose_profile: Callable[..., Any],
    get_profile: Callable[[str], dict],
    sha256: Callable[[Path], str],
    ensure_not_nested: Callable[[Path, Path, str], None],
    plan_item_factory: Callable[..., Any],
) -> List[Any]:
    input_root = input_root.resolve()
    output_root = output_root.resolve()
    ensure_not_nested(input_root, output_root, "Output folder")
    output_root.mkdir(parents=True, exist_ok=True)
    items: List[Any] = []
    for source in iter_audio_files(input_root, recursive):
        rel_path = sanitize_relative_path(source.resolve().relative_to(input_root).as_posix())
        decision = choose_profile(rel_path, default_profile, source_path=source, auto_profile=auto_profile)
        if strict_routing and getattr(decision, 'source', '') != 'routing-rule':
            raise ValueError(f"Strict routing requires a routing rule match for {rel_path.as_posix()} (got {getattr(decision, 'source', 'unknown')} -> {getattr(decision, 'profile', 'unknown')})")
        if forced_container is None:
            profile = get_profile(getattr(decision, 'profile'))
            destination = (output_root / rel_path).with_suffix(profile['container'])
        else:
            destination = (output_root / rel_path).with_suffix(forced_container)
        items.append(plan_item_factory(
            source=str(source),
            relative_path=rel_path.as_posix(),
            profile=getattr(decision, 'profile'),
            destination=str(destination),
            input_sha256=sha256(source),
            source_size=source.stat().st_size,
            profile_source=getattr(decision, 'source', 'default'),
            profile_confidence=getattr(decision, 'confidence', 100),
            profile_reasons=getattr(decision, 'reasons', None),
        ))
    validate_plan(items, lambda item: getattr(item, 'destination'))
    return items
