from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from aiio.public_projects import (
    classify_asset_class,
    classify_sponsor_signal,
    run_public_project_exposure,
    schedule_overlap,
)


FIELDS = [
    "project_id",
    "name",
    "estimated_cost_cad",
    "municipality",
    "start_year",
    "end_year",
    "sector",
    "project_type",
    "stage",
    "developer",
    "longitude",
    "latitude",
    "location_precision",
    "ai_relevance",
    "source_id",
    "source_evidence_status",
    "as_of_date",
]


class PublicProjectExposureTests(unittest.TestCase):
    def test_taxonomy_and_sponsor_are_explicit_inferences(self) -> None:
        self.assertEqual(
            classify_asset_class("Health Care", "Institutional"),
            "health_facilities",
        )
        self.assertEqual(
            classify_asset_class("Solar", "Power"), "power_sector_infrastructure"
        )
        self.assertIsNone(classify_asset_class("Apartment: Low-Rise", "Residential"))
        self.assertEqual(
            classify_sponsor_signal("Alberta Infrastructure"),
            "government_or_public_institution_signal",
        )
        self.assertEqual(
            classify_sponsor_signal("EPCOR"),
            "municipal_or_public_utility_signal",
        )
        self.assertEqual(classify_sponsor_signal("Private Developer Inc."), "unresolved")

    def test_schedule_overlap_keeps_incomplete_dates_indeterminate(self) -> None:
        self.assertEqual(schedule_overlap(2026, 2028, 2027, 2036), ("overlaps", [2027, 2028]))
        self.assertEqual(schedule_overlap(None, 2026, 2027, 2036), ("outside_window", []))
        self.assertEqual(
            schedule_overlap(2029, None, 2027, 2036),
            ("indeterminate_incomplete_schedule", []),
        )

    def test_exposure_annualizes_only_complete_costed_schedules(self) -> None:
        rows = [
            {
                "project_id": "ABMP_1",
                "name": "Hospital",
                "estimated_cost_cad": "300",
                "municipality": "Edmonton",
                "start_year": "2027",
                "end_year": "2029",
                "sector": "Institutional",
                "project_type": "Health Care",
                "stage": "Proposed",
                "developer": "Alberta Infrastructure",
                "longitude": "-113.5",
                "latitude": "53.5",
                "location_precision": "reported",
                "ai_relevance": "none",
                "source_id": "ALBERTA_MAJOR_PROJECTS",
                "source_evidence_status": "observed",
                "as_of_date": "2026-08-31",
            },
            {
                "project_id": "ABMP_2",
                "name": "School with unknown start",
                "estimated_cost_cad": "100",
                "municipality": "Calgary",
                "start_year": "",
                "end_year": "2030",
                "sector": "Institutional",
                "project_type": "School",
                "stage": "Proposed",
                "developer": "Alberta Infrastructure",
                "longitude": "",
                "latitude": "",
                "location_precision": "reported",
                "ai_relevance": "none",
                "source_id": "ALBERTA_MAJOR_PROJECTS",
                "source_evidence_status": "observed",
                "as_of_date": "2026-08-31",
            },
            {
                "project_id": "ABMP_3",
                "name": "AI power project",
                "estimated_cost_cad": "999",
                "municipality": "Calgary",
                "start_year": "2027",
                "end_year": "2028",
                "sector": "Power",
                "project_type": "Other Power",
                "stage": "Proposed",
                "developer": "Private",
                "longitude": "",
                "latitude": "",
                "location_precision": "reported",
                "ai_relevance": "enabling_power",
                "source_id": "ALBERTA_MAJOR_PROJECTS",
                "source_evidence_status": "observed",
                "as_of_date": "2026-08-31",
            },
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "projects.csv"
            with source.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=FIELDS)
                writer.writeheader()
                writer.writerows(rows)
            result = run_public_project_exposure(
                source, root / "exposure.json", root / "exposure.csv"
            )
        self.assertEqual(result["screened_project_count"], 2)
        hospital = next(item for item in result["projects"] if item["project_id"] == "ABMP_1")
        school = next(item for item in result["projects"] if item["project_id"] == "ABMP_2")
        self.assertEqual(hospital["annualized_cost_cad_if_complete"], 100)
        self.assertEqual(hospital["indicative_cost_allocated_to_window_cad"], 300)
        self.assertIsNone(school["annualized_cost_cad_if_complete"])
        self.assertEqual(school["schedule_overlap_status"], "indeterminate_incomplete_schedule")
        health_summary = next(
            item
            for item in result["asset_class_summaries"]
            if item["asset_class"] == "health_facilities"
        )
        self.assertEqual(health_summary["indicative_cost_allocated_to_window_cad"], 300)
        self.assertEqual(health_summary["unresolved_sponsor_signal_count"], 0)


if __name__ == "__main__":
    unittest.main()
