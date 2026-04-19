from __future__ import annotations

import fnmatch
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


@dataclass
class RouteRule:
    pattern: str
    profile: str


def iter_rule_patterns(rule: RouteRule) -> List[str]:
    patterns = [rule.pattern]
    if "/" in rule.pattern and not rule.pattern.startswith("**/"):
        patterns.append("**/" + rule.pattern)
    return patterns


def matches_route_rule(normalized_relative_path: str, rule: RouteRule) -> bool:
    for pattern in iter_rule_patterns(rule):
        if fnmatch.fnmatch(normalized_relative_path, pattern):
            return True
        if pattern.startswith("**/") and fnmatch.fnmatch(normalized_relative_path, pattern[3:]):
            return True
    return False


def resolve_profile_from_route(normalized_relative_path: str, rules: List[RouteRule], known_profiles: Set[str]) -> Optional[RouteRule]:
    for rule in rules:
        if rule.profile not in known_profiles:
            continue
        if matches_route_rule(normalized_relative_path, rule):
            return rule
    return None


def validate_strict_routing(
    input_root: Path,
    iter_audio_files: Any,
    sanitize_relative_path: Any,
    choose_profile: Any,
    default_profile: str,
    recursive: bool = True,
    auto_profile: bool = False,
) -> List[Dict[str, Any]]:
    issues: List[Dict[str, Any]] = []
    for source in iter_audio_files(input_root, recursive):
        rel_path = sanitize_relative_path(source.resolve().relative_to(input_root).as_posix())
        decision = choose_profile(rel_path, default_profile, source_path=source, auto_profile=auto_profile)
        if decision.source != "routing-rule":
            issues.append({
                "source": str(source),
                "relative_path": rel_path.as_posix(),
                "chosen_profile": decision.profile,
                "profile_source": decision.source,
                "profile_confidence": decision.confidence,
                "profile_reasons": decision.reasons,
            })
    return issues
