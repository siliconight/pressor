from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

from encoder import EncoderError, ProfileStore, RouteRule, RuleStore


def get_app_dir() -> Path:
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))


def get_profile_file(app_dir: Path | None = None) -> Path:
    root = app_dir or get_app_dir()
    return root / "pressor.profiles.json"


def get_rule_file(app_dir: Path | None = None) -> Path:
    root = app_dir or get_app_dir()
    return root / "pressor.routing.json"


def get_wwise_file(app_dir: Path | None = None) -> Path:
    root = app_dir or get_app_dir()
    return root / "pressor.wwise.json"


def load_profiles_config(path: Path | None = None) -> Dict[str, Dict[str, Any]]:
    return ProfileStore(path or get_profile_file()).load_profiles()


def load_routing_config(path: Path | None = None) -> List[RouteRule]:
    return RuleStore(path or get_rule_file()).load_rules()


def load_wwise_config(path: Path | None = None) -> Dict[str, Dict[str, Any]]:
    config_path = path or get_wwise_file()
    try:
        with config_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError as exc:
        raise EncoderError(f"File not found: {config_path}") from exc
    except json.JSONDecodeError as exc:
        raise EncoderError(f"Invalid JSON in {config_path}") from exc
    if not isinstance(data, dict):
        raise EncoderError("pressor.wwise.json must contain a JSON object.")
    return data


def validate_config_bundle(
    profiles: Dict[str, Dict[str, Any]],
    rules: List[RouteRule],
    default_profile: str | None = None,
) -> List[str]:
    issues: List[str] = []
    unknown = sorted({rule.profile for rule in rules if rule.profile not in profiles})
    if unknown:
        issues.append(f"Routing rules reference unknown profile(s): {', '.join(unknown)}")
    if default_profile and default_profile not in profiles:
        issues.append(f"Fallback profile '{default_profile}' was not found in pressor.profiles.json.")
    return issues
