from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from aiio.panel_preflight import (
    build_panel_acquisition_preflight,
    validate_panel_acquisition_contract,
)
from aiio.schemas import ValidationError


class PanelAcquisitionPreflightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = Path(__file__).resolve().parents[2]
        cls.attribution_path = (
            cls.root / "data/model/ai_attribution_panel_contract_v0.1.json"
        )
        cls.acquisition_path = (
            cls.root / "data/model/ai_attribution_panel_acquisition_contract_v0.1.json"
        )
        cls.registry_path = cls.root / "data/registry/sources.json"
        cls.attribution = json.loads(cls.attribution_path.read_text(encoding="utf-8"))
        cls.acquisition = json.loads(cls.acquisition_path.read_text(encoding="utf-8"))
        registry = json.loads(cls.registry_path.read_text(encoding="utf-8"))
        cls.registry_ids = {item["source_id"] for item in registry["sources"]}

    def test_committed_preflight_is_reproducible_and_fail_closed(self) -> None:
        committed = json.loads(
            (
                self.root
                / "data/model-runs/ai_attribution_panel_preflight_v0.1.json"
            ).read_text(encoding="utf-8")
        )
        rebuilt = build_panel_acquisition_preflight(
            self.root,
            self.attribution_path,
            self.acquisition_path,
            self.registry_path,
        )
        self.assertEqual(rebuilt, committed)
        self.assertEqual(rebuilt["candidate_scope"]["region_count"], 5)
        self.assertEqual(
            rebuilt["field_gap_summary"]["required_field_instance_count"], 27
        )
        self.assertEqual(
            rebuilt["field_gap_summary"]["uncovered_required_field_instance_count"],
            0,
        )
        self.assertEqual(
            rebuilt["current_eligibility"]["authorizing_treated_region_count"],
            0,
        )
        self.assertEqual(
            rebuilt["current_eligibility"]["assembled_panel_row_count"], 0
        )
        self.assertEqual(len(rebuilt["evidence_receipts"]), 13)
        self.assertFalse(
            rebuilt["publication_boundary"]["effect_estimation_authorized"]
        )
        self.assertIsNone(
            rebuilt["publication_boundary"][
                "ai_attributable_cost_escalation_percent"
            ]
        )

    def test_rejects_unknown_sources_and_evidence_drift(self) -> None:
        acquisition = copy.deepcopy(self.acquisition)
        acquisition["evidence_receipts"][0]["source_ids"].append("UNKNOWN_SOURCE")
        with self.assertRaisesRegex(ValidationError, "unknown sources"):
            validate_panel_acquisition_contract(
                acquisition,
                self.attribution,
                registry_ids=self.registry_ids,
                root=self.root,
            )

        acquisition = copy.deepcopy(self.acquisition)
        acquisition["evidence_receipts"][0]["assertions"][0]["equals"] = 999
        with self.assertRaisesRegex(ValidationError, "evidence assertion failed"):
            validate_panel_acquisition_contract(
                acquisition,
                self.attribution,
                registry_ids=self.registry_ids,
                root=self.root,
            )

    def test_rejects_premature_authorization_and_incomplete_field_queue(self) -> None:
        acquisition = copy.deepcopy(self.acquisition)
        acquisition["evidence_receipts"][0]["authorizing_status"] = "authorizing"
        with self.assertRaisesRegex(ValidationError, "cannot authorize"):
            validate_panel_acquisition_contract(
                acquisition,
                self.attribution,
                registry_ids=self.registry_ids,
                root=self.root,
            )

        acquisition = copy.deepcopy(self.acquisition)
        acquisition["acquisition_tasks"][0]["required_fields"].pop()
        with self.assertRaisesRegex(ValidationError, "does not cover the locked fields"):
            validate_panel_acquisition_contract(
                acquisition,
                self.attribution,
                registry_ids=self.registry_ids,
                root=self.root,
            )

    def test_rejects_candidate_scope_below_identification_minimums(self) -> None:
        acquisition = copy.deepcopy(self.acquisition)
        acquisition["candidate_regions"] = acquisition["candidate_regions"][:-1]
        with self.assertRaisesRegex(ValidationError, "too few potential control"):
            validate_panel_acquisition_contract(
                acquisition,
                self.attribution,
                registry_ids=self.registry_ids,
                root=self.root,
            )


if __name__ == "__main__":
    unittest.main()
