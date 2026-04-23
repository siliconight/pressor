from __future__ import annotations

import csv
import json
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any


def write_encode_report(results: List[object], report_path: Path) -> Path:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.writer(handle)
        writer.writerow([
            'source', 'destination', 'profile', 'profile_source', 'profile_confidence', 'profile_reasons',
            'perceptual_risk', 'perceptual_score', 'applied_bitrate', 'applied_sample_rate', 'applied_channels',
            'input_is_lossy', 'input_lossy_reason',
            'success', 'changed', 'original_size', 'output_size', 'bytes_saved', 'message',
            'stage', 'error_code', 'error_category', 'likely_cause', 'suggested_action', 'ffmpeg_exit_code', 'stderr_tail', 'command'
        ])
        for item in results:
            writer.writerow([
                str(item.source),
                str(item.destination) if getattr(item, 'destination', None) else '',
                item.profile,
                item.profile_source,
                item.profile_confidence,
                ' | '.join(getattr(item, 'profile_reasons', []) or []),
                item.perceptual_risk,
                item.perceptual_score,
                item.applied_bitrate,
                item.applied_sample_rate,
                item.applied_channels,
                getattr(item, 'input_is_lossy', False),
                getattr(item, 'input_lossy_reason', ''),
                item.success,
                item.changed,
                item.original_size,
                item.output_size,
                item.bytes_saved,
                item.message,
                getattr(item, 'stage', ''),
                getattr(item, 'error_code', ''),
                getattr(item, 'error_category', ''),
                getattr(item, 'likely_cause', ''),
                getattr(item, 'suggested_action', ''),
                getattr(item, 'ffmpeg_exit_code', ''),
                getattr(item, 'stderr_tail', ''),
                getattr(item, 'command', ''),
            ])
    return report_path


def build_run_summary(results: List[object]) -> str:
    total = len(results)
    success = sum(1 for item in results if item.success)
    changed = sum(1 for item in results if item.changed)
    failed = total - success
    original = sum(item.original_size for item in results)
    written = sum(item.output_size for item in results if item.changed)
    saved = sum(item.bytes_saved for item in results)
    pct = (saved / original * 100.0) if original else 0.0
    auto_count = sum(1 for item in results if item.profile_source == 'auto-preview')
    return (
        f'Files seen: {total}\n'
        f'Succeeded: {success}\n'
        f'Changed: {changed}\n'
        f'Failed: {failed}\n'
        f'Auto-profiled: {auto_count}\n'
        f'Original bytes: {original}\n'
        f'Output bytes: {written}\n'
        f'Bytes saved: {saved}\n'
        f'Savings: {pct:.2f}%'
    )


def write_scan_report(scan_results: List[Dict[str, object]], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        'relative_path', 'source', 'channels', 'sample_rate', 'duration', 'bit_rate', 'codec_name', 'format_name',
        'input_is_lossy', 'input_lossy_reason',
        'chosen_profile', 'profile_source', 'profile_confidence', 'profile_reasons',
        'preview_silence_ratio', 'preview_energy_mean', 'preview_energy_std', 'preview_zcr', 'preview_brightness', 'preview_transient_density',
        'perceptual_score', 'perceptual_risk', 'perceptual_recommendation', 'perceptual_bitrate', 'perceptual_reasons',
    ]
    with output_path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for item in scan_results:
            row = dict(item)
            row['profile_reasons'] = ' | '.join(row.get('profile_reasons', []))
            writer.writerow({name: row.get(name, '') for name in fieldnames})
    return output_path


def write_strict_routing_report(issues: List[Dict[str, object]], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ['relative_path', 'source', 'chosen_profile', 'profile_source', 'profile_confidence', 'profile_reasons']
    with output_path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for item in issues:
            row = dict(item)
            row['profile_reasons'] = ' | '.join(row.get('profile_reasons', []))
            writer.writerow({name: row.get(name, '') for name in fieldnames})
    return output_path


def write_failure_report(results: List[object], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    failures = []
    for item in results:
        if getattr(item, 'success', False):
            continue
        if is_dataclass(item):
            payload = asdict(item)
        else:
            payload = dict(item)
        payload['source'] = str(payload.get('source', ''))
        if payload.get('destination') is not None:
            payload['destination'] = str(payload.get('destination', ''))
        failures.append(payload)
    with output_path.open('w', encoding='utf-8') as handle:
        json.dump({'generated_at': datetime.now(timezone.utc).isoformat(), 'failures': failures}, handle, indent=2)
    return output_path




def write_rejected_report(rejected_inputs: List[Dict[str, Any]], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open('w', encoding='utf-8') as handle:
        json.dump({'generated_at': datetime.now(timezone.utc).isoformat(), 'rejected_inputs': rejected_inputs}, handle, indent=2)
    return output_path

def write_jsonl_log(records: List[Dict[str, Any]], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open('w', encoding='utf-8') as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + '\n')
    return output_path


def build_run_records(results: List[object], run_context: Dict[str, Any]) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    for item in results:
        payload = asdict(item) if is_dataclass(item) else dict(item)
        payload['source'] = str(payload.get('source', ''))
        if payload.get('destination') is not None:
            payload['destination'] = str(payload.get('destination', ''))
        payload['timestamp'] = datetime.now(timezone.utc).isoformat()
        payload['run_context'] = dict(run_context)
        records.append(payload)
    return records
