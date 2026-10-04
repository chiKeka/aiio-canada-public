from __future__ import annotations

import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from aiio.ai_capex_ledger import (
    REQUIRED_FIELDS,
    build_ai_capex_announcement_ledger,
    run_ai_capex_announcement_ledger,
)
from aiio.schemas import ValidationError


ROOT = Path(__file__).resolve().parents[2]


class AiCapexAnnouncementLedgerTests(unittest.TestCase):
    def write_rows(self, path: Path, rows: list[dict[str, str]]) -> None:
        fieldnames = sorted(REQUIRED_FIELDS)
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    def row(self, project_id: str, **overrides: str) -> dict[str, str]:
        row = {field: "" for field in REQUIRED_FIELDS}
        row.update(
            {
                "project_id": project_id,
                "name": f"Project {project_id}",
                "estimated_cost_cad": "1000000000",
                "municipality": "Test County",
                "schedule_text": "2025 - 2027",
                "start_year": "2025",
                "end_year": "2027",
                "stage": "Under Construction",
                "developer": "Test Developer",
                "project_website": "https://example.test/project",
                "location_count": "1",
                "location_precision": "reported",
                "ai_relevance": "core_data_centre",
                "ai_classification_basis": "controlled vocabulary",
                "source_id": "ALBERTA_MAJOR_PROJECTS",
                "source_evidence_status": "observed",
                "classification_evidence_status": "inferred",
                "as_of_date": "2026-08-31",
            }
        )
        row.update(overrides)
        return row

    def test_builds_partial_announcement_aggregate_without_treatment(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "projects.csv"
            self.write_rows(
                source,
                [
                    self.row("ABMP_1"),
                    self.row(
                        "ABMP_2",
                        ai_relevance="enabling_power",
                        estimated_cost_cad="",
                        schedule_text="Completion by 2030",
                        start_year="",
                        end_year="2030",
                        stage="Proposed",
                    ),
                ],
            )
            result = build_ai_capex_announcement_ledger(source)

        coverage = result["coverage_summary"]
        self.assertEqual(result["record_count"], 2)
        self.assertEqual(coverage["reported_estimated_cost_record_count"], 1)
        self.assertEqual(coverage["known_reported_estimated_cost_cad"], 1_000_000_000)
        self.assertEqual(coverage["publisher_construction_stage_candidate_count"], 1)
        self.assertEqual(coverage["authorizing_treatment_onset_count"], 0)
        self.assertEqual(coverage["authorizing_treatment_dose_count"], 0)
        self.assertTrue(result["aggregation_controls"]["missing_costs_are_not_zero"])
        self.assertFalse(
            result["aggregation_controls"]["probability_or_stage_weighting_applied"]
        )
        self.assertFalse(
            result["treatment_requirement_assessment"]["authorizing_treatment_present"]
        )

    def test_committed_ledger_is_reproducible_and_fail_closed(self) -> None:
        source = ROOT / "data/processed/alberta_ai_projects.csv"
        committed_path = (
            ROOT / "data/model-runs/alberta_ai_capex_announcement_ledger_v0.1.json"
        )
        with tempfile.TemporaryDirectory() as directory:
            regenerated_path = Path(directory) / "ledger.json"
            run_ai_capex_announcement_ledger(source, regenerated_path)
            regenerated = json.loads(regenerated_path.read_text(encoding="utf-8"))
        committed = json.loads(committed_path.read_text(encoding="utf-8"))

        self.assertEqual(regenerated, committed)
        self.assertEqual(
            committed["input_sha256"], hashlib.sha256(source.read_bytes()).hexdigest()
        )
        self.assertEqual(committed["record_count"], 22)
        self.assertEqual(
            committed["coverage_summary"]["core_data_centre_record_count"], 19
        )
        self.assertEqual(
            committed["coverage_summary"]["enabling_power_record_count"], 3
        )
        self.assertEqual(
            committed["coverage_summary"]["known_core_reported_estimated_cost_cad"],
            49_010_000_000,
        )
        self.assertEqual(
            committed["coverage_summary"]["known_enabling_reported_estimated_cost_cad"],
            6_400_000_000,
        )
        boundary = committed["publication_boundary"]
        self.assertTrue(boundary["descriptive_announcement_ledger_authorized"])
        self.assertTrue(boundary["partial_known_reported_cost_aggregate_authorized"])
        self.assertFalse(boundary["committed_investment_claim_authorized"])
        self.assertFalse(boundary["realized_construction_treatment_authorized"])
        self.assertFalse(boundary["probability_weighted_pipeline_authorized"])
        self.assertFalse(boundary["future_spend_forecast_authorized"])
        self.assertFalse(boundary["ai_attributable_effect_authorized"])
        self.assertTrue(
            all(
                item["realized_construction_start_date"] is None
                and item["realized_construction_spend_cad"] is None
                and not item["authorizing_treatment_onset_available"]
                and not item["authorizing_treatment_dose_available"]
                for item in committed["records"]
            )
        )

    def test_rejects_duplicate_ids_source_drift_and_invalid_schedule(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "projects.csv"
            self.write_rows(source, [self.row("ABMP_1"), self.row("ABMP_1")])
            with self.assertRaisesRegex(ValidationError, "duplicate project IDs"):
                build_ai_capex_announcement_ledger(source)

            self.write_rows(
                source,
                [self.row("ABMP_1", source_id="UNREGISTERED_SOURCE")],
            )
            with self.assertRaisesRegex(ValidationError, "source lineage changed"):
                build_ai_capex_announcement_ledger(source)

            self.write_rows(
                source,
                [self.row("ABMP_1", start_year="2030", end_year="2028")],
            )
            with self.assertRaisesRegex(ValidationError, "ends before it starts"):
                build_ai_capex_announcement_ledger(source)


if __name__ == "__main__":
    unittest.main()
