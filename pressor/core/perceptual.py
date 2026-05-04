"""Perceptual tuning helpers for Pressor.

Extracted during the refactor so bitrate and recommendation logic have a
clear home outside the encoder orchestration layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from pressor.core.audio_probe import AudioInfo, AudioPreview


@dataclass
class PerceptualEncodeDecision:
    bitrate: str
    sample_rate: int
    channels: int
    score: int
    risk: str
    recommendation: str
    reasons: List[str]


def _parse_kbps(value: str) -> int:
    return int(str(value).lower().replace("k", "").strip())


def _format_kbps(value: int) -> str:
    return f"{int(value)}k"


def _adaptive_bounds(profile: Dict[str, Any], channels: int) -> tuple[int, int, int]:
    key = "mono" if channels == 1 else "stereo"
    base = _parse_kbps(profile[f"bitrate_{key}"])
    min_key = f"adaptive_bitrate_{key}_min"
    max_key = f"adaptive_bitrate_{key}_max"
    min_value = _parse_kbps(profile.get(min_key, profile[f"bitrate_{key}"]))
    max_value = _parse_kbps(profile.get(max_key, profile[f"bitrate_{key}"]))
    return min(min_value, base), max(max_value, base), base


def compute_perceptual_risk(profile_name: str, info: AudioInfo, preview: AudioPreview) -> tuple[int, str, str, List[str]]:
    score = 0.0
    reasons: List[str] = []

    def push(weight: float, reason: str) -> None:
        nonlocal score
        score += weight
        reasons.append(reason)

    if profile_name == "dialogue":
        push(18, "dialogue profile protects speech clarity by default")
        if preview.silence_ratio >= 0.20:
            push(4, "pause-heavy speech still keeps dialogue-safe floor")
        if 0.03 <= preview.zcr <= 0.12:
            push(8, "speech-like harmonic content needs protection")
        if preview.brightness >= 0.18:
            push(12, "bright consonants need high-frequency protection")
        if preview.transient_density >= 2.6:
            push(10, "sharp plosives/transients present")
        if info.channels > 1:
            push(6, "multichannel source preserved conservatively")
    elif profile_name == "ambient":
        if preview.zcr > 0.18 and preview.energy_std < 0.04:
            push(-6, "steady broadband bed compresses efficiently")
        if preview.brightness >= 0.24:
            push(8, "airy upper detail present")
        if preview.transient_density >= 2.8:
            push(6, "transient ambience benefits from headroom")
        if preview.energy_std >= 0.08:
            push(6, "dynamic ambience needs safer bitrate")
    elif profile_name == "music":
        push(12, "music defaults to conservative perceptual treatment")
        if info.channels > 1:
            push(8, "stereo image should remain transparent")
        if preview.brightness >= 0.18:
            push(14, "high-frequency detail can reveal artifacts")
        if preview.transient_density >= 2.4:
            push(10, "transients can expose lossy smearing")
        if preview.energy_std >= 0.06:
            push(8, "dynamic passages need extra headroom")
        if preview.zcr < 0.08 and preview.brightness < 0.10 and preview.energy_std < 0.03:
            push(-8, "simple tonal structure can stay near baseline")
    elif profile_name == "sfx":
        push(8, "sfx keeps attack detail conservative by default")
        if preview.transient_density >= 2.6:
            push(16, "sharp attacks can reveal smearing")
        elif preview.transient_density >= 2.2:
            push(8, "noticeable transient content")
        if preview.brightness >= 0.20:
            push(10, "bright edge detail can reveal artifacts")
        if preview.duration <= 3.0:
            push(4, "short one-shot detail should stay crisp")
        if info.channels > 1:
            push(4, "stereo impact should remain stable")
    else:
        if preview.brightness >= 0.20:
            push(8, "bright content needs safer bitrate")
        if preview.transient_density >= 2.5:
            push(8, "transient density needs safer bitrate")

    normalized_score = max(0, min(100, int(50 + score)))
    if normalized_score >= 72:
        return normalized_score, "high", "safe", reasons
    if normalized_score >= 58:
        return normalized_score, "medium", "balanced", reasons
    return normalized_score, "low", "aggressive", reasons


def recommend_bitrate(profile_name: str, profile: Dict[str, Any], info: AudioInfo, preview: AudioPreview) -> tuple[str, int, int]:
    channels = max(1, min(int(profile.get("max_channels", info.channels)), info.channels))
    sample_rate = int(profile.get("sample_rate") or info.sample_rate)
    min_k, max_k, base_k = _adaptive_bounds(profile, channels)
    score, _risk, recommendation, _reasons = compute_perceptual_risk(profile_name, info, preview)

    if recommendation == "safe":
        chosen_k = max_k
    elif recommendation == "balanced":
        chosen_k = min(max_k, max(base_k, int(round((base_k + max_k) / 2))))
    else:
        chosen_k = max(min_k, base_k if profile_name == "music" else int(round((min_k + base_k) / 2)))

    if profile_name == "dialogue":
        # Dialogue is intentionally protected from aggressive speech-style compression.
        # Low complexity, silence, or speech-like detection must never push voice content
        # below the player-transparent floor established for game dialogue.
        chosen_k = max(chosen_k, 160)
        sample_rate = max(sample_rate, 48000)

    return _format_kbps(chosen_k), sample_rate, channels


def recommend_encode_plan(source: Path, profile_name: str, profile: Dict[str, Any], info: AudioInfo, preview: AudioPreview) -> PerceptualEncodeDecision:
    score, risk, recommendation, reasons = compute_perceptual_risk(profile_name, info, preview)
    bitrate, sample_rate, channels = recommend_bitrate(profile_name, profile, info, preview)
    top_reasons = reasons[:4] if reasons else ["baseline profile tuning"]
    top_reasons.append(f"complexity={score}")
    return PerceptualEncodeDecision(
        bitrate=bitrate,
        sample_rate=sample_rate,
        channels=channels,
        score=score,
        risk=risk,
        recommendation=recommendation,
        reasons=top_reasons,
    )
