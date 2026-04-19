from __future__ import annotations

import hashlib
import json
import logging
import math
import os
import shutil
import struct
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from pressor.core.audio_probe import AudioInfo, AudioPreview, AudioProbeError, assess_input_lossiness, probe_audio_file, read_preview_window
from pressor.core.routing import RouteRule, resolve_profile_from_route, validate_strict_routing
from pressor.core.profiles import resolve_profile_settings, validate_profile_definition
from pressor.core.classifier import ProfileDecision, classify_audio_preview
from pressor.core.perceptual import PerceptualEncodeDecision, recommend_encode_plan
from pressor.core.planner import build_encode_plan
from pressor.core.reports import write_encode_report as core_write_encode_report, build_run_summary as core_build_run_summary
from pressor.core.errors import infer_error_details
from pressor.core.encoder import (
    CoreEncoderError,
    FFmpegLocator as CoreFFmpegLocator,
    build_compare_paths as core_build_compare_paths,
    build_ffmpeg_command as core_build_ffmpeg_command,
    build_wwise_prep_command as core_build_wwise_prep_command,
    create_compare_pair as core_create_compare_pair,
)

ALLOWED_INPUT_EXTENSIONS = {
    ".wav", ".mp3", ".flac", ".ogg", ".opus", ".m4a", ".aac", ".aif", ".aiff", ".wma"
}
ALLOWED_CODECS = {"libopus", "aac"}
ALLOWED_CONTAINERS = {".opus", ".ogg", ".m4a", ".aac"}
LOGGER = logging.getLogger("pressor")


class EncoderError(Exception):
    pass


@dataclass
class JobPlanItem:
    source: str
    relative_path: str
    profile: str
    destination: str
    input_sha256: str
    source_size: int
    profile_source: str = "default"
    profile_confidence: int = 100
    profile_reasons: Optional[List[str]] = None


@dataclass
class JobResult:
    source: Path
    destination: Optional[Path]
    profile: str
    success: bool
    changed: bool
    original_size: int
    output_size: int
    message: str
    profile_source: str = "default"
    profile_confidence: int = 100
    profile_reasons: Optional[List[str]] = None
    perceptual_risk: str = "n/a"
    perceptual_score: int = 0
    applied_bitrate: str = ""
    applied_sample_rate: int = 0
    applied_channels: int = 0
    input_is_lossy: bool = False
    input_lossy_reason: str = ""
    stage: str = "complete"
    error_code: str = ""
    error_category: str = ""
    likely_cause: str = ""
    suggested_action: str = ""
    ffmpeg_exit_code: int = 0
    stderr_tail: str = ""
    command: str = ""

    @property
    def bytes_saved(self) -> int:
        if not self.changed:
            return 0
        return max(0, self.original_size - self.output_size)


class FFmpegLocator(CoreFFmpegLocator):
    def __init__(self, ffmpeg_path: Optional[str] = None, ffprobe_path: Optional[str] = None) -> None:
        try:
            super().__init__(ffmpeg_path, ffprobe_path)
        except CoreEncoderError as exc:
            raise EncoderError(str(exc)) from exc


class JsonStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = threading.Lock()

    def load(self) -> Any:
        try:
            with self.path.open("r", encoding="utf-8") as handle:
                return json.load(handle)
        except FileNotFoundError as exc:
            raise EncoderError(f"File not found: {self.path}") from exc
        except json.JSONDecodeError as exc:
            raise EncoderError(f"Invalid JSON in {self.path}") from exc

    def save(self, data: Any) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(self.path.suffix + ".tmp")
        with self._lock:
            with temp.open("w", encoding="utf-8") as handle:
                json.dump(data, handle, indent=2)
            temp.replace(self.path)


