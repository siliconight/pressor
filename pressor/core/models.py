"""Core data models for Pressor.

These models are introduced in Phase 2 of the refactor to make the codebase's
main concepts explicit without changing runtime behavior yet.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class AudioFileInfo:
    """Basic discovered metadata for a source audio file."""

    source_path: Path
    relative_path: Path
    codec_name: Optional[str] = None
    channels: Optional[int] = None
    sample_rate: Optional[int] = None
    duration_seconds: Optional[float] = None
    bitrate: Optional[int] = None


@dataclass(frozen=True)
class ScanResult:
    """Result of scanning or classifying an audio file."""

    source_path: Path
    relative_path: Path
    chosen_profile: str
    profile_source: str
    confidence: Optional[float] = None
    reason: str = ""
    channels: Optional[int] = None
    sample_rate: Optional[int] = None
    duration_seconds: Optional[float] = None
    perceptual_risk: Optional[str] = None
    perceptual_score: Optional[float] = None
    perceptual_bitrate: Optional[str] = None
    encode_plan: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ProfileDecision:
    """Resolved profile choice for a file before planning the encode."""

    profile_name: str
    source: str
    confidence: Optional[float] = None
    reason: str = ""
    encode_plan: Optional[str] = None
    perceptual_risk: Optional[str] = None
    perceptual_score: Optional[float] = None
    recommended_bitrate: Optional[str] = None


@dataclass(frozen=True)
class EncodePlanItem:
    """A single planned encode operation."""

    source_path: Path
    relative_path: Path
    destination_path: Path
    profile_name: str
    profile_source: str
    codec_name: Optional[str] = None
    output_extension: Optional[str] = None
    review_pack_path: Optional[Path] = None
    expected_channels: Optional[int] = None
    expected_sample_rate: Optional[int] = None
    perceptual_risk: Optional[str] = None
    perceptual_score: Optional[float] = None
    selected_bitrate: Optional[str] = None
    encode_plan: Optional[str] = None
    reason: str = ""
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EncodeResult:
    """Outcome of processing one file."""

    source_path: Path
    destination_path: Path
    profile_name: str
    status: str
    changed: bool
    profile_source: str = ""
    original_bytes: int = 0
    output_bytes: int = 0
    bytes_saved: int = 0
    error: Optional[str] = None
    perceptual_risk: Optional[str] = None
    selected_bitrate: Optional[str] = None
    verify_notes: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class FailureRecord:
    """Structured failure information for reports and diagnostics."""

    source_path: Path
    destination_path: Optional[Path]
    profile_name: str
    profile_source: str
    message: str
    stage: str = "encode"
    perceptual_risk: Optional[str] = None
    selected_bitrate: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DoctorResult:
    """One doctor check result."""

    status: str
    name: str
    message: str
