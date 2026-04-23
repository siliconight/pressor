from __future__ import annotations

from helpers import TMP, assert_contains, assert_exists, pressor_args, reset_tmp, run_cmd


def _latest_run_dir(root):
    candidates = [p for p in root.iterdir() if p.is_dir()]
    if not candidates:
        raise AssertionError(f'Expected run folder inside {root}')
    return sorted(candidates)[-1]


def test_doctor() -> None:
    result = run_cmd(pressor_args('--doctor'))
    assert_contains(result.stdout, 'Failures: 0')


def test_selftest() -> None:
    keep_dir = TMP / 'selftest_bundle'
    result = run_cmd(pressor_args('--selftest', '--keep-selftest-output', str(keep_dir)))
    output_text = result.stdout + result.stderr
    assert_contains(output_text, 'Succeeded: 5')
    assert_exists(keep_dir / 'pressor_report.csv')
    assert_exists(keep_dir / 'pressor_scan_report.csv')


def test_scan_only() -> None:
    source = TMP / 'selftest_bundle' / 'input'
    report = TMP / 'scan_report.csv'
    result = run_cmd(pressor_args('--scan-only', '--input', str(source), '--auto-profile', '--scan-report', str(report)))
    assert_contains(result.stdout + result.stderr, 'Scan report written')
    assert_exists(report)


def test_encode_and_review_pack() -> None:
    source = TMP / 'selftest_bundle' / 'input'
    output = TMP / 'encode_out'
    review = TMP / 'review_pack'
    result = run_cmd(pressor_args('--input', str(source), '--output', str(output), '--auto-profile', '--review-pack', str(review)))
    assert_contains(result.stdout + result.stderr, 'Succeeded: 5')
    run_dir = _latest_run_dir(output)
    assert_exists(run_dir / 'reports' / 'pressor_report.csv')
    assert_exists(run_dir / 'encoded')
    assert_exists(review)



def test_structured_output() -> None:
    source = TMP / 'selftest_bundle' / 'input'
    output = TMP / 'structured_out'
    result = run_cmd(pressor_args('--input', str(source), '--output', str(output), '--auto-profile', '--structured-output', '--skip-lossy-inputs'))
    output_text = result.stdout + result.stderr
    assert_contains(output_text, 'Structured output summary')
    run_dir = _latest_run_dir(output)
    assert_exists(run_dir / 'encoded')
    assert_exists(run_dir / 'skipped')
    assert_exists(run_dir / 'failed')
    assert_exists(run_dir / 'reports' / 'pressor_run.jsonl')



def test_cleanup_command() -> None:
    output = TMP / 'cleanup_out'
    runs_root = output / 'pressor_runs'
    runs_root.mkdir(parents=True, exist_ok=True)
    for name in ['2026-04-20_081500', '2026-04-21_081500', '2026-04-22_081500']:
        run_dir = runs_root / name
        run_dir.mkdir()
        (run_dir / 'marker.txt').write_text('x', encoding='utf-8')

    dry = run_cmd(pressor_args('cleanup', '--output', str(output), '--keep-last', '1', '--dry-run'))
    assert_contains(dry.stdout + dry.stderr, '[DRY RUN] Would delete')
    assert_exists(runs_root / '2026-04-20_081500')

    real = run_cmd(pressor_args('cleanup', '--output', str(output), '--keep-last', '1'))
    assert_contains(real.stdout + real.stderr, 'Deleting 2 run(s)')
    assert_exists(runs_root / '2026-04-22_081500')
    if (runs_root / '2026-04-20_081500').exists() or (runs_root / '2026-04-21_081500').exists():
        raise AssertionError('Expected old cleanup runs to be deleted')

def test_manifest_flow() -> None:
    source = TMP / 'selftest_bundle' / 'input'
    manifest = TMP / 'job.json'
    build = run_cmd(pressor_args('--build-manifest', str(manifest), '--input', str(source)))
    assert_contains(build.stdout + build.stderr, 'Manifest written')
    assert_exists(manifest)
    replay = run_cmd(pressor_args('--manifest', str(manifest)))
    assert_contains(replay.stdout + replay.stderr, 'Succeeded: 5')


def test_wwise_safe() -> None:
    source = TMP / 'selftest_bundle' / 'input'
    output = TMP / 'wwise_out'
    json_out = TMP / 'wwise_import.json'
    tsv_out = TMP / 'wwise_import.tsv'
    result = run_cmd(
        pressor_args(
            '--input', str(source), '--output', str(output), '--wwise-prep', '--wwise-safe',
            '--auto-profile', '--wwise-import-json-out', str(json_out), '--wwise-import-tsv-out', str(tsv_out)
        )
    )
    assert_contains(result.stdout + result.stderr, 'Succeeded: 5')
    assert_exists(json_out)
    assert_exists(tsv_out)


def test_strict_routing_failure() -> None:
    source = TMP / 'selftest_bundle' / 'input'
    result = run_cmd(pressor_args('--input', str(source), '--strict-routing'), expect_success=False)
    assert_contains(result.stdout + result.stderr, 'Strict routing found')


def test_nested_output_failure() -> None:
    source = TMP / 'selftest_bundle' / 'input'
    bad_output = source / 'out'
    result = run_cmd(pressor_args('--input', str(source), '--output', str(bad_output)), expect_success=False)
    assert_contains(result.stdout + result.stderr, 'Output folder must not be inside the input folder')


def main() -> None:
    reset_tmp()
    tests = [
        test_doctor,
        test_selftest,
        test_scan_only,
        test_encode_and_review_pack,
        test_structured_output,
        test_cleanup_command,
        test_manifest_flow,
        test_wwise_safe,
        test_strict_routing_failure,
        test_nested_output_failure,
    ]
    failures = []
    for test in tests:
        print(f'RUN {test.__name__}', flush=True)
        try:
            test()
            print(f'PASS {test.__name__}', flush=True)
        except Exception as exc:
            failures.append((test.__name__, exc))
            print(f'FAIL {test.__name__}: {exc}', flush=True)
    print('-' * 60, flush=True)
    if failures:
        for name, exc in failures:
            print(f'{name}: {exc}', flush=True)
        raise SystemExit(1)
    print(f'ALL SMOKE TESTS PASSED ({len(tests)} tests)', flush=True)


if __name__ == '__main__':
    main()
