from __future__ import annotations

import json
import logging
import math
import random
import struct
import tempfile
import threading
import shutil
import wave
import sys
from datetime import datetime
from pathlib import Path
from dataclasses import asdict
from typing import Any, Dict, List

from pressor.cli.main import main as cli_main
from pressor.core.subprocess_utils import DEFAULT_FFPROBE_TIMEOUT, run_external

from encoder import ALLOWED_INPUT_EXTENSIONS, AudioBatchEncoder, EncoderError, FFmpegLocator, JobResult, ProfileStore, RouteRule, RuleStore
from pressor.core.config import (
    get_app_dir,
    get_profile_file,
    get_rule_file,
    get_wwise_file,
    load_profiles_config,
    load_routing_config,
    load_wwise_config,
    validate_config_bundle,
)
from pressor.core.paths import (
    default_output_root_for_manifest_build,
    find_supported_audio_files,
    normalize_path,
    validate_path_relationships,
    create_run_workspace,
)
from pressor.core.reports import write_scan_report as core_write_scan_report, write_strict_routing_report as core_write_strict_routing_report
from pressor.pipeline.doctor import run_doctor as pipeline_run_doctor
from pressor.pipeline.selftest import run_selftest as pipeline_run_selftest
from pressor.pipeline.run_job import run_encode_job
from pressor.gui.state import GuiSessionState
from pressor.gui.presenters import (
    TABLE_COLUMNS,
    FOLDER_CONVENTIONS_TEXT,
    apply_overrides as gui_apply_overrides,
    build_table_values,
    dedupe_destination as gui_dedupe_destination,
    describe_drop_selection,
    split_drop_data,
)


APP_DIR = get_app_dir()
PROFILE_FILE = get_profile_file(APP_DIR)
RULE_FILE = get_rule_file(APP_DIR)
WWISE_FILE = get_wwise_file(APP_DIR)
ASSET_DIR = APP_DIR / "assets"
ICON_FILE = ASSET_DIR / "pressor.ico"
ICON_PNG = ASSET_DIR / "icon_256.png"
SPLASH_PNG = ASSET_DIR / "splash.png"
LOG_DIR = APP_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / f"pressor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    handlers=[logging.FileHandler(LOG_FILE, encoding="utf-8"), logging.StreamHandler()],
)
LOGGER = logging.getLogger("pressor")


def make_encoder(ffmpeg_path: str | None = None, ffprobe_path: str | None = None) -> AudioBatchEncoder:
    locator = FFmpegLocator(ffmpeg_path, ffprobe_path)
    return AudioBatchEncoder(locator, ProfileStore(PROFILE_FILE), RuleStore(RULE_FILE))


def _tool_version(binary_path: str, flag: str = "-version") -> str:
    result = run_external([binary_path, flag], timeout=DEFAULT_FFPROBE_TIMEOUT, text=True)
    if result.returncode != 0:
        raise EncoderError(f"Failed to query version for {binary_path}: {result.stderr.strip()}")
    first_line = (result.stdout or result.stderr).splitlines()[0].strip()
    return first_line


def _doctor_check(path: Path, ok: bool, detail: str, level: str = "PASS") -> Dict[str, str]:
    return {"name": str(path), "level": level if ok else "FAIL", "detail": detail}


def run_doctor(args: argparse.Namespace) -> int:
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
        add("ffmpeg", True, f"Found at {locator.ffmpeg}; {_tool_version(locator.ffmpeg)}")
        add("ffprobe", True, f"Found at {locator.ffprobe}; {_tool_version(locator.ffprobe)}")
    except EncoderError as exc:
        add("ffmpeg/ffprobe", False, str(exc))

    try:
        profiles = load_profiles_config(PROFILE_FILE)
        add("pressor.profiles.json", True, f"Loaded {len(profiles)} profile(s): {', '.join(sorted(profiles.keys()))}")
    except EncoderError as exc:
        profiles = {}
        add("pressor.profiles.json", False, str(exc))

    try:
        rules = load_routing_config(RULE_FILE)
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
        settings = load_wwise_config(WWISE_FILE)
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
            if args.strict_routing and profiles and locator is not None:
                try:
                    encoder = AudioBatchEncoder(locator, ProfileStore(PROFILE_FILE), RuleStore(RULE_FILE))
                    issues = encoder.validate_routing_expectations(input_root, args.profile, recursive=not args.no_recursive, auto_profile=args.auto_profile)
                    if issues:
                        add("strict routing preview", True, f"{len(issues)} file(s) would fail strict routing.", warn=True)
                    else:
                        add("strict routing preview", True, "All matching audio files satisfy strict routing.")
                except Exception as exc:
                    add("strict routing preview", False, str(exc))

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