class ProfileStore(JsonStore):
    def load_profiles(self) -> Dict[str, Dict[str, Any]]:
        data = self.load()
        if not isinstance(data, dict):
            raise EncoderError("pressor.profiles.json must contain a JSON object.")
        for name, profile in data.items():
            self._validate_profile(name, profile)
        return data

    def names(self) -> List[str]:
        return sorted(self.load_profiles().keys())

    def get(self, name: str) -> Dict[str, Any]:
        profiles = self.load_profiles()
        try:
            return resolve_profile_settings(
                profiles,
                name,
                allowed_codecs=ALLOWED_CODECS,
                allowed_containers=ALLOWED_CONTAINERS,
            )
        except ValueError as exc:
            raise EncoderError(str(exc)) from exc

    def save_profiles(self, profiles: Dict[str, Dict[str, Any]]) -> None:
        for name, profile in profiles.items():
            self._validate_profile(name, profile)
        self.save(profiles)

    @staticmethod
    def _validate_profile(name: str, profile: Dict[str, Any]) -> None:
        try:
            validate_profile_definition(
                name,
                profile,
                allowed_codecs=ALLOWED_CODECS,
                allowed_containers=ALLOWED_CONTAINERS,
            )
        except ValueError as exc:
            raise EncoderError(str(exc)) from exc


class RuleStore(JsonStore):
    def load_rules(self) -> List[RouteRule]:
        data = self.load()
        if not isinstance(data, list):
            raise EncoderError("pressor.routing.json must contain a JSON array.")
        rules: List[RouteRule] = []
        for item in data:
            if not isinstance(item, dict) or "pattern" not in item or "profile" not in item:
                raise EncoderError("Each routing rule must contain pattern and profile.")
            rules.append(RouteRule(pattern=str(item["pattern"]), profile=str(item["profile"])))
        return rules

    def save_rules(self, rules: List[RouteRule]) -> None:
        self.save([asdict(rule) for rule in rules])


