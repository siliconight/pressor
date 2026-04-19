from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Sequence
import re

from encoder import ALLOWED_INPUT_EXTENSIONS, EncoderError


@dataclass(frozen=True)
class RunWorkspace:
    run_id: str
    run_label: str
    run_root: Path
    encoded_root: Path
    review_root: Path
    reports_root: Path


def normalize_path(path: str | Path | None) -> Path | None:
    if path is None:
        return None
    return Path(path).expanduser()


def default_output_root_for_manifest_build(input_root: Path) -> Path:
    resolved = input_root.resolve()
    return resolved.parent / f"{resolved.name}_pressed"


def sanitize_run_label(label: str | None) -> str:
    if not label:
        return ""
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", label.strip())
    cleaned = cleaned.strip("-._")
    return cleaned[:80]


def create_run_workspace(output_root: Path, run_label: str | None = None, flat_output: bool = False) -> RunWorkspace:
    output_root = output_root.resolve()
    if flat_output:
        output_root.mkdir(parents=True, exist_ok=True)
        return RunWorkspace(
            run_id="flat",
            run_label=sanitize_run_label(run_label),
            run_root=output_root,
            encoded_root=output_root,
            review_root=output_root / "review",
            reports_root=output_root / "reports",
        )

    output_root.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    cleaned_label = sanitize_run_label(run_label)
    folder_name = f"{timestamp}_{cleaned_label}" if cleaned_label else timestamp
    run_root = output_root / folder_name
    counter = 2
    while run_root.exists():
        run_root = output_root / f"{folder_name}_{counter}"
        counter += 1
    encoded_root = run_root / "encoded"
    review_root = run_root / "review"
    reports_root = run_root / "reports"
    encoded_root.mkdir(parents=True, exist_ok=True)
    reports_root.mkdir(parents=True, exist_ok=True)
    return RunWorkspace(
        run_id=run_root.name,
        run_label=cleaned_label,
        run_root=run_root,
        encoded_root=encoded_root,
        review_root=review_root,
        reports_root=reports_root,
    )


def find_supported_audio_files(
    root: Path,
    recursive: bool = True,
    allowed_extensions: Sequence[str] | None = None,
) -> list[Path]:
    allowed = {ext.lower() for ext in (allowed_extensions or tuple(ALLOWED_INPUT_EXTENSIONS))}
    walker: Iterable[Path] = root.rglob("*") if recursive else root.glob("*")
    return sorted(path for path in walker if path.is_file() and path.suffix.lower() in allowed)


def relative_audio_path(input_root: Path, source_path: Path) -> Path:
    return source_path.resolve().relative_to(input_root.resolve())


def build_output_path(
    input_root: Path,
    output_root: Path,
    source_path: Path,
    container_suffix: str | None = None,
) -> Path:
    relative_path = relative_audio_path(input_root, source_path)
    destination = output_root / relative_path
    return destination.with_suffix(container_suffix) if container_suffix else destination


def build_review_pack_path(review_pack_root: Path, relative_path: Path, suffix: str | None = None) -> Path:
    destination = review_pack_root / relative_path
    return destination.with_suffix(suffix) if suffix else destination


def validate_path_relationships(input_root: Path | None, output_root: Path | None, review_pack_root: Path | None) -> None:
    if input_root is None:
        return
    input_resolved = input_root.resolve()
    for label, candidate in (("Output folder", output_root), ("Review pack", review_pack_root)):
        if candidate is None:
            continue
        candidate_resolved = candidate.resolve()
        try:
            candidate_resolved.relative_to(input_resolved)
        except ValueError:
            continue
        raise EncoderError(f"{label} must not be inside the input folder: {candidate_resolved}")