def load_wwise_settings() -> Dict[str, Dict[str, object]]:
    return load_wwise_config(WWISE_FILE)


def validate_wwise_safe_settings(settings: Dict[str, Dict[str, object]]) -> None:
    disallowed_keys = {
        "normalize",
        "normalize_db",
        "loudnorm",
        "dynaudnorm",
        "compand",
        "compressor",
        "limiter",
        "volume_db",
        "gain_db",
        "eq",
        "ffmpeg_audio_filters",
    }
    for profile_name, profile_settings in settings.items():
        if not isinstance(profile_settings, dict):
            raise EncoderError(f"Wwise settings for {profile_name} must be an object.")
        risky = sorted(key for key in profile_settings.keys() if key in disallowed_keys)
        if risky:
            joined = ", ".join(risky)
            raise EncoderError(
                f"Wwise-safe mode rejects risky transforms for {profile_name}: {joined}. "
                "Pressor is intended to remain acoustically invisible and must not normalize, compress, limit, EQ, or otherwise reshape loudness and dynamics before Wwise."
            )


def save_report(results: List[JobResult], output_root: Path) -> Path:
    report_path = output_root / "pressor_report.csv"
    AudioBatchEncoder.write_csv_report(results, report_path)
    return report_path


def save_scan_report(scan_results: List[Dict[str, object]], output_path: Path) -> Path:
    return core_write_scan_report(scan_results, output_path)


def save_strict_routing_report(issues: List[Dict[str, object]], output_path: Path) -> Path:
    return core_write_strict_routing_report(issues, output_path)


def run_selftest(args: argparse.Namespace) -> int:
    return pipeline_run_selftest(args, make_encoder, save_report, save_scan_report, LOG_FILE)


def run_cli(args: argparse.Namespace) -> int:
    encoder = make_encoder(args.ffmpeg, args.ffprobe)
    return run_encode_job(
        args,
        encoder,
        save_report,
        save_scan_report,
        save_strict_routing_report,
        load_wwise_settings,
        validate_wwise_safe_settings,
        WWISE_FILE,
        LOG_FILE,
    )


