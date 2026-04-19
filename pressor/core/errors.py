from __future__ import annotations

from typing import Dict


def _tail(text: str, lines: int = 8) -> str:
    cleaned = (text or '').strip()
    if not cleaned:
        return ''
    parts = cleaned.splitlines()
    return '\n'.join(parts[-lines:])


def infer_error_details(stage: str, message: str, stderr: str = '', input_is_lossy: bool = False) -> Dict[str, str]:
    text = f"{message}\n{stderr}".lower()
    stderr_tail = _tail(stderr or message)

    if input_is_lossy and ('rejected lossy input' in text or 'skipped lossy input' in text):
        return {
            'error_code': 'P1501',
            'error_category': 'user_config',
            'likely_cause': 'Input appears to already be perceptually encoded.',
            'suggested_action': 'Use original source-quality audio or disable the lossy-input guardrail intentionally.',
            'stderr_tail': stderr_tail,
        }

    if 'directory not found' in text or 'input folder is required' in text or 'input file not found' in text or 'source file not found' in text:
        return {
            'error_code': 'P1001',
            'error_category': 'user_config',
            'likely_cause': 'Input path is missing or the source file no longer exists.',
            'suggested_action': 'Check the input path and confirm the source file still exists.',
            'stderr_tail': stderr_tail,
        }
    if 'must not be inside the input folder' in text:
        return {
            'error_code': 'P1002',
            'error_category': 'user_config',
            'likely_cause': 'Output or review-pack path is nested inside the input folder.',
            'suggested_action': 'Move the output or review-pack folder outside the input folder.',
            'stderr_tail': stderr_tail,
        }
    if 'file not found' in text and ('ffmpeg' in text or 'ffprobe' in text):
        return {
            'error_code': 'P1101',
            'error_category': 'environment',
            'likely_cause': 'FFmpeg or FFprobe is not installed or not on PATH.',
            'suggested_action': 'Install FFmpeg and confirm ffmpeg and ffprobe are available on PATH, then run --doctor.',
            'stderr_tail': stderr_tail,
        }
    if 'permission denied' in text:
        return {
            'error_code': 'P1102',
            'error_category': 'environment',
            'likely_cause': 'Pressor could not read the source or write the output.',
            'suggested_action': 'Check file permissions and ensure the output folder is writable.',
            'stderr_tail': stderr_tail,
        }
    if 'timed out' in text:
        return {
            'error_code': 'P1303',
            'error_category': 'runtime_processing',
            'likely_cause': 'FFmpeg stalled on the source file or the machine was overloaded.',
            'suggested_action': 'Inspect the source file and try again with fewer workers.',
            'stderr_tail': stderr_tail,
        }
    if 'invalid argument' in text:
        return {
            'error_code': 'P1301',
            'error_category': 'runtime_processing',
            'likely_cause': 'FFmpeg rejected the source or one of the encode arguments.',
            'suggested_action': 'Re-run with the same file, inspect the source with ffprobe, and review the generated command.',
            'stderr_tail': stderr_tail,
        }
    if 'temp output was not created' in text or 'output file is empty' in text:
        return {
            'error_code': 'P1302',
            'error_category': 'runtime_processing',
            'likely_cause': 'Encoding did not produce a valid output file.',
            'suggested_action': 'Inspect the FFmpeg stderr output and verify the source file is decodable.',
            'stderr_tail': stderr_tail,
        }
    if 'manifest' in text:
        return {
            'error_code': 'P1401',
            'error_category': 'user_config',
            'likely_cause': 'The manifest is missing required fields or contains invalid paths or profiles.',
            'suggested_action': 'Rebuild the manifest from a known-good input folder and try again.',
            'stderr_tail': stderr_tail,
        }
    if stage in {'encode', 'wwise_prep'}:
        return {
            'error_code': 'P1301',
            'error_category': 'runtime_processing',
            'likely_cause': 'The encode or Wwise prep step failed while processing this file.',
            'suggested_action': 'Inspect the source file, review the command and stderr, and retry on the single file.',
            'stderr_tail': stderr_tail,
        }
    return {
        'error_code': 'P9001',
        'error_category': 'internal_bug',
        'likely_cause': 'An unexpected internal error occurred.',
        'suggested_action': 'Re-run with the same input, capture the logs, and inspect the traceback.',
        'stderr_tail': stderr_tail,
    }
