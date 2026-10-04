from __future__ import annotations

import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from aiio.adapters.canadabuys import (
    AMENDMENT,
    AMENDMENT_TYPE,
    AWARD_DATE,
    AWARD_REQUIRED_FIELDS,
    CATEGORY,
    CONTRACT_AMOUNT,
    CONTRACT_END,
    CONTRACT_NUMBER,
    CONTRACT_REQUIRED_FIELDS,
    CONTRACT_START,
    CURRENCY,
    PUBLICATION_DATE,
    REFERENCE,
    REGION,
    SOLICITATION,
    TENDER_CLOSE,
    TENDER_REQUIRED_FIELDS,
    TENDER_STATUS,
    TITLE,
    TOTAL_CONTRACT_VALUE,
    normalize_canadabuys_outcome_intake,
)
from aiio.schemas import ValidationError


class CanadaBuysOutcomeIntakeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)
        self.tender_path = self.root / "tender.csv"
        self.award_path = self.root / "award.csv"
        self.contract_path = self.root / "contract.csv"
        self.output_path = self.root / "output.csv"
        self.report_path = self.root / "report.json"

    def write_inputs(self) -> None:
        self.write_csv(
            self.tender_path,
            TENDER_REQUIRED_FIELDS,
            [
                {
                    TITLE: "Alberta laboratory renewal",
                    REFERENCE: "T-1",
                    AMENDMENT: "000",
                    SOLICITATION: "SOL-1",
                    PUBLICATION_DATE: "2026-04-01",
                    TENDER_CLOSE: "2026-04-21T14:00:00",
                    TENDER_STATUS: "Expired",
                    CATEGORY: "*CNST",
                    REGION: "*Alberta",
                },
                {
                    TITLE: "Office supplies",
                    REFERENCE: "T-2",
                    AMENDMENT: "000",
                    SOLICITATION: "SOL-2",
                    PUBLICATION_DATE: "2026-04-02",
                    TENDER_CLOSE: "2026-04-22",
                    TENDER_STATUS: "Expired",
                    CATEGORY: "*GD",
                    REGION: "*Alberta",
                },
            ],
        )
        self.write_csv(
            self.award_path,
            AWARD_REQUIRED_FIELDS,
            [
                {
                    TITLE: "Alberta laboratory renewal",
                    REFERENCE: "A-1",
                    AMENDMENT: "000",
                    SOLICITATION: "SOL-1",
                    CONTRACT_NUMBER: "C-1",
                    PUBLICATION_DATE: "2026-05-02",
                    AWARD_DATE: "2026-05-01",
                    CONTRACT_START: "2026-05-15",
                    CONTRACT_END: "2027-05-15",
                    CONTRACT_AMOUNT: "1000000.00",
                    TOTAL_CONTRACT_VALUE: "1000000.00",
                    CURRENCY: "CAD",
                    CATEGORY: "*CNST",
                    REGION: "*Alberta",
                }
            ],
        )
        self.write_csv(
            self.contract_path,
            CONTRACT_REQUIRED_FIELDS,
            [
                {
                    TITLE: "Alberta laboratory renewal",
                    REFERENCE: "C-1-ORIGINAL",
                    AMENDMENT: "000",
                    SOLICITATION: "SOL-1",
                    CONTRACT_NUMBER: "C-1",
                    PUBLICATION_DATE: "2026-05-02",
                    AWARD_DATE: "2026-05-01",
                    CONTRACT_START: "2026-05-15",
                    CONTRACT_END: "2027-05-15",
                    CONTRACT_AMOUNT: "1000000.00",
                    TOTAL_CONTRACT_VALUE: "1000000.00",
                    CURRENCY: "CAD",
                    CATEGORY: "*CNST",
                    REGION: "*Alberta",
                    AMENDMENT_TYPE: "Original",
                },
                {
                    TITLE: "Alberta laboratory renewal",
                    REFERENCE: "C-1-AMENDMENT",
                    AMENDMENT: "001",
                    SOLICITATION: "SOL-1",
                    CONTRACT_NUMBER: "C-1",
                    PUBLICATION_DATE: "2026-06-02",
                    AWARD_DATE: "2026-05-01",
                    CONTRACT_START: "2026-05-15",
                    CONTRACT_END: "2027-06-15",
                    CONTRACT_AMOUNT: "250000.00",
                    TOTAL_CONTRACT_VALUE: "1250000.00",
                    CURRENCY: "CAD",
                    CATEGORY: "*CNST",
                    REGION: "*Alberta",
                    AMENDMENT_TYPE: "Amendment",
                },
            ],
        )

    def test_builds_fail_closed_procurement_linkage(self) -> None:
        self.write_inputs()
        report = normalize_canadabuys_outcome_intake(
            self.tender_path,
            self.award_path,
            self.contract_path,
            self.output_path,
            self.report_path,
        )
        with self.output_path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["geography_id"], "PR_48")
        self.assertEqual(row["tender_duration_days"], "20")
        self.assertEqual(row["reported_award_value_cad"], "1000000.00")
        self.assertEqual(row["reported_total_contract_value_cad"], "1250000.00")
        self.assertEqual(row["contract_amendment_row_count"], "1")
        self.assertEqual(row["physical_project_id"], "")
        self.assertEqual(row["compliant_bidder_count"], "")
        self.assertEqual(row["cost_outcome_status"], "missing_required_fields")
        self.assertFalse(
            report["publication_boundary"]["public_project_cost_outcome_authorized"]
        )
        self.assertFalse(
            report["publication_boundary"]["ai_attributable_effect_authorized"]
        )
        self.assertEqual(report["construction_linkage_count"], 1)

    def test_rejects_schema_drift(self) -> None:
        self.write_inputs()
        fieldnames = sorted(TENDER_REQUIRED_FIELDS - {REGION})
        self.write_csv(self.tender_path, set(fieldnames), [{field: "x" for field in fieldnames}])
        with self.assertRaisesRegex(ValidationError, "schema changed"):
            normalize_canadabuys_outcome_intake(
                self.tender_path,
                self.award_path,
                self.contract_path,
                self.output_path,
                self.report_path,
            )

    def test_report_written_is_json_and_hash_locked(self) -> None:
        self.write_inputs()
        normalize_canadabuys_outcome_intake(
            self.tender_path,
            self.award_path,
            self.contract_path,
            self.output_path,
            self.report_path,
        )
        report = json.loads(self.report_path.read_text(encoding="utf-8"))
        self.assertEqual(report["cma_geography_count"], 0)
        self.assertEqual(report["field_availability"]["compliant_bidder_count"], 0)
        self.assertTrue(report["output_sha256"].startswith("sha256:"))

    def test_committed_feasibility_artifact_is_hash_locked_and_fail_closed(self) -> None:
        project_root = Path(__file__).resolve().parents[2]
        output_path = (
            project_root
            / "data"
            / "processed"
            / "canadabuys_construction_outcome_feasibility.csv"
        )
        report = json.loads(
            (
                project_root
                / "data"
                / "model-runs"
                / "canadabuys_construction_outcome_feasibility_v0.1.json"
            ).read_text(encoding="utf-8")
        )
        output_hash = "sha256:" + hashlib.sha256(output_path.read_bytes()).hexdigest()
        self.assertEqual(output_hash, report["output_sha256"])
        self.assertEqual(report["construction_linkage_count"], 358)
        self.assertEqual(report["linked_tender_award_count"], 89)
        self.assertEqual(report["linked_tender_contract_count"], 47)
        self.assertEqual(report["cma_geography_count"], 0)
        self.assertEqual(report["field_availability"]["compliant_bidder_count"], 0)
        self.assertFalse(
            report["publication_boundary"]["public_project_cost_outcome_authorized"]
        )
        self.assertFalse(
            report["publication_boundary"]["ai_attributable_effect_authorized"]
        )
        with output_path.open(encoding="utf-8", newline="") as handle:
            fieldnames = set(csv.DictReader(handle).fieldnames or ())
        self.assertFalse(
            fieldnames
            & {
                "contact_name",
                "contact_email",
                "contact_phone",
                "supplier_address",
                "tender_description",
            }
        )

    @staticmethod
    def write_csv(
        path: Path, fieldnames: set[str], rows: list[dict[str, str]]
    ) -> None:
        ordered_fields = sorted(fieldnames)
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=ordered_fields)
            writer.writeheader()
            for row in rows:
                writer.writerow({field: row.get(field, "") for field in ordered_fields})


if __name__ == "__main__":
    unittest.main()
