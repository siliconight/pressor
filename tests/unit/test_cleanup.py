from __future__ import annotations

from datetime import datetime, timedelta
from types import SimpleNamespace

from pressor.cleanup.cleanup import run_cleanup


def _make_run(root, dt):
    run = root / dt.strftime("%Y-%m-%d_%H%M%S")
    run.mkdir(parents=True, exist_ok=True)
    (run / "marker.txt").write_text("x", encoding="utf-8")
    return run


def test_cleanup_keep_last(tmp_path, capsys):
    out = tmp_path / "out" / "pressor_runs"
    now = datetime.now()
    old = _make_run(out, now - timedelta(days=3))
    mid = _make_run(out, now - timedelta(days=2))
    new = _make_run(out, now - timedelta(days=1))

    rc = run_cleanup(SimpleNamespace(output=str(tmp_path / "out"), keep_last=2, older_than_days=None, dry_run=False, verbose=False))
    assert rc == 0
    assert not old.exists()
    assert mid.exists()
    assert new.exists()
    assert "Deleting 1 run(s)" in capsys.readouterr().out


def test_cleanup_older_than_days(tmp_path):
    out = tmp_path / "out" / "pressor_runs"
    now = datetime.now()
    old = _make_run(out, now - timedelta(days=5))
    new = _make_run(out, now - timedelta(hours=12))

    rc = run_cleanup(SimpleNamespace(output=str(tmp_path / "out"), keep_last=None, older_than_days=2, dry_run=False, verbose=False))
    assert rc == 0
    assert not old.exists()
    assert new.exists()


def test_cleanup_dry_run(tmp_path, capsys):
    out = tmp_path / "out" / "pressor_runs"
    now = datetime.now()
    old = _make_run(out, now - timedelta(days=5))

    rc = run_cleanup(SimpleNamespace(output=str(tmp_path / "out"), keep_last=0, older_than_days=None, dry_run=True, verbose=False))
    assert rc == 0
    assert old.exists()
    assert "[DRY RUN] Would delete" in capsys.readouterr().out


def test_cleanup_ignores_non_timestamp_dirs(tmp_path):
    out = tmp_path / "out" / "pressor_runs"
    out.mkdir(parents=True, exist_ok=True)
    weird = out / "manual_notes"
    weird.mkdir()
    (weird / "keep.txt").write_text("x", encoding="utf-8")

    rc = run_cleanup(SimpleNamespace(output=str(tmp_path / "out"), keep_last=None, older_than_days=1, dry_run=False, verbose=False))
    assert rc == 0
    assert weird.exists()


def test_cleanup_empty_missing_root(tmp_path, capsys):
    rc = run_cleanup(SimpleNamespace(output=str(tmp_path / "out"), keep_last=5, older_than_days=None, dry_run=False, verbose=False))
    assert rc == 0
    assert "No pressor_runs folder found." in capsys.readouterr().out
