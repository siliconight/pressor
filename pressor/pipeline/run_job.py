from __future__ import annotations

import json
import sys
from pathlib import Path
import platform

from encoder import EncoderError
from pressor.pipeline.manifest import (
    build_manifest,
    build_wwise_manifest,
    load_manifest_context,
    write_wwise_import_json,
    write_wwise_import_tsv,
)
from pressor.pipeline.review_pack import normalize_review_pack_path, validate_review_pack_relationships
from pressor.pipeline.progress import print_progress_header, print_progress_result, print_run_summary
from pressor.pipeline.change_detection import DEFAULT_STATE_FILENAME, filter_changed_manifest, load_state, save_state, update_state_from_manifest_results
from pressor.core.paths import default_output_root_for_manifest_build, normalize_path, create_run_workspace
from pressor.core.reports import write_failure_report, build_run_records, write_jsonl_log
from pressor.tools.benchmark import print_benchmark_summary
from pressor.version import __version__


def _status_from_result(result) -> tuple[str, str | None]:
    message = (result.message or "").strip()
    lowered = message.lower()
    if result.success:
        if not result.changed and "skip" in lowered:
            return "skipped", message
        if not result.changed and "larger" in lowered:
            return "kept original", message
        if not result.changed and "dry run" in lowered:
            return "planned", message
        if result.changed:
            return "encoded", None
        return "completed", message or None
    return "failed", message or result.likely_cause or None


def _progress_callback(index, total, item, result) -> None:
    source_name = Path(str(item.source)).name
    profile = getattr(item, "profile", None)
    status, reason = _status_from_result(result)
    print_progress_result(index, total, source_name, profile, status, reason)




def _print_wwise_summary(prepared_assets: int, unchanged_assets: int, skipped_assets: int, failed_assets: int, json_path: Path | None, tsv_path: Path | None, reports_root: Path) -> None:
    print("Wwise mode summary")
    print("")
    print(f"Prepared assets : {prepared_assets}")
    print(f"Unchanged assets: {unchanged_assets}")
    print(f"Skipped lossy   : {skipped_assets}")
    print(f"Failed          : {failed_assets}")
    if json_path is not None:
        print(f"Import JSON     : {json_path}")
    if tsv_path is not None:
        print(f"Import TSV      : {tsv_path}")
    print(f"Reports         : {reports_root}")
    print("")

