from __future__ import annotations

from pathlib import Path
from typing import Any

from pressor.core.paths import normalize_path, validate_path_relationships


def normalize_review_pack_path(path: str | None) -> Path | None:
    return normalize_path(path)


def validate_review_pack_relationships(input_root: Path | None, output_root: Path | None, review_pack_root: Path | None) -> None:
    validate_path_relationships(input_root, output_root, review_pack_root)


def review_pack_enabled(root: Path | None) -> bool:
    return root is not None
