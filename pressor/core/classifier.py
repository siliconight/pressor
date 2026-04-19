"""Preview-based audio classification helpers.

This module is introduced in Phase 8 of the refactor to isolate auto-profile
heuristics from the encoder orchestration without changing behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from pressor.core.audio_probe import AudioPreview


@dataclass
class ProfileDecision:
    profile: str
    source: str
    confidence: int
    reasons: List[str]


def classify_audio_preview(preview: AudioPreview) -> ProfileDecision:
    scores: Dict[str, float] = {"dialogue": 0.0, "ambient": 0.0, "music": 0.0, "sfx": 0.0}
    reasons: Dict[str, List[str]] = {"dialogue": [], "ambient": [], "music": [], "sfx": []}

    def add(profile: str, score: float, reason: str) -> None:
        scores[profile] += score
        reasons[profile].append(reason)

    if preview.channels == 1:
        add("dialogue", 1.5, "mono source")
        add("ambient", 0.6, "mono-compatible")
    else:
        add("music", 3.0, "stereo or multichannel source")
        add("ambient", 1.0, "stereo bed possible")

    if preview.duration <= 12.0:
        add("dialogue", 2.0, "short duration")
    elif preview.duration >= 45.0:
        add("music", 2.2, "long-form content")
        add("ambient", 1.8, "loop-like duration")
    elif preview.duration >= 20.0:
        add("music", 1.4, "extended content")
        add("ambient", 1.2, "bed-like duration")
    else:
        add("ambient", 0.6, "medium duration")

    if preview.silence_ratio >= 0.18:
        add("dialogue", 3.2, "pause-heavy preview")
    elif preview.silence_ratio <= 0.04:
        add("music", 1.8, "continuous energy")
        add("ambient", 1.2, "continuous bed")
    else:
        add("ambient", 0.8, "some gaps but mostly continuous")

    if preview.energy_std >= 0.12:
        add("dialogue", 1.0, "bursty loudness changes")
        add("music", 0.7, "dynamic variation")
    elif preview.energy_std <= 0.05:
        add("ambient", 2.0, "steady loudness")
        add("music", 0.8, "stable music bed")

    if preview.brightness >= 0.32:
        add("music", 1.5, "bright high-frequency content")
    elif preview.brightness <= 0.10:
        add("music", 1.2, "tonal low-brightness content")
        add("ambient", 1.0, "soft spectral profile")
        add("dialogue", 0.4, "speech-like upper band")
    elif preview.brightness <= 0.18:
        add("ambient", 1.5, "soft spectral profile")
        add("dialogue", 0.5, "speech-like upper band")

    if 0.03 <= preview.zcr <= 0.12:
        add("dialogue", 0.8, "speech-like zero crossing rate")
        add("music", 1.0, "harmonic texture")
    if preview.channels == 1 and preview.duration <= 8.0 and preview.brightness < 0.12 and preview.zcr < 0.08:
        add("dialogue", 2.4, "mono speech-like texture")
    if preview.channels == 1 and preview.silence_ratio < 0.10 and preview.energy_std >= 0.08 and preview.transient_density < 2.0:
        add("dialogue", 1.4, "speech cadence without long decay")
    elif preview.zcr > 0.20:
        add("ambient", 3.0, "noise-like texture")
    elif preview.zcr > 0.14:
        add("ambient", 1.0, "noise-like texture")
        add("music", 0.6, "dense upper detail")

    if preview.zcr > 0.20 and preview.brightness > 0.70 and preview.energy_std < 0.03:
        add("ambient", 2.5, "steady broadband noise")
    if preview.zcr < 0.08 and preview.brightness < 0.08 and preview.silence_ratio < 0.04 and preview.energy_std < 0.02:
        add("music", 2.5, "steady tonal structure")

    if preview.duration <= 6.0:
        add("sfx", 1.2, "short one-shot duration")
    elif preview.duration <= 12.0:
        add("sfx", 1.0, "brief event-like duration")
    if preview.channels > 1 and preview.duration <= 4.0:
        add("sfx", 2.8, "short stereo event")
    if preview.transient_density >= 2.8:
        add("sfx", 3.2, "strong transient spikes")
    elif preview.transient_density >= 2.2:
        add("sfx", 1.6, "noticeable transient content")
    if preview.brightness >= 0.22:
        add("sfx", 1.4, "bright attack content")
    if preview.energy_std >= 0.10:
        add("sfx", 2.0, "bursty dynamics")
    if 0.15 <= preview.silence_ratio <= 0.75 and preview.duration <= 4.0 and preview.energy_std >= 0.08:
        add("sfx", 2.0, "event body surrounded by decay or silence")
    if preview.silence_ratio <= 0.08 and preview.duration <= 8.0 and preview.transient_density >= 2.4:
        add("sfx", 1.6, "compact high-impact event")

    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    winner, winner_score = ranked[0]
    runner_score = ranked[1][1] if len(ranked) > 1 else 0.0
    margin = max(0.0, winner_score - runner_score)
    confidence = max(35, min(98, int(55 + margin * 12)))
    winner_reasons = reasons[winner][:4]
    winner_reasons.extend([
        f"silence={preview.silence_ratio:.2f}",
        f"brightness={preview.brightness:.2f}",
        f"zcr={preview.zcr:.2f}",
    ])
    return ProfileDecision(
        profile=winner,
        source="auto-preview",
        confidence=confidence,
        reasons=winner_reasons,
    )
