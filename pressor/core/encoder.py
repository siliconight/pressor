from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional


class CoreEncoderError(Exception):
    pass


class FFmpegLocator:
    def __init__(self, ffmpeg_path: Optional[str] = None, ffprobe_path: Optional[str] = None) -> None:
        self.ffmpeg = self._resolve_binary(ffmpeg_path or "ffmpeg")
        self.ffprobe = self._resolve_binary(ffprobe_path or "ffprobe")

    @staticmethod
    def _resolve_binary(name_or_path: str) -> str:
        candidate = shutil.which(name_or_path)
        if candidate:
            return candidate
        path = Path(name_or_path)
        if path.exists() and os.access(path, os.X_OK):
            return str(path.resolve())
        raise CoreEncoderError(f"Could not find executable: {name_or_path}")


def build_ffmpeg_command(
    ffmpeg_binary: str,
    source: Path,
    destination: Path,
    profile: Dict[str, Any],
    tuning: Any,
    overwrite: bool,
) -> tuple[list[str], Path]:
    codec = profile["codec"]
    channels = tuning.channels
    bitrate = tuning.bitrate
    sample_rate = tuning.sample_rate
    temp_output = destination.with_name(destination.stem + ".part" + destination.suffix)

    cmd = [
        ffmpeg_binary,
        "-hide_banner",
        "-loglevel", "error",
        "-nostdin",
        "-y" if overwrite else "-n",
        "-i", str(source),
        "-map_metadata", "0",
        "-vn",
        "-c:a", codec,
        "-ac", str(channels),
        "-ar", str(sample_rate),
        "-b:a", bitrate,
    ]
    if codec == "libopus":
        cmd.extend([
            "-application", str(profile.get("application", "audio")),
            "-vbr", str(profile.get("vbr", "on")),
            "-compression_level", str(profile.get("compression_level", 10)),
            "-frame_duration", str(profile.get("frame_duration", 20)),
        ])
    elif codec == "aac":
        cmd.extend(["-movflags", "+faststart"])
    cmd.append(str(temp_output))
    return cmd, temp_output


def build_wwise_prep_command(
    ffmpeg_binary: str,
    source: Path,
    destination: Path,
    info: Any,
    settings: Dict[str, Any],
    overwrite: bool,
) -> tuple[list[str], Path]:
    desired_channels = int(settings.get("channels", info.channels))
    channels = max(1, min(desired_channels, info.channels))
    sample_rate = int(settings.get("sample_rate") or info.sample_rate)
    pcm_codec = str(settings.get("pcm_codec", "pcm_s16le"))
    temp_output = destination.with_name(destination.stem + ".part" + destination.suffix)
    cmd = [
        ffmpeg_binary,
        "-hide_banner",
        "-loglevel", "error",
        "-nostdin",
        "-y" if overwrite else "-n",
        "-i", str(source),
        "-map_metadata", "0",
        "-vn",
        "-c:a", pcm_codec,
        "-ac", str(channels),
        "-ar", str(sample_rate),
        str(temp_output),
    ]
    return cmd, temp_output


def build_compare_paths(compare_output_root: Path, item: Any, encoded_destination: Path, sanitize_relative_path) -> Dict[str, Path]:
    compare_root = compare_output_root.resolve() / item.profile
    relative = sanitize_relative_path(item.relative_path)
    base_dir = compare_root / relative.parent
    original_target = base_dir / f"{relative.stem}_original{Path(item.source).suffix.lower()}"
    encoded_target = base_dir / f"{relative.stem}_encoded{encoded_destination.suffix.lower()}"
    return {"original": original_target, "encoded": encoded_target}


def create_compare_pair(compare_output_root: Path, item: Any, source: Path, encoded_destination: Path, sanitize_relative_path) -> Dict[str, Path]:
    paths = build_compare_paths(compare_output_root, item, encoded_destination, sanitize_relative_path)
    paths["original"].parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, paths["original"])
    shutil.copy2(encoded_destination, paths["encoded"])
    return paths