def run_encode_job(
    args,
    encoder,
    save_report,
    save_scan_report,
    save_strict_routing_report,
    load_wwise_settings,
    validate_wwise_safe_settings,
    wwise_file: Path,
    log_file: Path,
) -> int:
    print("")
    print("Pressor starting...")
    print("")
    manifest_payload: dict[str, object] | None = None
    if args.skip_lossy_inputs and args.fail_on_lossy_inputs:
        raise EncoderError("Choose either --skip-lossy-inputs or --fail-on-lossy-inputs, not both.")
    if args.allow_lossy_inputs and (args.skip_lossy_inputs or args.fail_on_lossy_inputs):
        args.skip_lossy_inputs = False
        args.fail_on_lossy_inputs = False
    if getattr(args, "wwise_mode", False):
        print("Running in Wwise mode.")
        args.wwise_safe = True
        print("Wwise preset enabled: Wwise-safe validation and import artifact generation.")
        if not args.changed_only:
            print("Changed-only processing is not forced in Wwise mode. Use --changed-only explicitly when you want incremental behavior.")
        print("")
    if args.manifest:
        manifest_payload = load_manifest_context(Path(args.manifest))

    recursive = bool(manifest_payload.get("recursive", True)) if manifest_payload is not None else not args.no_recursive
    input_root = normalize_path(args.input)
    output_root = normalize_path(args.output)

    if input_root is None and manifest_payload is not None:
        manifest_input = manifest_payload.get("input_root")
        if isinstance(manifest_input, str) and manifest_input:
            input_root = normalize_path(manifest_input)
    if output_root is None and manifest_payload is not None:
        manifest_output = manifest_payload.get("output_root")
        if isinstance(manifest_output, str) and manifest_output:
            output_root = normalize_path(manifest_output)
    if input_root is None:
        raise EncoderError("Input folder is required unless it is provided by --manifest.")

    if args.scan_only:
        scan_results = encoder.scan(input_root, args.profile, recursive=recursive, auto_profile=args.auto_profile)
        if args.scan_report:
            report_path = save_scan_report(scan_results, Path(args.scan_report))
            print(f"Scan report written: {report_path}")
        if args.strict_routing:
            issues = encoder.validate_routing_expectations(input_root, args.profile, recursive=recursive, auto_profile=args.auto_profile)
            if issues:
                strict_report = Path(args.scan_report).with_name("pressor_strict_routing_report.csv") if args.scan_report else input_root / "pressor_strict_routing_report.csv"
                strict_path = save_strict_routing_report(issues, strict_report)
                print(f"Strict routing report written: {strict_path}")
                print(f"Strict routing found {len(issues)} file(s) without a routing rule match.", file=sys.stderr)
                print(json.dumps(scan_results, indent=2))
                return 2
        print(json.dumps(scan_results, indent=2))
        return 0

    if args.build_manifest and output_root is None:
        output_root = default_output_root_for_manifest_build(input_root)

    review_pack_root = normalize_review_pack_path(args.review_pack)

    if output_root is None and not args.manifest:
        raise EncoderError("Output folder is required unless --scan-only, --build-manifest, or --manifest is used.")
    if output_root is None:
        raise EncoderError("Output folder is required for this operation and was not found in the manifest.")

    effective_output_root = output_root
    reports_root = output_root
    run_root: Path | None = None
    if not args.build_manifest and not args.manifest:
        workspace = create_run_workspace(output_root, getattr(args, "run_label", None), flat_output=bool(getattr(args, "flat_output", False)))
        run_root = workspace.run_root
        effective_output_root = workspace.encoded_root
        reports_root = workspace.reports_root
        if review_pack_root is None:
            review_pack_root = workspace.review_root

    validate_review_pack_relationships(input_root, effective_output_root, review_pack_root)

    if args.strict_routing and not args.manifest:
        issues = encoder.validate_routing_expectations(input_root, args.profile, recursive=recursive, auto_profile=args.auto_profile)
        if issues:
            strict_report = reports_root / "pressor_strict_routing_report.csv"
            strict_path = save_strict_routing_report(issues, strict_report)
            raise EncoderError(f"Strict routing found {len(issues)} file(s) without a routing rule match. See {strict_path}")

    if args.build_manifest:
        manifest_path = build_manifest(
            encoder,
            Path(args.build_manifest),
            input_root,
            effective_output_root,
            args.profile,
            recursive,
            args.auto_profile,
            args.strict_routing,
            args.wwise_prep,
        )
        print(f"Manifest written: {manifest_path}")
        return 0

    wwise_json_path: Path | None = None
    wwise_tsv_path: Path | None = None
    if getattr(args, "wwise_mode", False):
        if not args.wwise_import_json_out:
            args.wwise_import_json_out = str(reports_root / "wwise_import.json")
        if not args.wwise_import_tsv_out:
            args.wwise_import_tsv_out = str(reports_root / "wwise_import.tsv")

    selected_manifest_path: Path | None = Path(args.manifest) if args.manifest else None
    selected_manifest_payload: dict[str, object] | None = manifest_payload
    state_manifest_path = output_root / DEFAULT_STATE_FILENAME
    mode_name = "wwise-prep" if args.wwise_prep else "encode"

    if args.changed_only and not args.build_manifest:
        base_manifest_path = reports_root / "pressor_manifest_full.json"
        selected_manifest_path = build_manifest(
            encoder,
            base_manifest_path,
            input_root,
            effective_output_root,
            args.profile,
            recursive,
            args.auto_profile,
            args.strict_routing,
            args.wwise_prep,
        )
        with selected_manifest_path.open("r", encoding="utf-8") as handle:
            selected_manifest_payload = json.load(handle)
        state_payload = load_state(state_manifest_path)
        changed_manifest_payload, changed_count, unchanged_count = filter_changed_manifest(selected_manifest_payload, state_payload, mode_name)
        changed_manifest_path = reports_root / "pressor_manifest_changed.json"
        with changed_manifest_path.open("w", encoding="utf-8") as handle:
            json.dump(changed_manifest_payload, handle, indent=2)
        selected_manifest_path = changed_manifest_path
        selected_manifest_payload = changed_manifest_payload
        print(f"Changed assets selected: {changed_count}")
        print(f"Unchanged assets skipped before processing: {unchanged_count}")
        print("")
        if changed_count == 0:
            print("No changed assets detected. Pressor did not need to process any files.")
            print(f"State manifest: {state_manifest_path}")
            return 0

    if selected_manifest_payload is not None:
        total_files = len(selected_manifest_payload.get("items", []))
    else:
        total_files = len(encoder.scan(input_root, args.profile, recursive=recursive, auto_profile=args.auto_profile)) if input_root is not None else 0
    print_progress_header(total_files)

    if args.wwise_prep:
        settings = load_wwise_settings()
        if args.wwise_safe or args.wwise_prep:
            validate_wwise_safe_settings(settings)
        results = encoder.prep_for_wwise(
            input_root=input_root,
            output_root=effective_output_root,
            default_profile=args.profile,
            recursive=recursive,
            overwrite=args.overwrite,
            dry_run=args.dry_run,
            max_workers=args.workers,
            use_manifest=selected_manifest_path,
            compare_output_root=review_pack_root,
            prep_settings=settings,
            auto_profile=args.auto_profile,
            strict_routing=args.strict_routing,
            skip_lossy_inputs=args.skip_lossy_inputs,
            fail_on_lossy_inputs=args.fail_on_lossy_inputs,
            allow_lossy_inputs=args.allow_lossy_inputs,
            progress_callback=_progress_callback,
        )
    else:
        results = encoder.batch_encode(
            input_root=input_root,
            output_root=effective_output_root,
            default_profile=args.profile,
            recursive=recursive,
            overwrite=args.overwrite,
            dry_run=args.dry_run,
            max_workers=args.workers,
            skip_if_larger=not args.keep_larger,
            use_manifest=selected_manifest_path,
            compare_output_root=review_pack_root,
            auto_profile=args.auto_profile,
            strict_routing=args.strict_routing,
            skip_lossy_inputs=args.skip_lossy_inputs,
            fail_on_lossy_inputs=args.fail_on_lossy_inputs,
            allow_lossy_inputs=args.allow_lossy_inputs,
            progress_callback=_progress_callback,
        )


    if args.changed_only and selected_manifest_payload is not None:
        successful_sources = {str(item.source) for item in results if item.success}
        state_payload = load_state(state_manifest_path)
        state_payload = update_state_from_manifest_results(state_payload, selected_manifest_payload, successful_sources, mode_name)
        save_state(state_manifest_path, state_payload)

    if args.wwise_import_json_out or args.wwise_import_tsv_out:
        if args.wwise_safe or args.wwise_prep or getattr(args, "wwise_mode", False):
            validate_wwise_safe_settings(load_wwise_settings())
        import_payload = build_wwise_manifest(
            encoder,
            input_root,
            effective_output_root,
            args.profile,
            recursive,
            args.auto_profile,
            wwise_file,
        )
        if args.wwise_import_json_out:
            wwise_json_path = write_wwise_import_json(import_payload, Path(args.wwise_import_json_out))
            print(f"Wwise starter JSON written: {wwise_json_path}")
        if args.wwise_import_tsv_out:
            wwise_tsv_path = write_wwise_import_tsv(import_payload, Path(args.wwise_import_tsv_out))
            print(f"Wwise starter TSV written: {wwise_tsv_path}")

    report_path = save_report(results, reports_root)
    failure_path = write_failure_report(results, reports_root / "pressor_failures.json")
    run_context = {
        "pressor_version": __version__,
        "platform": platform.platform(),
        "python_version": sys.version.split()[0],
        "input_root": str(input_root),
        "output_root": str(effective_output_root),
        "auto_profile": bool(args.auto_profile),
        "wwise_prep": bool(args.wwise_prep),
        "wwise_safe": bool(args.wwise_safe),
        "wwise_mode": bool(getattr(args, "wwise_mode", False)),
        "changed_only": bool(getattr(args, "changed_only", False)),
        "strict_routing": bool(args.strict_routing),
        "skip_lossy_inputs": bool(args.skip_lossy_inputs),
        "fail_on_lossy_inputs": bool(args.fail_on_lossy_inputs),
        "dry_run": bool(args.dry_run),
    }
    jsonl_path = write_jsonl_log(build_run_records(results, run_context), reports_root / "pressor_run.jsonl")
    succeeded = sum(1 for item in results if item.success and (item.changed or not str(item.message).lower().startswith("skipped")))
    skipped = sum(1 for item in results if item.success and not item.changed and "skip" in str(item.message).lower())
    failed = sum(1 for item in results if not item.success)
    print_run_summary(
        succeeded=succeeded,
        skipped=skipped,
        failed=failed,
        output_root=str(run_root if run_root is not None else effective_output_root),
        reports_root=str(reports_root),
    )
    if run_root is not None:
        print(f"Run folder: {run_root}")
    print(encoder.summarize(results))
    print(f"CSV report: {report_path}")
    print(f"Failure report: {failure_path}")
    print(f"Structured log: {jsonl_path}")
    print(f"Log file: {log_file}")

    if getattr(args, "benchmark", False):
        benchmark_output_root = effective_output_root
        print_benchmark_summary(input_root, benchmark_output_root)

    if getattr(args, "wwise_mode", False):
        prepared_assets = sum(1 for item in results if item.success and item.changed)
        unchanged_assets = sum(1 for item in results if item.success and not item.changed and "unchanged" in str(item.message).lower())
        skipped_assets = sum(1 for item in results if item.success and not item.changed and "skip" in str(item.message).lower())
        failed_assets = sum(1 for item in results if not item.success)
        _print_wwise_summary(prepared_assets, unchanged_assets, skipped_assets, failed_assets, wwise_json_path, wwise_tsv_path, reports_root)

    return 0 if all(item.success for item in results) else 2
