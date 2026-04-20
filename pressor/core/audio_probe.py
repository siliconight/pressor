from __future__ import annotations

import json
import math
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from pressor.core.subprocess_utils import DEFAULT_FFMPEG_TIMEOUT, DEFAULT_FFPROBE_TIMEOUT, run_external

LOSSLESS_CODECS = {"pcm_s16le", "pcm_s24le", "pcm_s32le", "flac", "alac", "ape", "wavpack"}
LOSSY_CODECS = {"mp3", "aac", "opus", "vorbis", "libvorbis", "wmav1", "wmav2", "ac3", "eac3"}
COMMONLY_LOSSY_EXTENSIONS = {".mp3", ".m4a", ".aac", ".opus", ".ogg", ".wma"}


class AudioProbeError(Exception):
    pass


@dataclass
class AudioInfo:
    path: Path
    channels: int
    sample_rate: int
    duration: float
    bit_rate: Optional[int]
    codec_name: Optional[str] = None
    format_name: Optional[str] = None


@dataclass
class AudioPreview:
    channels: int
    sample_rate: int
    duration: float
    silence_ratio: float
    energy_mean: float
    energy_std: float
    zcr: float
    brightness: float
    transient_density: float


def probe_audio_file(path: Path, ffprobe_bin: str, validate_input_file: Callable[[Path], None] | None = None) -> AudioInfo:
    if validate_input_file is not None:
        validate_input_file(path)
    cmd = [
        ffprobe_bin,
        '-v', 'error',
        '-show_streams',
        '-show_format',
        '-of', 'json',
        str(path),
    ]
    try:
        result = run_external(cmd, timeout=DEFAULT_FFPROBE_TIMEOUT, text=True)
    except subprocess.TimeoutExpired as exc:
        raise AudioProbeError(f'ffprobe timed out for {path}') from exc
    if result.returncode != 0:
        raise AudioProbeError(f'ffprobe failed for {path}: {result.stderr.strip()}')
    payload = json.loads(result.stdout)
    streams = payload.get('streams', [])
    audio_stream = next((stream for stream in streams if stream.get('codec_type') == 'audio'), None)
    if not audio_stream:
        raise AudioProbeError(f'No audio stream found in {path}')
    fmt = payload.get('format', {})
    return AudioInfo(
        path=path,
        channels=int(audio_stream.get('channels') or 1),
        sample_rate=int(audio_stream.get('sample_rate') or 48000),
        duration=float(fmt.get('duration') or 0.0),
        bit_rate=int(fmt.get('bit_rate')) if fmt.get('bit_rate') else None,
        codec_name=audio_stream.get('codec_name'),
        format_name=fmt.get('format_name'),
    )


def read_duration_seconds(path: Path, ffprobe_bin: str, validate_input_file: Callable[[Path], None] | None = None) -> float:
    return probe_audio_file(path, ffprobe_bin, validate_input_file).duration


