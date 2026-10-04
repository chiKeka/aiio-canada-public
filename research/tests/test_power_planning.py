from __future__ import annotations

import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from aiio.power_planning import run_provincial_power_planning_contract
from aiio.schemas import ValidationError


ROOT = Path(__file__).resolve().parents[2]
EXTRACT = ROOT / "data" / "manual" / "provincial_power_planning_extract_2026_09.json"
EXPECTED_JSON = (
    ROOT / "data" / "model-runs" / "provincial_power_planning_contract_v0.1.json"
)
EXPECTED_CSV = ROOT / "data" / "processed" / "provincial_power_planning_metrics.csv"


class ProvincialPowerPlanningContractTests(unittest.TestCase):
    def _run_raw(self, raw: dict) -> dict:
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            extract = temp / "extract.json"
            extract.write_text(json.dumps(raw), encoding="utf-8")
            return run_provincial_power_planning_contract(
                extract,
                ROOT,
                temp / "result.json",
                temp / "metrics.csv",
            )

    def test_committed_artifacts_are_reproducible_and_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            result_path = temp / "result.json"
            csv_path = temp / "metrics.csv"
            result = run_provincial_power_planning_contract(
                EXTRACT, ROOT, result_path, csv_path
            )

            self.assertEqual(result, json.loads(EXPECTED_JSON.read_text(encoding="utf-8")))
            self.assertEqual(csv_path.read_bytes(), EXPECTED_CSV.read_bytes())
            self.assertEqual(result["source_count"], 5)
            self.assertEqual(result["metric_count"], 47)
            self.assertEqual(result["transmission_action_count"], 4)
            self.assertFalse(
                result["publication_boundary"]["provincial_power_profile_authorized"]
            )
            self.assertFalse(
                result["publication_boundary"]["transmission_requirement_authorized"]
            )

    def test_xlsx_locator_is_checked_against_source_cell(self) -> None:
        raw = json.loads(EXTRACT.read_text(encoding="utf-8"))
        changed = deepcopy(raw)
        metric = next(
            item
            for item in changed["metrics"]
            if item["metric_id"] == "ON_SYSTEM_ENERGY_REF_2026"
        )
        metric["value"] = 152.47
        with self.assertRaisesRegex(ValidationError, "does not match Figure 1!B7"):
            self._run_raw(changed)

    def test_incompatible_unit_contract_is_rejected(self) -> None:
        raw = json.loads(EXTRACT.read_text(encoding="utf-8"))
        changed = deepcopy(raw)
        metric = next(
            item
            for item in changed["metrics"]
            if item["metric_id"] == "QC_DC_WINTER_PEAK_2034_35"
        )
        metric["unit"] = "TWh"
        with self.assertRaisesRegex(ValidationError, "quantity/unit contract"):
            self._run_raw(changed)

    def test_source_hash_drift_is_rejected(self) -> None:
        raw = json.loads(EXTRACT.read_text(encoding="utf-8"))
        changed = deepcopy(raw)
        changed["source_files"][0]["content_hash"] = "sha256:" + "0" * 64
        with self.assertRaisesRegex(ValidationError, "archive hash does not match"):
            self._run_raw(changed)


if __name__ == "__main__":
    unittest.main()
