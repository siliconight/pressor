
from types import SimpleNamespace
import unittest
from pathlib import Path
from unittest.mock import patch

from pressor.pipeline.run_job import run_encode_job


class WwiseModeBehaviorTests(unittest.TestCase):
    def test_wwise_mode_does_not_force_changed_only(self):
        args = SimpleNamespace(
            skip_lossy_inputs=False,
            fail_on_lossy_inputs=False,
            allow_lossy_inputs=False,
            wwise_mode=True,
            changed_only=False,
            manifest=None,
            no_recursive=False,
            input=".",
            output=".",
            scan_only=False,
            build_manifest=None,
            review_pack=None,
            strict_routing=False,
            auto_profile=False,
            profile="dialogue",
            wwise_import_json_out=None,
            wwise_import_tsv_out=None,
            wwise_safe=False,
            wwise_prep=False,
            overwrite=False,
            dry_run=True,
            workers=1,
            keep_larger=False,
            benchmark=False,
            run_label=None,
            flat_output=True,
        )

        class DummyEncoder:
            def scan(self, *args, **kwargs):
                return []
            def batch_encode(self, **kwargs):
                return []
            def summarize(self, results):
                return "summary"

        def save_report(results, reports_root):
            return reports_root / "pressor_report.csv"

        def save_scan_report(*args, **kwargs):
            return Path("scan.csv")

        def save_strict_routing_report(*args, **kwargs):
            return Path("strict.csv")

        def load_wwise_settings():
            return {}

        def validate_wwise_safe_settings(settings):
            return None

        with patch("pressor.pipeline.run_job.write_failure_report", return_value=Path("failures.json")),              patch("pressor.pipeline.run_job.write_jsonl_log", return_value=Path("run.jsonl")),              patch("pressor.pipeline.run_job.build_run_records", return_value=[]),              patch("pressor.pipeline.run_job.normalize_review_pack_path", return_value=None),              patch("pressor.pipeline.run_job.validate_review_pack_relationships", return_value=None),              patch("pressor.pipeline.run_job.build_wwise_manifest", return_value={"items": []}),              patch("pressor.pipeline.run_job.write_wwise_import_json", return_value=Path("wwise_import.json")),              patch("pressor.pipeline.run_job.write_wwise_import_tsv", return_value=Path("wwise_import.tsv")),              patch("pressor.pipeline.run_job.create_run_workspace") as mock_workspace:
            mock_workspace.return_value = SimpleNamespace(
                run_root=Path("."),
                encoded_root=Path("."),
                reports_root=Path("."),
                review_root=Path("review"),
            )
            run_encode_job(
                args,
                DummyEncoder(),
                save_report,
                save_scan_report,
                save_strict_routing_report,
                load_wwise_settings,
                validate_wwise_safe_settings,
                Path("wwise.json"),
                Path("log.txt"),
            )

        self.assertFalse(args.changed_only)
        self.assertTrue(args.wwise_safe)
