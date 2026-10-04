from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from aiio.audited_outcomes import run_audited_project_outcomes
from aiio.schemas import ValidationError


class AuditedProjectOutcomeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.project_root = Path(__file__).resolve().parents[2]
        cls.manual_path = (
            cls.project_root
            / "data"
            / "manual"
            / "oago_selected_infrastructure_outcomes_2024.json"
        )
        cls.manual = json.loads(cls.manual_path.read_text(encoding="utf-8"))
        cls.anchor_text = "\n".join(
            anchor["anchor_text"] for anchor in cls.manual["source_anchors"]
        )

    def _run_fixture(self, manual: dict | None = None) -> dict:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pdf_path = root / "source.pdf"
            pdf_path.write_bytes(b"fixture audit pdf")
            fixture = copy.deepcopy(manual or self.manual)
            fixture["source_content_hash"] = (
                "sha256:" + hashlib.sha256(pdf_path.read_bytes()).hexdigest()
            )
            manual_path = root / "manual.json"
            manual_path.write_text(json.dumps(fixture), encoding="utf-8")
            return run_audited_project_outcomes(
                manual_path,
                pdf_path,
                root / "outcome.json",
                root / "outcome.csv",
                source_text_override=self.anchor_text,
            )

    def test_builds_two_fail_closed_named_reference_cases(self) -> None:
        result = self._run_fixture()
        self.assertEqual(
            result["coverage_summary"]["named_completed_project_count"], 2
        )
        self.assertEqual(
            result["coverage_summary"]["completed_total_cost_case_count"], 1
        )
        self.assertEqual(
            result["coverage_summary"]["exact_day_substantial_completion_pair_count"],
            1,
        )
        self.assertFalse(
            result["publication_boundary"]["ai_attributable_effect_authorized"]
        )
        cases = {case["project_reference_id"]: case for case in result["cases"]}
        self.assertIsNone(cases["ON_LAKERIDGE_GARDENS_LTC"]["schedule_delay_days"])
        self.assertEqual(
            cases["ON_HIGHWAY_427_EXPANSION"]["schedule_delay_days"], 344
        )

    def test_rejects_scope_mismatch(self) -> None:
        manual = copy.deepcopy(self.manual)
        manual["cases"][0]["latest_or_final_cost"]["scope_id"] = "different_scope"
        with self.assertRaisesRegex(ValidationError, "different scopes"):
            self._run_fixture(manual)

    def test_rejects_day_delay_from_mixed_precision_dates(self) -> None:
        manual = copy.deepcopy(self.manual)
        manual["cases"][0]["schedule"]["computed_delay_days"] = 54
        with self.assertRaisesRegex(ValidationError, "mixed-precision"):
            self._run_fixture(manual)

    def test_rejects_missing_source_anchor(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pdf_path = root / "source.pdf"
            pdf_path.write_bytes(b"fixture audit pdf")
            manual = copy.deepcopy(self.manual)
            manual["source_content_hash"] = (
                "sha256:" + hashlib.sha256(pdf_path.read_bytes()).hexdigest()
            )
            manual_path = root / "manual.json"
            manual_path.write_text(json.dumps(manual), encoding="utf-8")
            with self.assertRaisesRegex(ValidationError, "source anchor not found"):
                run_audited_project_outcomes(
                    manual_path,
                    pdf_path,
                    root / "outcome.json",
                    root / "outcome.csv",
                    source_text_override="not the reviewed source",
                )

    def test_rejects_source_hash_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pdf_path = root / "source.pdf"
            pdf_path.write_bytes(b"wrong source")
            with self.assertRaisesRegex(ValidationError, "source PDF hash"):
                run_audited_project_outcomes(
                    self.manual_path,
                    pdf_path,
                    root / "outcome.json",
                    root / "outcome.csv",
                    source_text_override=self.anchor_text,
                )


if __name__ == "__main__":
    unittest.main()