def read_preview_window(path: Path, ffmpeg_bin: str, ffprobe_bin: str, seconds: float = 12.0, sample_rate: int = 16000, validate_input_file: Callable[[Path], None] | None = None) -> AudioPreview:
    info = probe_audio_file(path, ffprobe_bin, validate_input_file)
    preview_duration = max(0.0, min(seconds, info.duration if info.duration > 0 else seconds))
    start_offset = 0.0
    if info.duration > preview_duration:
        start_offset = max(0.0, (info.duration - preview_duration) / 2.0)
    cmd = [ffmpeg_bin, '-hide_banner', '-loglevel', 'error', '-nostdin']
    if start_offset > 0.0:
        cmd.extend(['-ss', f'{start_offset:.3f}'])
    cmd.extend([
        '-t', f'{preview_duration:.3f}',
        '-i', str(path),
        '-vn',
        '-ac', '1',
        '-ar', str(sample_rate),
        '-f', 's16le',
        '-',
    ])
    try:
        result = run_external(cmd, timeout=DEFAULT_FFMPEG_TIMEOUT, text=False)
    except subprocess.TimeoutExpired as exc:
        raise AudioProbeError(f'Preview decode timed out for {path}') from exc
    if result.returncode != 0:
        stderr = result.stderr.decode('utf-8', errors='ignore').strip()
        raise AudioProbeError(f'Preview decode failed for {path}: {stderr}')
    raw = result.stdout
    if len(raw) < 4:
        raise AudioProbeError(f'Preview decode produced no audio samples for {path}')
    sample_count = len(raw) // 2
    samples = struct.unpack('<' + 'h' * sample_count, raw[: sample_count * 2])
    normalized = [abs(sample) / 32768.0 for sample in samples]
    silence_threshold = 0.01
    silence_ratio = sum(1 for value in normalized if value < silence_threshold) / max(1, len(normalized))

    frame_size = max(1, int(sample_rate * 0.02))
    frame_rms: list[float] = []
    zcr_values: list[float] = []
    brightness_values: list[float] = []
    transient_values: list[float] = []
    for start in range(0, len(samples), frame_size):
        frame = samples[start:start + frame_size]
        if len(frame) < 8:
            continue
        float_frame = [sample / 32768.0 for sample in frame]
        rms = math.sqrt(sum(value * value for value in float_frame) / len(float_frame))
        frame_rms.append(rms)
        zc = 0
        prev = float_frame[0]
        for value in float_frame[1:]:
            if (prev < 0 <= value) or (prev > 0 >= value):
                zc += 1
            prev = value
        zcr_values.append(zc / max(1, len(float_frame) - 1))
        diff_energy = sum((float_frame[i] - float_frame[i - 1]) ** 2 for i in range(1, len(float_frame)))
        total_energy = sum(value * value for value in float_frame) + 1e-9
        brightness_values.append(min(1.0, diff_energy / total_energy))
        peak = max(abs(value) for value in float_frame)
        transient_values.append(peak / (rms + 1e-6))

    energy_mean = sum(frame_rms) / max(1, len(frame_rms))
    energy_std = math.sqrt(sum((value - energy_mean) ** 2 for value in frame_rms) / max(1, len(frame_rms))) if frame_rms else 0.0
    zcr = sum(zcr_values) / max(1, len(zcr_values))
    brightness = sum(brightness_values) / max(1, len(brightness_values))
    transient_density = sum(transient_values) / max(1, len(transient_values))
    return AudioPreview(
        channels=info.channels,
        sample_rate=info.sample_rate,
        duration=info.duration,
        silence_ratio=silence_ratio,
        energy_mean=energy_mean,
        energy_std=energy_std,
        zcr=zcr,
        brightness=brightness,
        transient_density=transient_density,
    )


def is_decodable(path: Path, ffmpeg_bin: str, validate_input_file: Callable[[Path], None] | None = None) -> bool:
    if validate_input_file is not None:
        validate_input_file(path)
    cmd = [
        ffmpeg_bin,
        '-hide_banner',
        '-loglevel', 'error',
        '-nostdin',
        '-i', str(path),
        '-vn',
        '-f', 'null',
        '-',
    ]
    try:
        result = run_external(cmd, timeout=DEFAULT_FFPROBE_TIMEOUT, text=False)
    except subprocess.TimeoutExpired:
        return False
    return result.returncode == 0



def assess_input_lossiness(path: Path, info: Optional[AudioInfo] = None) -> tuple[bool, str]:
    ext = path.suffix.lower()
    codec_name = (getattr(info, "codec_name", None) or "").lower()
    if codec_name:
        if codec_name in LOSSLESS_CODECS:
            return False, f"codec {codec_name} is lossless"
        if codec_name in LOSSY_CODECS:
            return True, f"codec {codec_name} is lossy"
        return False, f"codec {codec_name} is not classified as lossy"
    if ext in COMMONLY_LOSSY_EXTENSIONS:
        return True, f"extension {ext} commonly indicates lossy audio"
    return False, ""
