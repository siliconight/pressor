from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List, Callable

from encoder import ALLOWED_INPUT_EXTENSIONS, AudioBatchEncoder, EncoderError, FFmpegLocator, ProfileStore, RuleStore
from pressor.core.audio_probe import assess_input_lossiness
from pressor.core.config import load_profiles_config, load_routing_config, load_wwise_config, validate_config_bundle
from pressor.core.paths import find_supported_audio_files, normalize_path, validate_path_relationships


def run_doctor(
    args,
    profile_file: Path,
    rule_file: Path,
    wwise_file: Path,
    make_tool_version: Callable[[str, str], str],
    validate_wwise_safe_settings: Callable[[Dict[str, Dict[str, object]]], None],
) -> int:
    checks: List[Dict[str, str]] = []
    failures = 0
    warnings = 0

    def add(name: str, ok: bool, detail: str, warn: bool = False) -> None:
        nonlocal failures, warnings
        if ok:
            level = "WARN" if warn else "PASS"
            if warn:
                warnings += 1
        else:
            level = "FAIL"
            failures += 1
        checks.append({"name": name, "level": level, "detail": detail})

    add("python", sys.version_info >= (3, 10), f"Python {sys.version.split()[0]}")

    locator: FFmpegLocator | None = None
    try:
        locator = FFmpegLocator(args.ffmpeg, args.ffprobe)
        add("ffmpeg", True, f"Found at {locator.ffmpeg}; {make_tool_version(locator.ffmpeg, '-version')}")
        add("ffprobe", True, f"Found at {locator.ffprobe}; {make_tool_version(locator.ffprobe, '-version')}")
    except EncoderError as exc:
        detail = str(exc) + " Install FFmpeg, make sure both ffmpeg and ffprobe are on PATH, then run python pressor.py --doctor. On Windows, setup.bat can help prepare the machine."
        add("ffmpeg/ffprobe", False, detail)

    try:
        profiles = load_profiles_config(profile_file)
        add("pressor.profiles.json", True, f"Loaded {len(profiles)} profile(s): {', '.join(sorted(profiles.keys()))}")
    except EncoderError as exc:
        profiles = {}
        add("pressor.profiles.json", False, str(exc))

    try:
        rules = load_routing_config(rule_file)
        config_issues = validate_config_bundle(profiles, rules, args.profile)
        routing_issues = [issue for issue in config_issues if issue.startswith("Routing rules")]
        default_issues = [issue for issue in config_issues if issue.startswith("Fallback profile")]
        if routing_issues:
            add("pressor.routing.json", False, routing_issues[0])
        else:
            add("pressor.routing.json", True, f"Loaded {len(rules)} routing rule(s).")
        if args.profile:
            if default_issues:
                add("default profile", False, default_issues[0])
            elif profiles:
                add("default profile", True, f"Fallback profile '{args.profile}' is valid.")
    except EncoderError as exc:
        add("pressor.routing.json", False, str(exc))
        if args.profile:
            add("default profile", False, f"Fallback profile '{args.profile}' could not be validated because routing config failed to load.")

    try:
        settings = load_wwise_config(wwise_file)
        add("pressor.wwise.json", True, f"Loaded {len(settings)} Wwise prep setting block(s).")
        try:
            validate_wwise_safe_settings(settings)
            add("wwise-safe policy", True, "Current Wwise prep settings satisfy the transparency policy.")
        except EncoderError as exc:
            add("wwise-safe policy", True, str(exc), warn=True)
        add("perceptual tuning", True, "Standalone encoding uses content-aware bitrate tuning only. No loudness normalization or dynamics processing is applied.")
    except EncoderError as exc:
        add("pressor.wwise.json", False, str(exc))

    if args.input:
        input_root = Path(args.input)
        if not input_root.exists():
            add("input path", False, f"Input folder does not exist: {input_root}")
        elif not input_root.is_dir():
            add("input path", False, f"Input path is not a folder: {input_root}")
        else:
            files = find_supported_audio_files(input_root, recursive=True, allowed_extensions=sorted(ALLOWED_INPUT_EXTENSIONS))
            add("input path", True, f"Found {len(files)} supported audio file(s) under {input_root}.", warn=len(files) == 0)
            if locator is not None:
                try:
                    encoder = AudioBatchEncoder(locator, ProfileStore(profile_file), RuleStore(rule_file))
                    lossy_count = 0
                    lossy_examples: list[str] = []
                    for file_path in files:
                        info = encoder.probe(file_path)
                        is_lossy, reason = assess_input_lossiness(file_path, info)
                        if is_lossy:
                            lossy_count += 1
                            if len(lossy_examples) < 3:
                                lossy_examples.append(f"{file_path.name} ({reason})")
                    if lossy_count:
                        detail = f"{lossy_count} file(s) appear to already be lossy encoded"
                        if lossy_examples:
                            detail += ": " + ", ".join(lossy_examples)
                        add("lossy input preview", True, detail, warn=True)
                    else:
                        add("lossy input preview", True, "No obviously lossy input files detected.")
                    if args.strict_routing and profiles:
                        issues = encoder.validate_routing_expectations(input_root, args.profile, recursive=not args.no_recursive, auto_profile=args.auto_profile)
                        if issues:
                            add("strict routing preview", True, f"{len(issues)} file(s) would fail strict routing.", warn=True)
                        else:
                            add("strict routing preview", True, "All matching audio files satisfy strict routing.")
                except Exception as exc:
                    add("input inspection", False, str(exc))

    if args.output:
        output_root = Path(args.output)
        parent = output_root if output_root.exists() else output_root.parent
        add("output path", parent.exists(), f"Output target resolves under {output_root}.")
    if args.input and Path(args.input).exists() and (args.output or args.review_pack):
        try:
            validate_path_relationships(normalize_path(args.input), normalize_path(args.output), normalize_path(args.review_pack))
            add("path relationships", True, "Output and review-pack are outside the input folder.")
        except EncoderError as exc:
            add("path relationships", False, str(exc))

    print("Pressor doctor")
    print("=" * 60)
    for item in checks:
        print(f"[{item['level']}] {item['name']}: {item['detail']}")
    print("=" * 60)
    print(f"Failures: {failures} | Warnings: {warnings}")
    return 0 if failures == 0 else 2