def run_gui(preload_paths: list[str] | None = None) -> int:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk

    try:
        from tkinterdnd2 import DND_FILES, TkinterDnD  # type: ignore
        dnd_available = True
    except Exception:
        DND_FILES = None  # type: ignore[assignment]
        TkinterDnD = None  # type: ignore[assignment]
        dnd_available = False

    encoder = make_encoder()
    root = TkinterDnD.Tk() if dnd_available and TkinterDnD is not None else tk.Tk()
    root.title("Pressor")
    root.geometry("1220x860")

    try:
        if ICON_PNG.exists():
            root._pressor_icon = tk.PhotoImage(file=str(ICON_PNG))
            root.iconphoto(True, root._pressor_icon)
        if sys.platform.startswith("win") and ICON_FILE.exists():
            try:
                root.iconbitmap(default=str(ICON_FILE))
            except Exception:
                pass
    except Exception:
        pass

    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True)

    run_tab = ttk.Frame(notebook, padding=12)
    rules_tab = ttk.Frame(notebook, padding=12)
    profiles_tab = ttk.Frame(notebook, padding=12)
    conventions_tab = ttk.Frame(notebook, padding=12)
    notebook.add(run_tab, text="Run Job")
    notebook.add(rules_tab, text="Routing Rules")
    notebook.add(profiles_tab, text="Profiles")
    notebook.add(conventions_tab, text="Conventions")

    input_var = tk.StringVar()
    output_var = tk.StringVar()
    profile_var = tk.StringVar(value=encoder.profiles.names()[0])
    manifest_var = tk.StringVar()
    review_pack_var = tk.StringVar()
    workers_var = tk.IntVar(value=2)
    overwrite_var = tk.BooleanVar(value=False)
    dry_run_var = tk.BooleanVar(value=False)
    recursive_var = tk.BooleanVar(value=True)
    keep_larger_var = tk.BooleanVar(value=False)
    auto_profile_var = tk.BooleanVar(value=False)
    strict_routing_var = tk.BooleanVar(value=False)
    wwise_prep_var = tk.BooleanVar(value=False)
    wwise_safe_var = tk.BooleanVar(value=False)
    status_var = tk.StringVar(value="Choose folders, then preview or run.")
    summary_var = tk.StringVar(value="No scan yet. Timestamped run folders are created automatically.")

    session_state = GuiSessionState()
    active_thread: threading.Thread | None = None
    columns = TABLE_COLUMNS

    def _split_drop_data(data: str) -> list[Path]:
        return split_drop_data(root, data)

    def _dedupe_destination(dest: Path) -> Path:
        return gui_dedupe_destination(dest)

    def _stage_dropped_paths(staging_root: Path, paths: list[Path]) -> Path:
        staged_input = staging_root / "input"
        staged_input.mkdir(parents=True, exist_ok=True)
        for source in paths:
            if source.is_dir():
                target = _dedupe_destination(staged_input / source.name)
                shutil.copytree(source, target)
            else:
                target = _dedupe_destination(staged_input / source.name)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
        return staged_input

    def _effective_input_root() -> tuple[Path, tempfile.TemporaryDirectory[str] | None]:
        if session_state.dropped_paths:
            temp_dir = tempfile.TemporaryDirectory(prefix="pressor_drop_")
            staged_input = _stage_dropped_paths(Path(temp_dir.name), session_state.dropped_paths)
            return staged_input, temp_dir
        if not input_var.get():
            raise EncoderError("Choose an input folder or drag files into Pressor.")
        return Path(input_var.get()), None

    def _describe_drop_selection() -> str:
        return describe_drop_selection(session_state.dropped_paths)

    def _clear_drop_selection() -> None:
        session_state.clear_dropped_paths()
        drop_status_var.set("No dragged files staged.")
        if input_var.get() == "[dragged files]":
            input_var.set("")
        status_var.set("Choose folders, then preview or run.")

    def _apply_drop_paths(paths: list[Path]) -> None:
        session_state.clear_dropped_paths()
        existing = [path.resolve() for path in paths if path.exists()]
        if not existing:
            return
        if len(existing) == 1 and existing[0].is_dir():
            input_var.set(str(existing[0]))
            drop_status_var.set(f"Dropped folder loaded: {existing[0]}")
            status_var.set("Dropped folder ready.")
            return
        session_state.dropped_paths.extend(existing)
        input_var.set("[dragged files]")
        drop_status_var.set(f"Using dragged selection: {describe_drop_selection(session_state.dropped_paths)}. Files are staged into a temporary input folder when you scan or run.")
        status_var.set("Dragged selection ready.")

    def _handle_drop_event(event: object) -> None:
        data = getattr(event, "data", "")
        paths = _split_drop_data(str(data))
        if not paths:
            return
        _apply_drop_paths(paths)

    def browse_dir(target: tk.StringVar, title: str) -> None:
        value = filedialog.askdirectory(title=title)
        if value:
            target.set(value)

    def browse_file(target: tk.StringVar, title: str) -> None:
        value = filedialog.asksaveasfilename(title=title, defaultextension=".json", filetypes=[("JSON", "*.json")])
        if value:
            target.set(value)

    def append(text: str) -> None:
        output_text.insert("end", text + "\n")
        output_text.see("end")

    def clear_table() -> None:
        for item_id in file_tree.get_children():
            file_tree.delete(item_id)

    def fill_table(items: list[dict]) -> None:
        clear_table()
        for item in items:
            values = build_table_values(item)
            tag = str(item.get("profile_source", "default"))
            file_tree.insert("", "end", values=values, tags=(tag,))

    def apply_overrides(items: list[dict]) -> list[dict]:
        return gui_apply_overrides(items, session_state.override_map)

    def refresh_table_from_state() -> None:
        session_state.scan_results = apply_overrides(session_state.base_scan_results)
        fill_table(session_state.scan_results)

    def set_controls(enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        readonly = "readonly" if enabled else "disabled"
        for widget in interactive_widgets:
            try:
                widget.configure(state=state)
            except tk.TclError:
                pass
        profile_box.configure(state=readonly)
        start_button.configure(state=state)
        scan_button.configure(state=state)

    def refresh_profiles() -> None:
        names = encoder.profiles.names()
        profile_box["values"] = names
        override_box["values"] = names
        if profile_var.get() not in names:
            profile_var.set(names[0])
        if override_profile_var.get() not in names:
            override_profile_var.set(profile_var.get())

    def validate_paths(require_output: bool = False) -> tuple[Path | None, Path | None]:
        input_root: Path | None = None
        if input_var.get() and input_var.get() != "[dragged files]":
            input_root = Path(input_var.get())
        elif not session_state.dropped_paths:
            raise EncoderError("Choose an input folder or drag files into Pressor.")
        output_root = Path(output_var.get()) if output_var.get() else None
        if require_output and output_root is None:
            raise EncoderError("Choose an output folder.")
        review_root = normalize_path(review_pack_var.get())
        validate_path_relationships(input_root, output_root, review_root)
        return input_root, output_root

    def run_scan() -> None:
        nonlocal active_thread
        if active_thread and active_thread.is_alive():
            messagebox.showinfo("Pressor", "A job is already running.")
            return
        output_text.delete("1.0", "end")
        append("Scanning audio files...")
        status_var.set("Scanning files...")
        summary_var.set("Scanning...")
        progress.configure(mode="indeterminate")
        progress.start(12)
        set_controls(False)

        def worker() -> None:
            try:
                _, _ = validate_paths(False)
                effective_input, temp_dir = _effective_input_root()
                try:
                    results = encoder.scan(effective_input, profile_var.get(), recursive=recursive_var.get(), auto_profile=auto_profile_var.get())
                    strict_issues = []
                    if strict_routing_var.get():
                        strict_issues = encoder.validate_routing_expectations(effective_input, profile_var.get(), recursive=recursive_var.get(), auto_profile=auto_profile_var.get())
                finally:
                    if temp_dir is not None:
                        temp_dir.cleanup()

                def on_done() -> None:
                    session_state.base_scan_results = results
                    refresh_table_from_state()
                    counts: dict[str, int] = {}
                    for item in results:
                        counts[item.get("chosen_profile", "unknown")] = counts.get(item.get("chosen_profile", "unknown"), 0) + 1
                    counts_text = ", ".join(f"{name}: {count}" for name, count in sorted(counts.items())) or "no files found"
                    summary = f"Scanned {len(results)} file(s)"
                    if strict_routing_var.get():
                        summary += f". Strict routing issues: {len(strict_issues)}"
                    summary += f". {counts_text}"
                    summary_var.set(summary)
                    status_var.set("Scan complete.")
                    append(summary)
                    if strict_issues:
                        append(f"Strict routing would block {len(strict_issues)} file(s) without a routing rule match.")
                    progress.stop()
                    progress.configure(mode="determinate", value=0)
                    set_controls(True)

                root.after(0, on_done)
            except Exception as exc:
                def on_err() -> None:
                    progress.stop()
                    progress.configure(mode="determinate", value=0)
                    set_controls(True)
                    status_var.set("Scan failed.")
                    messagebox.showerror("Scan failed", str(exc))

                root.after(0, on_err)

        active_thread = threading.Thread(target=worker, daemon=True)
        active_thread.start()

    def start_job() -> None:
        nonlocal active_thread
        if active_thread and active_thread.is_alive():
            messagebox.showinfo("Pressor", "A job is already running.")
            return
        output_text.delete("1.0", "end")
        append("Starting Pressor job...")
        status_var.set("Preparing run...")
        summary_var.set("Running...")
        progress.configure(mode="indeterminate")
        progress.start(12)
        set_controls(False)

        def worker() -> None:
            temp_manifest_path: Path | None = None
            temp_input_dir: tempfile.TemporaryDirectory[str] | None = None
            try:
                _, output_root = validate_paths(True)
                assert output_root is not None
                effective_input, temp_input_dir = _effective_input_root()
                workspace = create_run_workspace(output_root)
                effective_output_root = workspace.encoded_root
                reports_root = workspace.reports_root
                review_output_root = normalize_path(review_pack_var.get()) or workspace.review_root
                manifest_path = Path(manifest_var.get()) if manifest_var.get() else None
                forced_container = ".wav" if wwise_prep_var.get() else None

                if manifest_path or session_state.override_map:
                    plan_items = encoder.build_plan(
                        effective_input,
                        effective_output_root,
                        profile_var.get(),
                        recursive=recursive_var.get(),
                        forced_container=forced_container,
                        auto_profile=auto_profile_var.get(),
                        strict_routing=strict_routing_var.get(),
                    )
                    for plan_item in plan_items:
                        if plan_item.relative_path in session_state.override_map:
                            plan_item.profile = session_state.override_map[plan_item.relative_path]
                            plan_item.profile_source = "manual-override"
                            plan_item.profile_confidence = 100
                            plan_item.profile_reasons = ["manual override in GUI"]
                    payload = {
                        "input_root": str(effective_input.resolve()),
                        "output_root": str(effective_output_root.resolve()),
                        "default_profile": profile_var.get(),
                        "recursive": recursive_var.get(),
                        "auto_profile": auto_profile_var.get(),
                        "items": [asdict(item) for item in plan_items],
                    }
                    if manifest_path:
                        manifest_path.parent.mkdir(parents=True, exist_ok=True)
                        manifest_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
                        root.after(0, lambda: append(f"Manifest written: {manifest_path}"))
                    else:
                        tmp = tempfile.NamedTemporaryFile(prefix="pressor_gui_", suffix=".json", delete=False)
                        tmp.close()
                        temp_manifest_path = Path(tmp.name)
                        temp_manifest_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
                    manifest_to_use = manifest_path or temp_manifest_path
                else:
                    manifest_to_use = None

                if wwise_prep_var.get():
                    settings = load_wwise_settings()
                    if wwise_safe_var.get() or wwise_prep_var.get():
                        validate_wwise_safe_settings(settings)
                    results = encoder.prep_for_wwise(
                        input_root=effective_input,
                        output_root=effective_output_root,
                        default_profile=profile_var.get(),
                        recursive=recursive_var.get(),
                        overwrite=overwrite_var.get(),
                        dry_run=dry_run_var.get(),
                        max_workers=workers_var.get(),
                        use_manifest=manifest_to_use,
                        compare_output_root=review_output_root,
                        prep_settings=settings,
                        auto_profile=auto_profile_var.get(),
                        strict_routing=strict_routing_var.get(),
                    )
                else:
                    results = encoder.batch_encode(
                        input_root=effective_input,
                        output_root=effective_output_root,
                        default_profile=profile_var.get(),
                        recursive=recursive_var.get(),
                        overwrite=overwrite_var.get(),
                        dry_run=dry_run_var.get(),
                        max_workers=workers_var.get(),
                        skip_if_larger=not keep_larger_var.get(),
                        use_manifest=manifest_to_use,
                        compare_output_root=review_output_root,
                        auto_profile=auto_profile_var.get(),
                        strict_routing=strict_routing_var.get(),
                    )

                report_path = save_report(results, reports_root)
                scan_items = encoder.scan(effective_input, profile_var.get(), recursive=recursive_var.get(), auto_profile=auto_profile_var.get())

                if temp_manifest_path is not None:
                    temp_manifest_path.unlink(missing_ok=True)

                def on_done() -> None:
                    session_state.base_scan_results = scan_items
                    refresh_table_from_state()
                    summary_text = AudioBatchEncoder.summarize(results)
                    success_count = sum(1 for item in results if item.success)
                    failed_count = sum(1 for item in results if not item.success)
                    changed_count = sum(1 for item in results if item.changed)
                    summary_var.set(f"Succeeded: {success_count} | Changed: {changed_count} | Failed: {failed_count}")
                    status_var.set("Run complete." if failed_count == 0 else "Run completed with failures.")
                    append(f"Run folder: {workspace.run_root}")
                    append(summary_text)
                    append(f"CSV report: {report_path}")
                    append(f"Log file: {LOG_FILE}")
                    failed = [item for item in results if not item.success]
                    if failed:
                        append("Failures:")
                        for item in failed[:20]:
                            append(f" - {item.source.name}: {item.message}")
                    progress.stop()
                    progress.configure(mode="determinate", value=100)
                    set_controls(True)

                root.after(0, on_done)
            except Exception as exc:
                if temp_manifest_path is not None:
                    temp_manifest_path.unlink(missing_ok=True)

                def on_err() -> None:
                    progress.stop()
                    progress.configure(mode="determinate", value=0)
                    set_controls(True)
                    status_var.set("Run failed.")
                    messagebox.showerror("Encoding failed", str(exc))

                root.after(0, on_err)
            finally:
                if temp_input_dir is not None:
                    temp_input_dir.cleanup()

        active_thread = threading.Thread(target=worker, daemon=True)
        active_thread.start()

    brand_frame = ttk.Frame(run_tab)
    brand_frame.pack(fill="x", pady=(0, 10))
    try:
        if SPLASH_PNG.exists():
            root._pressor_splash = tk.PhotoImage(file=str(SPLASH_PNG))
            ttk.Label(brand_frame, image=root._pressor_splash).pack(side="left", anchor="w")
        else:
            ttk.Label(brand_frame, text="PRESSOR", font=("Segoe UI", 20, "bold")).pack(side="left", anchor="w")
    except Exception:
        ttk.Label(brand_frame, text="PRESSOR", font=("Segoe UI", 20, "bold")).pack(side="left", anchor="w")

    top = ttk.Frame(run_tab)
    top.pack(fill="x")

    ttk.Label(top, textvariable=workspace_var).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))

    drop_status_var = tk.StringVar(value="Drag audio files or folders into the drop zone, or browse for an input folder.")
    top.columnconfigure(0, weight=1)

    ttk.Label(top, text="Pressor Input Folder").grid(row=1, column=0, sticky="w")
    input_entry = ttk.Entry(top, textvariable=input_var, width=100)
    input_entry.grid(row=2, column=0, sticky="ew")
    input_btn = ttk.Button(top, text="Browse", command=lambda: browse_dir(input_var, "Select input folder"))
    input_btn.grid(row=2, column=1, padx=8)

    drop_frame = ttk.LabelFrame(top, text="Drag and Drop")
    drop_frame.grid(row=10, column=0, columnspan=2, sticky="ew", pady=(10, 0))
    drop_frame.columnconfigure(0, weight=1)
    drop_label = tk.Label(drop_frame, text="Drop audio files or folders here", relief="groove", bd=2, padx=12, pady=16)
    drop_label.grid(row=0, column=0, sticky="ew")
    ttk.Label(drop_frame, textvariable=drop_status_var, wraplength=760).grid(row=1, column=0, sticky="w", pady=(8, 0))
    clear_drop_button = ttk.Button(drop_frame, text="Clear Dropped Selection", command=_clear_drop_selection)
    clear_drop_button.grid(row=0, column=1, padx=(8, 0))

    if dnd_available and DND_FILES is not None:
        for widget in (drop_label, drop_frame):
            widget.drop_target_register(DND_FILES)
            widget.dnd_bind('<<Drop>>', _handle_drop_event)
        drop_label.configure(text="Drop audio files or folders here")
    else:
        drop_label.configure(text="Install tkinterdnd2 for in-window drag and drop, or drop files onto the Pressor app shortcut/exe.")

    ttk.Label(top, text="Output Root").grid(row=10, column=0, sticky="w", pady=(10, 0))
    output_entry = ttk.Entry(top, textvariable=output_var, width=100)
    output_entry.grid(row=10, column=0, sticky="ew")
    output_btn = ttk.Button(top, text="Browse", command=lambda: browse_dir(output_var, "Select output root"))
    output_btn.grid(row=10, column=1, padx=8)

    ttk.Label(top, text="Default Profile").grid(row=10, column=0, sticky="w", pady=(10, 0))
    profile_box = ttk.Combobox(top, textvariable=profile_var, values=encoder.profiles.names(), state="readonly", width=24)
    profile_box.grid(row=10, column=0, sticky="w")

    ttk.Label(top, text="Manifest File (optional)").grid(row=10, column=0, sticky="w", pady=(10, 0))
    manifest_entry = ttk.Entry(top, textvariable=manifest_var, width=100)
    manifest_entry.grid(row=10, column=0, sticky="ew")
    manifest_btn = ttk.Button(top, text="Save As", command=lambda: browse_file(manifest_var, "Choose manifest path"))
    manifest_btn.grid(row=10, column=1, padx=8)

    ttk.Label(top, text="Review Pack Output Folder (optional)").grid(row=10, column=0, sticky="w", pady=(10, 0))
    review_entry = ttk.Entry(top, textvariable=review_pack_var, width=100)
    review_entry.grid(row=10, column=0, sticky="ew")
    review_btn = ttk.Button(top, text="Browse", command=lambda: browse_dir(review_pack_var, "Select review pack output root"))
    review_btn.grid(row=10, column=1, padx=8)

    opts = ttk.Frame(run_tab)
    opts.pack(fill="x", pady=(12, 4))
    ttk.Label(opts, text="Workers").pack(side="left")
    workers_spin = ttk.Spinbox(opts, from_=1, to=32, textvariable=workers_var, width=6)
    workers_spin.pack(side="left", padx=(6, 12))
    recursive_chk = ttk.Checkbutton(opts, text="Recursive", variable=recursive_var)
    recursive_chk.pack(side="left", padx=(0, 10))
    overwrite_chk = ttk.Checkbutton(opts, text="Overwrite", variable=overwrite_var)
    overwrite_chk.pack(side="left", padx=(0, 10))
    dry_run_chk = ttk.Checkbutton(opts, text="Dry Run", variable=dry_run_var)
    dry_run_chk.pack(side="left", padx=(0, 10))
    keep_larger_chk = ttk.Checkbutton(opts, text="Keep Larger Outputs", variable=keep_larger_var)
    keep_larger_chk.pack(side="left", padx=(0, 10))
    auto_profile_chk = ttk.Checkbutton(opts, text="Auto Profile", variable=auto_profile_var)
    auto_profile_chk.pack(side="left", padx=(0, 10))
    strict_routing_chk = ttk.Checkbutton(opts, text="Strict Routing", variable=strict_routing_var)
    strict_routing_chk.pack(side="left", padx=(0, 10))

    opts2 = ttk.Frame(run_tab)
    opts2.pack(fill="x", pady=(0, 8))
    wwise_prep_chk = ttk.Checkbutton(opts2, text="Wwise Prep", variable=wwise_prep_var)
    wwise_prep_chk.pack(side="left", padx=(0, 10))
    wwise_safe_chk = ttk.Checkbutton(opts2, text="Wwise Safe", variable=wwise_safe_var)
    wwise_safe_chk.pack(side="left", padx=(0, 10))

    actions = ttk.Frame(run_tab)
    actions.pack(fill="x", pady=(0, 8))
    scan_button = ttk.Button(actions, text="Preview Scan", command=run_scan)
    scan_button.pack(side="left")
    start_button = ttk.Button(actions, text="Start", command=start_job)
    start_button.pack(side="left", padx=(8, 0))
    ttk.Label(actions, textvariable=status_var).pack(side="left", padx=(18, 0))

    override_bar = ttk.Frame(run_tab)
    override_bar.pack(fill="x", pady=(0, 8))
    selected_file_var = tk.StringVar(value="No file selected.")
    override_profile_var = tk.StringVar(value=profile_var.get())
    ttk.Label(override_bar, textvariable=selected_file_var).pack(side="left")
    ttk.Label(override_bar, text="Override To").pack(side="left", padx=(16, 6))
    override_box = ttk.Combobox(override_bar, textvariable=override_profile_var, values=encoder.profiles.names(), state="readonly", width=18)
    override_box.pack(side="left")

    def update_selection(*_args: object) -> None:
        selected = file_tree.selection()
        if not selected:
            selected_file_var.set("No file selected.")
            return
        values = file_tree.item(selected[0], "values")
        selected_file_var.set(str(values[0]))
        if len(values) > 1:
            override_profile_var.set(str(values[1]))

    def apply_selected_override() -> None:
        selected = file_tree.selection()
        if not selected:
            messagebox.showinfo("Pressor", "Select a file in the preview table first.")
            return
        rel = str(file_tree.item(selected[0], "values")[0])
        session_state.override_map[rel] = override_profile_var.get()
        refresh_table_from_state()
        for item_id in file_tree.get_children():
            if str(file_tree.item(item_id, "values")[0]) == rel:
                file_tree.selection_set(item_id)
                file_tree.focus(item_id)
                break
        status_var.set(f"Manual override set for {rel}.")

    def clear_selected_override() -> None:
        selected = file_tree.selection()
        if not selected:
            messagebox.showinfo("Pressor", "Select a file in the preview table first.")
            return
        rel = str(file_tree.item(selected[0], "values")[0])
        session_state.override_map.pop(rel, None)
        refresh_table_from_state()
        for item_id in file_tree.get_children():
            if str(file_tree.item(item_id, "values")[0]) == rel:
                file_tree.selection_set(item_id)
                file_tree.focus(item_id)
                break
        status_var.set(f"Manual override cleared for {rel}.")

    apply_override_button = ttk.Button(override_bar, text="Apply Override", command=apply_selected_override)
    apply_override_button.pack(side="left", padx=(8, 0))
    clear_override_button = ttk.Button(override_bar, text="Clear Override", command=clear_selected_override)
    clear_override_button.pack(side="left", padx=(8, 0))

    progress = ttk.Progressbar(run_tab, mode="determinate")
    progress.pack(fill="x", pady=(0, 8))
    ttk.Label(run_tab, textvariable=summary_var).pack(anchor="w", pady=(0, 8))

    preview_frame = ttk.LabelFrame(run_tab, text="File Preview")
    preview_frame.pack(fill="both", expand=True)
    preview_frame.columnconfigure(0, weight=1)
    preview_frame.rowconfigure(0, weight=1)

    file_tree = ttk.Treeview(preview_frame, columns=columns, show="headings", height=16)
    headings = {
        "relative_path": "File",
        "detected_profile": "Profile",
        "encode_plan": "Plan",
        "bitrate": "Bitrate",
        "source": "Source",
        "confidence": "Confidence",
        "channels": "Ch",
        "duration": "Duration",
        "sample_rate": "Hz",
        "notes": "Reason",
    }
    widths = {
        "relative_path": 300,
        "detected_profile": 90,
        "encode_plan": 80,
        "bitrate": 70,
        "source": 110,
        "confidence": 80,
        "channels": 40,
        "duration": 70,
        "sample_rate": 80,
        "notes": 280,
    }
    for col in columns:
        file_tree.heading(col, text=headings[col])
        file_tree.column(col, width=widths[col], anchor="w")
    file_tree.grid(row=0, column=0, sticky="nsew")
    tree_scroll_y = ttk.Scrollbar(preview_frame, orient="vertical", command=file_tree.yview)
    tree_scroll_y.grid(row=0, column=1, sticky="ns")
    tree_scroll_x = ttk.Scrollbar(preview_frame, orient="horizontal", command=file_tree.xview)
    tree_scroll_x.grid(row=1, column=0, sticky="ew")
    file_tree.configure(yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)
    file_tree.bind("<<TreeviewSelect>>", update_selection)
    file_tree.tag_configure("routing-rule", background="#e8f5e9")
    file_tree.tag_configure("auto-preview", background="#fff8e1")
    file_tree.tag_configure("default", background="#ffebee")
    file_tree.tag_configure("manifest", background="#e3f2fd")
    file_tree.tag_configure("manual-override", background="#ede7f6")

    ttk.Label(run_tab, text="Run Output").pack(anchor="w", pady=(10, 0))
    output_text = tk.Text(run_tab, height=10, wrap="word")
    output_text.pack(fill="both", expand=False)

    interactive_widgets = [
        input_entry, input_btn, output_entry, output_btn, manifest_entry, manifest_btn,
        review_entry, review_btn, workers_spin, recursive_chk, overwrite_chk, dry_run_chk,
        keep_larger_chk, auto_profile_chk, strict_routing_chk, wwise_prep_chk, wwise_safe_chk, override_box, apply_override_button, clear_override_button, clear_drop_button,
    ]

    rules_text = tk.Text(rules_tab, wrap="none")
    rules_text.pack(fill="both", expand=True)

    def load_rules_into_editor() -> None:
        rules_text.delete("1.0", "end")
        raw = [{"pattern": rule.pattern, "profile": rule.profile} for rule in encoder.rules.load_rules()]
        rules_text.insert("1.0", json.dumps(raw, indent=2))

    def save_rules_from_editor() -> None:
        data = json.loads(rules_text.get("1.0", "end"))
        rules = [RouteRule(pattern=str(item["pattern"]), profile=str(item["profile"])) for item in data]
        encoder.rules.save_rules(rules)
        messagebox.showinfo("Saved", "Routing rules saved.")

    ttk.Button(rules_tab, text="Save Rules", command=save_rules_from_editor).pack(anchor="w", pady=(8, 0))
    load_rules_into_editor()

    profiles_text = tk.Text(profiles_tab, wrap="none")
    profiles_text.pack(fill="both", expand=True)

    def load_profiles_into_editor() -> None:
        profiles_text.delete("1.0", "end")
        profiles_text.insert("1.0", json.dumps(encoder.profiles.load_profiles(), indent=2))

    def save_profiles_from_editor() -> None:
        data = json.loads(profiles_text.get("1.0", "end"))
        encoder.profiles.save_profiles(data)
        refresh_profiles()
        messagebox.showinfo("Saved", "Profiles saved.")

    ttk.Button(profiles_tab, text="Save Profiles", command=save_profiles_from_editor).pack(anchor="w", pady=(8, 0))
    load_profiles_into_editor()

    conventions_text = tk.Text(conventions_tab, wrap="word")
    conventions_text.pack(fill="both", expand=True)
    conventions_text.insert("1.0", FOLDER_CONVENTIONS_TEXT)
    conventions_text.configure(state="disabled")

    if preload_paths:
        preload_existing = [Path(item).expanduser() for item in preload_paths if Path(item).expanduser().exists()]
        if preload_existing:
            _apply_drop_paths(preload_existing)

    root.mainloop()
    return 0


def main() -> int:
    return cli_main(
        run_selftest=run_selftest,
        run_doctor=run_doctor,
        run_gui=run_gui,
        run_cli=run_cli,
        error_type=EncoderError,
    )


if __name__ == "__main__":
    raise SystemExit(main())
