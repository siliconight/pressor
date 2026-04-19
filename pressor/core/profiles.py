from __future__ import annotations

from typing import Any, Dict, Iterable


def validate_profile_name(name: str, profiles: Dict[str, Dict[str, Any]]) -> None:
    if name not in profiles:
        raise ValueError(f"Unknown profile: {name}")


def get_profile(profiles: Dict[str, Dict[str, Any]], name: str) -> Dict[str, Any]:
    validate_profile_name(name, profiles)
    return profiles[name]


def validate_profile_definition(
    name: str,
    profile: Dict[str, Any],
    *,
    allowed_codecs: Iterable[str],
    allowed_containers: Iterable[str],
) -> None:
    if not isinstance(profile, dict):
        raise ValueError(f"Profile {name} must be an object.")
    codec = profile.get("codec")
    container = profile.get("container")
    if codec not in set(allowed_codecs):
        raise ValueError(f"Profile {name} has unsupported codec: {codec}")
    if container not in set(allowed_containers):
        raise ValueError(f"Profile {name} has unsupported container: {container}")
    for key, value in profile.items():
        if key.startswith("bitrate") or key.startswith("adaptive_bitrate"):
            if not isinstance(value, str) or not value.endswith("k"):
                raise ValueError(f"Profile {name} must define {key} as a string like 48k.")
    max_channels = int(profile.get("max_channels", 2))
    if max_channels < 1 or max_channels > 8:
        raise ValueError(f"Profile {name} max_channels must be between 1 and 8.")


def resolve_profile_settings(
    profiles: Dict[str, Dict[str, Any]],
    name: str,
    *,
    allowed_codecs: Iterable[str],
    allowed_containers: Iterable[str],
) -> Dict[str, Any]:
    profile = get_profile(profiles, name)
    validate_profile_definition(
        name,
        profile,
        allowed_codecs=allowed_codecs,
        allowed_containers=allowed_containers,
    )
    return profile
