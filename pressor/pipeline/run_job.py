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
from pressor.core.paths import default_output_root_for_manifest_build, normalize_path, create_run_workspace
from pressor.core.reports import write_failure_report, build_run_records, write_jsonl_log
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

    if args.wwise_import_json_out or args.wwise_import_tsv_out:
        if args.wwise_safe or args.wwise_prep:
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
            json_path = write_wwise_import_json(import_payload, Path(args.wwise_import_json_out))
            print(f"Wwise starter JSON written: {json_path}")
        if args.wwise_import_tsv_out:
            tsv_path = write_wwise_import_tsv(import_payload, Path(args.wwise_import_tsv_out))
            print(f"Wwise starter TSV written: {tsv_path}")
        if not args.wwise_prep and not args.manifest and not args.dry_run:
            return 0

    if args.manifest:
        total_files = len(manifest_payload.get("items", [])) if manifest_payload is not None else 0
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
            use_manifest=Path(args.manifest) if args.manifest else None,
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
            use_manifest=Path(args.manifest) if args.manifest else None,
            compare_output_root=review_pack_root,
            auto_profile=args.auto_profile,
            strict_routing=args.strict_routing,
            skip_lossy_inputs=args.skip_lossy_inputs,
            fail_on_lossy_inputs=args.fail_on_lossy_inputs,
            allow_lossy_inputs=args.allow_lossy_inputs,
            progress_callback=_progress_callback,
        )

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
    return 0 if all(item.success for item in results) else 2