class AudioBatchEncoder:
    def __init__(self, ffmpeg: FFmpegLocator, profiles: ProfileStore, rules: RuleStore) -> None:
        self.ffmpeg = ffmpeg
        self.profiles = profiles
        self.rules = rules

    @staticmethod
    def _sanitize_relative_path(relative_path: str) -> Path:
        candidate = Path(relative_path)
        if candidate.is_absolute() or '..' in candidate.parts:
            raise EncoderError(f"Unsafe relative path in plan or manifest: {relative_path}")
        return candidate

    @staticmethod
    def _normalize_worker_count(max_workers: int | None) -> int:
        requested = int(max_workers or 1)
        requested = max(1, requested)
        cpu_count = os.cpu_count() or 4
        return min(requested, max(1, cpu_count * 2))

    @staticmethod
    def _ensure_not_nested(parent: Path, child: Path, label: str) -> None:
        parent_resolved = parent.resolve()
        child_resolved = child.resolve()
        try:
            child_resolved.relative_to(parent_resolved)
        except ValueError:
            return
        raise EncoderError(f"{label} must not be inside the input folder: {child_resolved}")

    def probe(self, path: Path) -> AudioInfo:
        try:
            return probe_audio_file(path, self.ffmpeg.ffprobe, self._validate_input_file)
        except AudioProbeError as exc:
            raise EncoderError(str(exc)) from exc

    def preview(self, path: Path, seconds: float = 12.0, sample_rate: int = 16000) -> AudioPreview:
        try:
            return read_preview_window(path, self.ffmpeg.ffmpeg, self.ffmpeg.ffprobe, seconds=seconds, sample_rate=sample_rate, validate_input_file=self._validate_input_file)
        except AudioProbeError as exc:
            raise EncoderError(str(exc)) from exc

    def classify_path(self, path: Path) -> ProfileDecision:
        preview = self.preview(path)
        return classify_audio_preview(preview)

    def choose_perceptual_encode(self, source: Path, profile_name: str, profile: Dict[str, Any], info: AudioInfo, preview: Optional[AudioPreview] = None) -> PerceptualEncodeDecision:
        preview = preview or self.preview(source)
        return recommend_encode_plan(source, profile_name, profile, info, preview)

    def inspect_input_lossiness(self, source: Path, info: Optional[AudioInfo] = None) -> tuple[bool, str]:
        info = info or self.probe(source)
        return assess_input_lossiness(source, info)

    def choose_profile(self, relative_path: Path, default_profile: str, source_path: Optional[Path] = None, auto_profile: bool = False) -> ProfileDecision:
        normalized = relative_path.as_posix()
        rules = self.rules.load_rules()
        known_profiles = set(self.profiles.names())
        matched_rule = resolve_profile_from_route(normalized, rules, known_profiles)
        if matched_rule is not None:
            return ProfileDecision(matched_rule.profile, "routing-rule", 100, [f"matched rule {matched_rule.pattern}"])
        if auto_profile and source_path is not None:
            return self.classify_path(source_path)
        return ProfileDecision(default_profile, "default", 100, ["used default profile"])

    def validate_routing_expectations(self, input_root: Path, default_profile: str, recursive: bool = True, auto_profile: bool = False) -> List[Dict[str, Any]]:
        input_root = input_root.resolve()
        self._validate_directory(input_root, must_exist=True)
        return validate_strict_routing(
            input_root=input_root,
            iter_audio_files=self._iter_audio_files,
            sanitize_relative_path=self._sanitize_relative_path,
            choose_profile=self.choose_profile,
            default_profile=default_profile,
            recursive=recursive,
            auto_profile=auto_profile,
        )

    def build_plan(self, input_root: Path, output_root: Path, default_profile: str, recursive: bool = True, forced_container: Optional[str] = None, auto_profile: bool = False, strict_routing: bool = False) -> List[JobPlanItem]:
        input_root = input_root.resolve()
        output_root = output_root.resolve()
        self._validate_directory(input_root, must_exist=True)
        try:
            return build_encode_plan(
                input_root=input_root,
                output_root=output_root,
                default_profile=default_profile,
                recursive=recursive,
                forced_container=forced_container,
                auto_profile=auto_profile,
                strict_routing=strict_routing,
                iter_audio_files=self._iter_audio_files,
                sanitize_relative_path=self._sanitize_relative_path,
                choose_profile=self.choose_profile,
                get_profile=self.profiles.get,
                sha256=self.sha256,
                ensure_not_nested=self._ensure_not_nested,
                plan_item_factory=JobPlanItem,
            )
        except ValueError as exc:
            message = str(exc)
            if message == "No supported audio files found.":
                raise EncoderError(f"No supported audio files found under {input_root}") from exc
            raise EncoderError(message) from exc

    def save_manifest(self, manifest_path: Path, input_root: Path, output_root: Path, default_profile: str, recursive: bool = True, forced_container: Optional[str] = None, extra: Optional[Dict[str, Any]] = None, auto_profile: bool = False, strict_routing: bool = False) -> Path:
        manifest_path = manifest_path.resolve()
        plan = self.build_plan(input_root, output_root, default_profile, recursive, forced_container=forced_container, auto_profile=auto_profile, strict_routing=strict_routing)
        payload: Dict[str, Any] = {
            "input_root": str(input_root.resolve()),
            "output_root": str(output_root.resolve()),
            "default_profile": default_profile,
            "recursive": recursive,
            "auto_profile": auto_profile,
            "strict_routing": strict_routing,
            "items": [asdict(item) for item in plan],
        }
        if extra:
            payload.update(extra)
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        with manifest_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
        return manifest_path

    def batch_encode(
        self,
        input_root: Path,
        output_root: Path,
        default_profile: str,
        recursive: bool = True,
        overwrite: bool = False,
        dry_run: bool = False,
        max_workers: int = 2,
        skip_if_larger: bool = True,
        use_manifest: Optional[Path] = None,
        compare_output_root: Optional[Path] = None,
        auto_profile: bool = False,
        strict_routing: bool = False,
        skip_lossy_inputs: bool = False,
        fail_on_lossy_inputs: bool = False,
        progress_callback: Optional[Callable[[int, int, JobPlanItem, JobResult], None]] = None,
    ) -> List[JobResult]:
        if use_manifest:
            items = self._load_manifest(use_manifest)
        else:
            items = self.build_plan(input_root, output_root, default_profile, recursive, auto_profile=auto_profile, strict_routing=strict_routing)

        results: List[JobResult] = []
        worker_count = self._normalize_worker_count(max_workers)
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            future_to_item = {
                executor.submit(
                    self._encode_plan_item,
                    item,
                    overwrite,
                    dry_run,
                    skip_if_larger,
                    compare_output_root,
                    skip_lossy_inputs,
                    fail_on_lossy_inputs,
                ): item
                for item in items
            }
            completed = 0
            total = len(items)
            for future in as_completed(future_to_item):
                item = future_to_item[future]
                result = future.result()
                results.append(result)
                completed += 1
                if progress_callback is not None:
                    progress_callback(completed, total, item, result)
        return sorted(results, key=lambda item: str(item.source))

    def prep_for_wwise(
        self,
        input_root: Path,
        output_root: Path,
        default_profile: str,
        recursive: bool = True,
        overwrite: bool = False,
        dry_run: bool = False,
        max_workers: int = 2,
        use_manifest: Optional[Path] = None,
        compare_output_root: Optional[Path] = None,
        prep_settings: Optional[Dict[str, Dict[str, Any]]] = None,
        auto_profile: bool = False,
        strict_routing: bool = False,
        skip_lossy_inputs: bool = False,
        fail_on_lossy_inputs: bool = False,
        progress_callback: Optional[Callable[[int, int, JobPlanItem, JobResult], None]] = None,
    ) -> List[JobResult]:
        settings = prep_settings or {}
        if use_manifest:
            items = self._load_manifest(use_manifest)
        else:
            items = self.build_plan(input_root, output_root, default_profile, recursive, forced_container=".wav", auto_profile=auto_profile, strict_routing=strict_routing)

        results: List[JobResult] = []
        worker_count = self._normalize_worker_count(max_workers)
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            future_to_item = {
                executor.submit(
                    self._prep_wwise_plan_item,
                    item,
                    overwrite,
                    dry_run,
                    compare_output_root,
                    settings,
                    skip_lossy_inputs,
                    fail_on_lossy_inputs,
                ): item
                for item in items
            }
            completed = 0
            total = len(items)
            for future in as_completed(future_to_item):
                item = future_to_item[future]
                result = future.result()
                results.append(result)
                completed += 1
                if progress_callback is not None:
                    progress_callback(completed, total, item, result)
        return sorted(results, key=lambda item: str(item.source))

    def scan(
        self,
        input_root: Path,
        default_profile: str,
        recursive: bool = True,
        auto_profile: bool = False,
    ) -> List[Dict[str, Any]]:
        input_root = input_root.resolve()
        self._validate_directory(input_root, must_exist=True)
        items: List[Dict[str, Any]] = []
        for source in self._iter_audio_files(input_root, recursive):
            rel_path = source.resolve().relative_to(input_root)
            info = self.probe(source)
            decision = self.choose_profile(rel_path, default_profile, source_path=source, auto_profile=auto_profile)
            input_is_lossy, input_lossy_reason = self.inspect_input_lossiness(source, info)
            entry: Dict[str, Any] = {
                "source": str(source),
                "relative_path": rel_path.as_posix(),
                "channels": info.channels,
                "sample_rate": info.sample_rate,
                "duration": round(info.duration, 3),
                "bit_rate": info.bit_rate,
                "codec_name": info.codec_name,
                "format_name": info.format_name,
                "input_is_lossy": input_is_lossy,
                "input_lossy_reason": input_lossy_reason,
                "chosen_profile": decision.profile,
                "profile_source": decision.source,
                "profile_confidence": decision.confidence,
                "profile_reasons": decision.reasons,
            }
            preview = self.preview(source)
            tuning = self.choose_perceptual_encode(source, decision.profile, self.profiles.get(decision.profile), info, preview)
            entry.update({
                "preview_silence_ratio": round(preview.silence_ratio, 3),
                "preview_energy_mean": round(preview.energy_mean, 4),
                "preview_energy_std": round(preview.energy_std, 4),
                "preview_zcr": round(preview.zcr, 4),
                "preview_brightness": round(preview.brightness, 4),
                "preview_transient_density": round(preview.transient_density, 4),
                "perceptual_score": tuning.score,
                "perceptual_risk": tuning.risk,
                "perceptual_recommendation": tuning.recommendation,
                "perceptual_bitrate": tuning.bitrate,
                "perceptual_reasons": tuning.reasons,
            })
            items.append(entry)
        return items

    def _load_manifest(self, manifest_path: Path) -> List[JobPlanItem]:
        with manifest_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        raw_items = payload.get("items", [])
        if not isinstance(raw_items, list):
            raise EncoderError("Manifest items must be an array.")
        known_profiles = set(self.profiles.names())
        items: List[JobPlanItem] = []
        seen_destinations: set[str] = set()
        for index, item in enumerate(raw_items, start=1):
            if not isinstance(item, dict):
                raise EncoderError(f"Manifest item {index} must be an object.")
            required = ["source", "relative_path", "profile", "destination", "input_sha256", "source_size"]
            missing = [key for key in required if key not in item]
            if missing:
                raise EncoderError(f"Manifest item {index} is missing required fields: {', '.join(missing)}")
            if str(item["profile"]) not in known_profiles:
                raise EncoderError(f"Manifest item {index} references unknown profile: {item['profile']}")
            self._sanitize_relative_path(str(item["relative_path"]))
            destination = Path(str(item["destination"]))
            if not destination.suffix:
                raise EncoderError(f"Manifest item {index} destination must include a file extension.")
            destination_key = str(destination).casefold()
            if destination_key in seen_destinations:
                raise EncoderError(f"Manifest contains duplicate destination paths: {destination}")
            seen_destinations.add(destination_key)
            item.setdefault("profile_source", "manifest")
            item.setdefault("profile_confidence", 100)
            item.setdefault("profile_reasons", ["loaded from manifest"])
            items.append(JobPlanItem(**item))
        if not items:
            raise EncoderError("Manifest did not contain any items.")
        return items

    def _iter_audio_files(self, root: Path, recursive: bool) -> Iterable[Path]:
        walker = root.rglob("*") if recursive else root.glob("*")
        for path in walker:
            if path.is_file() and path.suffix.lower() in ALLOWED_INPUT_EXTENSIONS:
                yield path

    @staticmethod
    def _command_text(command: Optional[List[str]]) -> str:
        if not command:
            return ""
        return " ".join(str(part) for part in command)

    def _error_result(
        self,
        source: Path,
        destination: Optional[Path],
        item: JobPlanItem,
        original_size: int,
        message: str,
        *,
        stage: str,
        perceptual_risk: str = "n/a",
        perceptual_score: int = 0,
        applied_bitrate: str = "",
        applied_sample_rate: int = 0,
        applied_channels: int = 0,
        input_is_lossy: bool = False,
        input_lossy_reason: str = "",
        command: Optional[List[str]] = None,
        ffmpeg_exit_code: int = 0,
        stderr: str = "",
    ) -> JobResult:
        details = infer_error_details(stage, message, stderr=stderr, input_is_lossy=input_is_lossy)
        return JobResult(
            source, destination, item.profile, False, False, original_size, 0, message,
            item.profile_source, item.profile_confidence, item.profile_reasons,
            perceptual_risk, perceptual_score, applied_bitrate, applied_sample_rate, applied_channels,
            input_is_lossy, input_lossy_reason, stage, details['error_code'], details['error_category'],
            details['likely_cause'], details['suggested_action'], ffmpeg_exit_code, details['stderr_tail'], self._command_text(command)
        )

    def _encode_plan_item(
        self,
        item: JobPlanItem,
        overwrite: bool,
        dry_run: bool,
        skip_if_larger: bool,
        compare_output_root: Optional[Path],
        skip_lossy_inputs: bool,
        fail_on_lossy_inputs: bool,
    ) -> JobResult:
        source = Path(item.source)
        destination = Path(item.destination)
        original_size = source.stat().st_size if source.exists() else item.source_size
        try:
            if not source.exists():
                return self._error_result(source, None, item, original_size, "Source file not found", stage="probe")
            current_hash = self.sha256(source)
            if current_hash != item.input_sha256:
                return self._error_result(source, None, item, original_size, "Source changed since manifest was generated", stage="plan")
            profile = self.profiles.get(item.profile)
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists() and not overwrite:
                return JobResult(source, destination, item.profile, True, False, original_size, destination.stat().st_size, "Skipped existing", item.profile_source, item.profile_confidence, item.profile_reasons)
            info = self.probe(source)
            input_is_lossy, input_lossy_reason = self.inspect_input_lossiness(source, info)
            if input_is_lossy and fail_on_lossy_inputs:
                return self._error_result(source, None, item, original_size, f"Rejected lossy input: {input_lossy_reason}", stage="probe", input_is_lossy=True, input_lossy_reason=input_lossy_reason)
            if input_is_lossy and skip_lossy_inputs:
                return JobResult(source, None, item.profile, True, False, original_size, original_size, f"Skipped lossy input: {input_lossy_reason}", item.profile_source, item.profile_confidence, item.profile_reasons, input_is_lossy=True, input_lossy_reason=input_lossy_reason)
            cmd, temp_output, tuning = self._build_ffmpeg_command(source, destination, info, item.profile, profile, overwrite)
            if dry_run:
                message = "DRY RUN: " + " ".join(cmd) + f" | Perceptual tuning: {tuning.risk} risk, {tuning.bitrate}, score {tuning.score}"
                if compare_output_root:
                    compare_paths = self._build_compare_paths(compare_output_root, item, destination)
                    message += f" | Compare pair: {compare_paths['original']} | {compare_paths['encoded']}"
                if input_is_lossy:
                    message += f" | Warning: lossy input detected ({input_lossy_reason})"
                return JobResult(source, destination, item.profile, True, False, original_size, 0, message, item.profile_source, item.profile_confidence, item.profile_reasons, tuning.risk, tuning.score, tuning.bitrate, tuning.sample_rate, tuning.channels, input_is_lossy, input_lossy_reason)

            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=3600)
            except subprocess.TimeoutExpired as exc:
                temp_output.unlink(missing_ok=True)
                return self._error_result(source, destination, item, original_size, "ffmpeg timed out", stage="encode", perceptual_risk=tuning.risk, perceptual_score=tuning.score, applied_bitrate=tuning.bitrate, applied_sample_rate=tuning.sample_rate, applied_channels=tuning.channels, input_is_lossy=input_is_lossy, input_lossy_reason=input_lossy_reason, command=cmd)
            if result.returncode != 0:
                temp_output.unlink(missing_ok=True)
                return self._error_result(source, destination, item, original_size, result.stderr.strip() or "ffmpeg failed", stage="encode", perceptual_risk=tuning.risk, perceptual_score=tuning.score, applied_bitrate=tuning.bitrate, applied_sample_rate=tuning.sample_rate, applied_channels=tuning.channels, input_is_lossy=input_is_lossy, input_lossy_reason=input_lossy_reason, command=cmd, ffmpeg_exit_code=result.returncode, stderr=result.stderr)

            if not temp_output.exists():
                return self._error_result(source, destination, item, original_size, "Temp output was not created", stage="verify", perceptual_risk=tuning.risk, perceptual_score=tuning.score, applied_bitrate=tuning.bitrate, applied_sample_rate=tuning.sample_rate, applied_channels=tuning.channels, input_is_lossy=input_is_lossy, input_lossy_reason=input_lossy_reason, command=cmd)

            output_size = temp_output.stat().st_size
            if skip_if_larger and output_size >= original_size:
                temp_output.unlink(missing_ok=True)
                message = f"Skipped because output was not smaller | Perceptual tuning: {tuning.risk} risk, {tuning.bitrate}"
                if input_is_lossy:
                    message += f" | Warning: lossy input detected ({input_lossy_reason})"
                return JobResult(source, None, item.profile, True, False, original_size, original_size, message, item.profile_source, item.profile_confidence, item.profile_reasons, tuning.risk, tuning.score, tuning.bitrate, tuning.sample_rate, tuning.channels, input_is_lossy, input_lossy_reason)

            temp_output.replace(destination)
            message = f"Encoded | Perceptual tuning: {tuning.risk} risk, {tuning.bitrate}, score {tuning.score}"
            if input_is_lossy:
                message += f" | Warning: lossy input detected ({input_lossy_reason})"
            if compare_output_root:
                compare_paths = self._create_compare_pair(compare_output_root, item, source, destination)
                message = f"Encoded | Compare pair: {compare_paths['original']} | {compare_paths['encoded']}"
            return JobResult(source, destination, item.profile, True, True, original_size, output_size, message, item.profile_source, item.profile_confidence, item.profile_reasons, tuning.risk, tuning.score, tuning.bitrate, tuning.sample_rate, tuning.channels, input_is_lossy, input_lossy_reason)
        except Exception as exc:
            LOGGER.exception("Failed to encode %s", source)
            return self._error_result(source, None, item, original_size, str(exc), stage="encode")

    def _prep_wwise_plan_item(
        self,
        item: JobPlanItem,
        overwrite: bool,
        dry_run: bool,
        compare_output_root: Optional[Path],
        prep_settings: Dict[str, Dict[str, Any]],
        skip_lossy_inputs: bool,
        fail_on_lossy_inputs: bool,
    ) -> JobResult:
        source = Path(item.source)
        destination = Path(item.destination)
        original_size = source.stat().st_size if source.exists() else item.source_size
        try:
            if not source.exists():
                return self._error_result(source, None, item, original_size, "Source file not found", stage="probe")
            current_hash = self.sha256(source)
            if current_hash != item.input_sha256:
                return self._error_result(source, None, item, original_size, "Source changed since manifest was generated", stage="plan")
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists() and not overwrite:
                return JobResult(source, destination, item.profile, True, False, original_size, destination.stat().st_size, "Skipped existing", item.profile_source, item.profile_confidence, item.profile_reasons)
            info = self.probe(source)
            input_is_lossy, input_lossy_reason = self.inspect_input_lossiness(source, info)
            if input_is_lossy and fail_on_lossy_inputs:
                return self._error_result(source, None, item, original_size, f"Rejected lossy input: {input_lossy_reason}", stage="probe", input_is_lossy=True, input_lossy_reason=input_lossy_reason)
            if input_is_lossy and skip_lossy_inputs:
                return JobResult(source, None, item.profile, True, False, original_size, original_size, f"Skipped lossy input: {input_lossy_reason}", item.profile_source, item.profile_confidence, item.profile_reasons, input_is_lossy=True, input_lossy_reason=input_lossy_reason)
            settings = prep_settings.get(item.profile, {})
            cmd, temp_output = self._build_wwise_prep_command(source, destination, info, settings, overwrite)
            if dry_run:
                message = "DRY RUN: " + " ".join(cmd)
                if compare_output_root:
                    compare_paths = self._build_compare_paths(compare_output_root, item, destination)
                    message += f" | Compare pair: {compare_paths['original']} | {compare_paths['encoded']}"
                if input_is_lossy:
                    message += f" | Warning: lossy input detected ({input_lossy_reason})"
                return JobResult(source, destination, item.profile, True, False, original_size, 0, message, item.profile_source, item.profile_confidence, item.profile_reasons, input_is_lossy=input_is_lossy, input_lossy_reason=input_lossy_reason)
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=3600)
            except subprocess.TimeoutExpired as exc:
                temp_output.unlink(missing_ok=True)
                return self._error_result(source, destination, item, original_size, "ffmpeg timed out", stage="wwise_prep", input_is_lossy=input_is_lossy, input_lossy_reason=input_lossy_reason, command=cmd)
            if result.returncode != 0:
                temp_output.unlink(missing_ok=True)
                return self._error_result(source, destination, item, original_size, result.stderr.strip() or "ffmpeg failed", stage="wwise_prep", input_is_lossy=input_is_lossy, input_lossy_reason=input_lossy_reason, command=cmd, ffmpeg_exit_code=result.returncode, stderr=result.stderr)
            if not temp_output.exists():
                return self._error_result(source, destination, item, original_size, "Temp output was not created", stage="verify", input_is_lossy=input_is_lossy, input_lossy_reason=input_lossy_reason, command=cmd)
            output_size = temp_output.stat().st_size
            temp_output.replace(destination)
            message = "Prepared for Wwise"
            if input_is_lossy:
                message += f" | Warning: lossy input detected ({input_lossy_reason})"
            if compare_output_root:
                compare_paths = self._create_compare_pair(compare_output_root, item, source, destination)
                message = f"Prepared for Wwise | Compare pair: {compare_paths['original']} | {compare_paths['encoded']}"
            return JobResult(source, destination, item.profile, True, True, original_size, output_size, message, item.profile_source, item.profile_confidence, item.profile_reasons, input_is_lossy=input_is_lossy, input_lossy_reason=input_lossy_reason)
        except Exception as exc:
            LOGGER.exception("Failed to prep for Wwise %s", source)
            return self._error_result(source, None, item, original_size, str(exc), stage="wwise_prep")

    def _build_ffmpeg_command(self, source: Path, destination: Path, info: AudioInfo, profile_name: str, profile: Dict[str, Any], overwrite: bool) -> tuple[List[str], Path, PerceptualEncodeDecision]:
        preview = self.preview(source)
        tuning = self.choose_perceptual_encode(source, profile_name, profile, info, preview)
        cmd, temp_output = core_build_ffmpeg_command(self.ffmpeg.ffmpeg, source, destination, profile, tuning, overwrite)
        return cmd, temp_output, tuning
    def _build_wwise_prep_command(self, source: Path, destination: Path, info: AudioInfo, settings: Dict[str, Any], overwrite: bool) -> tuple[List[str], Path]:
        return core_build_wwise_prep_command(self.ffmpeg.ffmpeg, source, destination, info, settings, overwrite)
    def _build_compare_paths(self, compare_output_root: Path, item: JobPlanItem, encoded_destination: Path) -> Dict[str, Path]:
        return core_build_compare_paths(compare_output_root, item, encoded_destination, self._sanitize_relative_path)
    def _create_compare_pair(self, compare_output_root: Path, item: JobPlanItem, source: Path, encoded_destination: Path) -> Dict[str, Path]:
        return core_create_compare_pair(compare_output_root, item, source, encoded_destination, self._sanitize_relative_path)
    @staticmethod
    def sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def write_csv_report(results: List[JobResult], report_path: Path) -> None:
        core_write_encode_report(results, report_path)

    @staticmethod
    def summarize(results: List[JobResult]) -> str:
        return core_build_run_summary(results)

    @staticmethod
    def _validate_input_file(path: Path) -> None:
        if not path.exists() or not path.is_file():
            raise EncoderError(f"Input file not found: {path}")
        if path.suffix.lower() not in ALLOWED_INPUT_EXTENSIONS:
            raise EncoderError(f"Unsupported input type: {path.suffix}")

    @staticmethod
    def _validate_directory(path: Path, must_exist: bool) -> None:
        if must_exist and not path.exists():
            raise EncoderError(f"Directory not found: {path}")
        if path.exists() and not path.is_dir():
            raise EncoderError(f"Not a directory: {path}")
