from __future__ import annotations
from pressor.version import __version__

import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Pressor: batch perceptual audio encoder for game assets with content-aware perceptual tuning.")
    parser.add_argument("--gui", action="store_true", help="Launch the desktop UI.")
    parser.add_argument("--version", action="version", version=f"Pressor {__version__}")
    parser.add_argument("paths", nargs="*", help="Optional files or folders dropped onto the Pressor executable to preload into the GUI.")
    parser.add_argument("--selftest", action="store_true", help="Generate sample inputs and run a local self-test.")
    parser.add_argument("--doctor", action="store_true", help="Check FFmpeg, configs, routing, and Wwise-safe readiness before a run.")
    parser.add_argument("--init", action="store_true", help="Initialize or reinitialize the default Pressor workspace.")
    parser.add_argument("--show-workspace", action="store_true", help="Print the saved Pressor workspace paths and exit.")
    parser.add_argument("--workspace-root", help="Workspace root to use with --init for non-interactive setup.")
    parser.add_argument("--keep-selftest-output", help="Optional folder where self-test artifacts will be copied for inspection.")
    parser.add_argument("--scan-only", action="store_true", help="Preview-scan audio and print chosen profile decisions without encoding.")
    parser.add_argument("--scan-report", help="Optional CSV path for scan-only results.")
    parser.add_argument("--input", help="Input folder containing source audio files.")
    parser.add_argument("--output", help="Output root for encoded runs. Pressor creates a timestamped run folder by default.")
    parser.add_argument("--run-label", help="Optional label appended to the timestamped run folder name.")
    parser.add_argument("--flat-output", action="store_true", help="Write directly into the selected output folder instead of creating a timestamped run folder.")
    parser.add_argument("--profile", default="dialogue", help="Default fallback profile name.")
    parser.add_argument("--auto-profile", action="store_true", help="Use preview scanning to classify files when no routing rule matches.")
    parser.add_argument("--strict-routing", action="store_true", help="Fail if any source file does not match a routing rule before encoding.")
    parser.add_argument("--workers", type=int, default=2, help="Maximum parallel ffmpeg workers.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing outputs.")
    parser.add_argument("--dry-run", action="store_true", help="Print planned ffmpeg actions without encoding.")
    parser.add_argument("--no-recursive", action="store_true", help="Do not scan subfolders.")
    parser.add_argument("--keep-larger", action="store_true", help="Keep encoded outputs even if they are not smaller than the source.")
    parser.add_argument("--skip-lossy-inputs", action="store_true", help="Skip files that already appear to be lossy-encoded instead of processing them again.")
    parser.add_argument("--fail-on-lossy-inputs", action="store_true", help="Fail files that already appear to be lossy-encoded instead of processing them again.")
    parser.add_argument("--allow-lossy-inputs", action="store_true", help="Allow already lossy-encoded inputs to be processed intentionally.")
    parser.add_argument("--manifest", help="Run against an existing manifest JSON.")
    parser.add_argument("--build-manifest", help="Create a manifest JSON and exit.")
    parser.add_argument("--review-pack", help="Optional folder where original and encoded review pairs will be copied side by side.")
    parser.add_argument("--benchmark", action="store_true", help="Print a measured size comparison summary after a run.")
    parser.add_argument("--changed-only", action="store_true", help="Process only assets whose source hash or selected profile has changed since the last successful run.")
    parser.add_argument("--wwise-mode", action="store_true", help="Run in a Wwise-oriented preset that enables Wwise-safe validation, import artifact generation, and CI-friendly summaries. Use --changed-only explicitly when incremental behavior is desired.")
    parser.add_argument("--wwise-prep", action="store_true", help="Prepare WAV outputs for Wwise import instead of standalone lossy outputs.")
    parser.add_argument("--wwise-safe", action="store_true", help="Enforce Wwise-safe transparency rules that reject loudness or dynamics processing before Wwise.")
    parser.add_argument("--wwise-import-json-out", help="Write a starter Wwise import JSON mapping file.")
    parser.add_argument("--wwise-import-tsv-out", help="Write a starter Wwise tab-delimited import file.")
    parser.add_argument("--ffmpeg", help="Optional path to ffmpeg executable.")
    parser.add_argument("--ffprobe", help="Optional path to ffprobe executable.")
    return parser


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    return build_parser().parse_args(argv)
