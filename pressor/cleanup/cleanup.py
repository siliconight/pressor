from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
import shutil


def get_folder_size(path: Path) -> int:
    total = 0
    for p in path.rglob("*"):
        if p.is_file():
            try:
                total += p.stat().st_size
            except OSError:
                continue
    return total


def _parse_run_timestamp(path: Path) -> datetime | None:
    try:
        return datetime.strptime(path.name, "%Y-%m-%d_%H%M%S")
    except ValueError:
        return None


def run_cleanup(args) -> int:
    output = Path(args.output)
    runs_root = output / "pressor_runs"

    if not runs_root.exists():
        print("No pressor_runs folder found.")
        return 0

    runs = [p for p in runs_root.iterdir() if p.is_dir()]
    runs.sort(key=lambda p: p.name, reverse=True)

    to_delete: set[Path] = set()

    if args.keep_last is not None and args.keep_last < 0:
        raise ValueError("--keep-last must be 0 or greater")
    if args.older_than_days is not None and args.older_than_days < 0:
        raise ValueError("--older-than-days must be 0 or greater")

    if args.keep_last is not None:
        to_delete.update(runs[args.keep_last:])

    if args.older_than_days is not None:
        cutoff = datetime.now() - timedelta(days=args.older_than_days)
        for run in runs:
            ts = _parse_run_timestamp(run)
            if ts is not None and ts < cutoff:
                to_delete.add(run)

    ordered_delete = sorted(to_delete, key=lambda p: p.name)

    print(f"Found {len(runs)} Pressor run folder(s)")
    if args.keep_last is not None:
        print(f"Keeping newest {args.keep_last} run(s)")
    if args.older_than_days is not None:
        print(f"Deleting run folders older than {args.older_than_days} day(s)")
    print(f"Deleting {len(ordered_delete)} run(s)")

    if args.dry_run:
        for run in ordered_delete:
            print(f"[DRY RUN] Would delete: {run}")
        return 0

    deleted_size = 0
    for run in ordered_delete:
        deleted_size += get_folder_size(run)
        shutil.rmtree(run)
        if args.verbose:
            print(f"Deleted: {run}")

    print(f"Recovered {deleted_size / (1024**3):.2f} GB")
    return 0
